from __future__ import annotations

import platform
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.competitions import COMPETITIONS  # noqa: E402
from matchiq.engine import (  # noqa: E402
    MatchIQEngine,
    ModelArtifactError,
    build_runtime_artifact,
)


def installed_version(distribution: str, module: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return str(getattr(import_module(module), "__version__", "unknown"))


def validate_runtime(competition_id: str) -> MatchIQEngine:
    spec = COMPETITIONS[competition_id]
    engine = MatchIQEngine(spec.model_path(PROJECT_ROOT))
    if engine.competition_id != competition_id:
        raise ModelArtifactError(
            f"Runtime berisi {engine.competition_id}, seharusnya {competition_id}."
        )
    if competition_id == "ucl" and engine.pipeline_version != "ucl_v4_audited":
        raise ModelArtifactError(
            f"Runtime UCL masih {engine.pipeline_version}; versi ucl_v4_audited diperlukan."
        )
    expected = {
        "platform": platform.system(),
        "scikit_learn": installed_version("scikit-learn", "sklearn"),
        "xgboost": installed_version("xgboost", "xgboost"),
    }
    mismatches = [
        f"{key}: model={engine.metadata.get(key)!r}, aktif={value!r}"
        for key, value in expected.items()
        if engine.metadata.get(key) != value
    ]
    if mismatches:
        raise ModelArtifactError("Environment model berbeda (" + "; ".join(mismatches) + ").")
    prediction = engine.predict(spec.default_home, spec.default_away, handicap=-1.5)
    if abs(sum(prediction["one_x_two"].values()) - 1.0) >= 1e-4:
        raise ModelArtifactError("Probabilitas uji model tidak valid.")
    return engine


def main() -> int:
    for competition_id, spec in COMPETITIONS.items():
        try:
            engine = validate_runtime(competition_id)
            print(
                f"[OK] Runtime {spec.name_id} cocok dengan "
                f"{engine.metadata['platform']} / scikit-learn {engine.metadata['scikit_learn']} / "
                f"XGBoost {engine.metadata['xgboost']}."
            )
            continue
        except (ModelArtifactError, OSError, ValueError) as exc:
            print(f"Runtime {spec.name_id} perlu disiapkan ulang: {exc}")

        print(f"Membangun runtime native {spec.name_id}...")
        build_runtime_artifact(
            PROJECT_ROOT,
            spec.model_path(PROJECT_ROOT),
            competition_id=competition_id,
        )
        engine = validate_runtime(competition_id)
        print(
            f"[OK] Runtime {spec.name_id} berhasil dibuat "
            f"({engine.metadata['training_matches']} pertandingan latih)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
