from __future__ import annotations

import numpy as np

from matchiq.ucl_v4 import load_matches, make_features


def test_prematch_features_do_not_use_current_or_future_scores():
    matches = load_matches("data/processed/ucl_matches.csv").iloc[:140].copy()
    original, _ = make_features(matches)
    cutoff = 100
    modified = matches.copy()
    modified.loc[cutoff:, "home_goals"] = 7
    modified.loc[cutoff:, "away_goals"] = 0
    modified.loc[cutoff:, "result"] = "H"
    changed, _ = make_features(modified)
    feature_columns = [column for column in original if column not in matches]
    assert np.allclose(
        original.loc[:cutoff, feature_columns].to_numpy(dtype=float),
        changed.loc[:cutoff, feature_columns].to_numpy(dtype=float),
    )
