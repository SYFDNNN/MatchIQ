from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.competitions import COMPETITIONS  # noqa: E402
from matchiq.engine import MatchIQEngine, build_runtime_artifact  # noqa: E402


def main() -> int:
    spec = COMPETITIONS["ucl"]
    destination = spec.model_path(PROJECT_ROOT)
    print("Training MatchIQ UCL Hybrid v3...")
    metadata = build_runtime_artifact(
        PROJECT_ROOT,
        destination,
        competition_id="ucl",
    )
    engine = MatchIQEngine(destination)
    prediction = engine.predict(spec.default_home, spec.default_away, handicap=-1.5)
    probability_total = sum(prediction["one_x_two"].values())
    if abs(probability_total - 1.0) >= 1e-4:
        raise RuntimeError(f"Probabilitas UCL tidak valid: {probability_total}")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"[OK] Runtime UCL siap: {destination.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
