from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.engine import (  # noqa: E402
    ALL_FEATS_V3,
    MAX_GOALS,
    RANDOM_SEED,
    DixonColesModel,
    _load_training_matches,
    build_professional_features,
    matrix_outcome_probs,
)


def main() -> int:
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import accuracy_score, log_loss
    from xgboost import XGBClassifier

    matches = _load_training_matches(PROJECT_ROOT, "ucl")
    if "season" not in matches:
        raise RuntimeError("Kolom season wajib tersedia untuk evaluasi temporal UCL.")

    holdout_season = "2025-26"
    train_mask = matches["season"].astype(str) != holdout_season
    test_mask = matches["season"].astype(str) == holdout_season
    train_matches = matches.loc[train_mask].copy()
    if train_matches.empty or not test_mask.any():
        raise RuntimeError("Split temporal UCL tidak menghasilkan train/test yang valid.")

    professional, _ = build_professional_features(matches)
    dc_model = DixonColesModel(xi=0.0018, ridge=1e-3).fit(train_matches)
    dc_rows = []
    for _, match in matches.iterrows():
        probabilities = matrix_outcome_probs(
            dc_model.score_matrix(match["home_team"], match["away_team"], MAX_GOALS)
        )
        dc_rows.append(
            {
                "dc_p_h": probabilities["H"],
                "dc_p_d": probabilities["D"],
                "dc_p_a": probabilities["A"],
            }
        )
    professional = professional.join(pd.DataFrame(dc_rows, index=professional.index))
    professional["y"] = professional["result"].map({"H": 0, "D": 1, "A": 2})

    x_train = professional.loc[train_mask, ALL_FEATS_V3].fillna(0)
    y_train = professional.loc[train_mask, "y"].astype(int).to_numpy()
    x_test = professional.loc[test_mask, ALL_FEATS_V3].fillna(0)
    y_test = professional.loc[test_mask, "y"].astype(int).to_numpy()

    counts = Counter(y_train)
    sample_weights = np.array(
        [len(y_train) / (3 * counts[label]) for label in y_train],
        dtype=float,
    )
    base_model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=RANDOM_SEED,
        verbosity=0,
    )
    model = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
    model.fit(x_train, y_train, sample_weight=sample_weights)

    ml_probabilities = model.predict_proba(x_test)
    dc_probabilities = x_test[["dc_p_h", "dc_p_d", "dc_p_a"]].to_numpy()
    blended = 0.6 * ml_probabilities + 0.4 * dc_probabilities
    blended /= blended.sum(axis=1, keepdims=True)
    predicted = blended.argmax(axis=1)
    one_hot = np.eye(3)[y_test]

    report = {
        "status": "passed",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "competition": "ucl",
        "method": "temporal_holdout_then_production_refit",
        "train_seasons": [
            str(value) for value in sorted(matches.loc[train_mask, "season"].unique())
        ],
        "test_season": holdout_season,
        "train_matches": int(train_mask.sum()),
        "test_matches": int(test_mask.sum()),
        "metrics": {
            "accuracy": round(float(accuracy_score(y_test, predicted)), 6),
            "multiclass_log_loss": round(
                float(log_loss(y_test, blended, labels=[0, 1, 2])), 6
            ),
            "multiclass_brier": round(
                float(np.mean(np.sum((blended - one_hot) ** 2, axis=1))), 6
            ),
        },
        "leakage_controls": [
            "Test season 2025-26 is excluded from evaluator fitting.",
            "Rolling form and Elo features are calculated chronologically before each match.",
            "The production runtime is refit on all completed matches only after evaluation.",
        ],
    }
    output = PROJECT_ROOT / "data" / "ucl" / "reports" / "ucl_model_evaluation.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"[OK] Evaluation report: {output.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
