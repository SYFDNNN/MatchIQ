from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.competitions import COMPETITIONS  # noqa: E402
from matchiq.engine import MatchIQEngine, build_runtime_artifact  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bangun runtime native MatchIQ untuk Piala Dunia dan/atau UCL."
    )
    parser.add_argument(
        "--competition",
        choices=["all", *COMPETITIONS],
        default="all",
        help="Runtime yang dibangun (default: all).",
    )
    return parser.parse_args()


def build_one(competition_id: str) -> dict:
    spec = COMPETITIONS[competition_id]
    destination = spec.model_path(PROJECT_ROOT)
    print(f"\nMembangun runtime {spec.name_id}...")
    metadata = build_runtime_artifact(
        PROJECT_ROOT,
        destination,
        competition_id=competition_id,
    )
    engine = MatchIQEngine(destination)
    prediction = engine.predict(spec.default_home, spec.default_away, handicap=-1.5)
    if abs(sum(prediction["one_x_two"].values()) - 1.0) >= 1e-4:
        raise RuntimeError(
            f"Validasi model {competition_id} gagal: probabilitas 1X2 tidak berjumlah 1."
        )
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"[OK] Runtime siap: {destination.relative_to(PROJECT_ROOT)}")
    return metadata


def main() -> int:
    args = parse_args()
    competition_ids = list(COMPETITIONS) if args.competition == "all" else [args.competition]
    for competition_id in competition_ids:
        build_one(competition_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
