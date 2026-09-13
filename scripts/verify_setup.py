from __future__ import annotations

import ast
import csv
import importlib
import json
import platform
import sys
import zipfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
NOTEBOOK = PROJECT_ROOT / "Piala_Dunia_26_Hybrid_AI_v4_VSCode.ipynb"
UCL_NOTEBOOK = PROJECT_ROOT / "notebooks" / "MatchIQ_UCL_Hybrid_AI_Training.ipynb"
UCL_V4_NOTEBOOK = PROJECT_ROOT / "notebooks" / "MatchIQ_UCL_v4_Audited.ipynb"

PACKAGE_IMPORTS = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "scikit-learn": "sklearn",
    "joblib": "joblib",
    "tqdm": "tqdm",
    "openpyxl": "openpyxl",
    "xgboost": "xgboost",
    "lightgbm": "lightgbm",
    "ipykernel": "ipykernel",
    "nbformat": "nbformat",
    "Jinja2": "jinja2",
    "Flask": "flask",
}

EXPECTED_ZIP_FILES = {
    "fifa_ranking_2022-10-06.csv",
    "fifa_ranking_2026-06-08.csv",
    "matches_1930_2022.csv",
    "schedule_2026.csv",
    "world_cup.csv",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


if sys.version_info[:2] != (3, 12):
    fail(f"Python harus versi 3.12; yang aktif sekarang {platform.python_version()}.")
if platform.architecture()[0] != "64bit":
    fail("Python harus arsitektur 64-bit.")

print(f"[OK] Python {platform.python_version()} ({platform.architecture()[0]})")

for distribution, module in PACKAGE_IMPORTS.items():
    importlib.import_module(module)
    try:
        installed_version = version(distribution)
    except PackageNotFoundError:
        installed_version = "terpasang"
    print(f"[OK] {distribution} {installed_version}")

required_files = [
    DATA_DIR / "world_cup_data.zip",
    DATA_DIR / "master_matches.csv",
    DATA_DIR / "matches.csv",
    NOTEBOOK,
    UCL_NOTEBOOK,
    UCL_V4_NOTEBOOK,
    PROJECT_ROOT / "app.py",
    PROJECT_ROOT / "matchiq" / "engine.py",
    PROJECT_ROOT / "matchiq" / "competitions.py",
    PROJECT_ROOT / "matchiq" / "web.py",
    PROJECT_ROOT / "scripts" / "ensure_runtime_model.py",
    PROJECT_ROOT / "models" / "dixon_coles_params.json",
    PROJECT_ROOT / "models" / "ucl_dixon_coles_params.json",
    PROJECT_ROOT / "models" / "matchiq_runtime.joblib",
    PROJECT_ROOT / "models" / "ucl_runtime.joblib",
    PROJECT_ROOT / "data" / "processed" / "ucl_matches.csv",
    PROJECT_ROOT / "data" / "processed" / "ucl_teams.csv",
    PROJECT_ROOT / "scripts" / "validate_ucl_dataset.py",
    PROJECT_ROOT / "scripts" / "train_ucl_runtime.py",
    PROJECT_ROOT / "scripts" / "build_ucl_notebook.py",
    PROJECT_ROOT / "templates" / "index.html",
    PROJECT_ROOT / "static" / "css" / "app.css",
    PROJECT_ROOT / "static" / "js" / "app.js",
    PROJECT_ROOT / "static" / "img" / "logo.svg",
]
for path in required_files:
    if not path.is_file():
        fail(f"File wajib tidak ditemukan: {path}")
    print(f"[OK] {path.relative_to(PROJECT_ROOT)}")

with zipfile.ZipFile(DATA_DIR / "world_cup_data.zip") as archive:
    archive.testzip()
    names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
missing_in_zip = EXPECTED_ZIP_FILES - names
if missing_in_zip:
    fail(f"Isi ZIP tidak lengkap: {sorted(missing_in_zip)}")
print("[OK] world_cup_data.zip valid dan berisi 5 dataset yang diharapkan")

ucl_matches_path = DATA_DIR / "processed" / "ucl_matches.csv"
with ucl_matches_path.open(encoding="utf-8", newline="") as handle:
    ucl_matches = list(csv.DictReader(handle))
ucl_match_ids = [row["match_id"] for row in ucl_matches]
if len(ucl_matches) != 1997 or len(ucl_match_ids) != len(set(ucl_match_ids)):
    fail("Dataset UCL tidak valid: jumlah pertandingan atau match_id bermasalah.")

ucl_teams_path = DATA_DIR / "processed" / "ucl_teams.csv"
with ucl_teams_path.open(encoding="utf-8", newline="") as handle:
    ucl_teams = list(csv.DictReader(handle))
if len(ucl_teams) != 161:
    fail(f"Registry klub UCL seharusnya 161 baris, ditemukan {len(ucl_teams)}.")
print("[OK] Dataset UCL valid (1.997 pertandingan utama, 161 klub)")

notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
if "/content" in source or "google.colab" in source:
    fail("Notebook masih mengandung path atau import khusus Google Colab.")
kernel = notebook.get("metadata", {}).get("kernelspec", {})
if kernel.get("language") != "python" or kernel.get("name") not in {
    "python3",
    "piala-dunia-26-hybrid-ai-v4",
}:
    fail("Metadata kernel notebook bukan kernel Python yang didukung.")
print(f"[OK] Notebook lokal valid ({len(notebook['cells'])} cell)")

ucl_notebook = json.loads(UCL_NOTEBOOK.read_text(encoding="utf-8"))
ucl_source = "\n".join(
    "".join(cell.get("source", [])) for cell in ucl_notebook["cells"]
)
if "/content" in ucl_source or "google.colab" in ucl_source:
    fail("Notebook UCL masih mengandung path atau import khusus Google Colab.")
ucl_kernel = ucl_notebook.get("metadata", {}).get("kernelspec", {})
ucl_metadata = ucl_notebook.get("metadata", {}).get("matchiq", {})
if ucl_kernel.get("language") != "python" or ucl_kernel.get("name") not in {
    "python3",
    "piala-dunia-26-hybrid-ai-v4",
}:
    fail("Metadata kernel notebook UCL bukan kernel Python yang didukung.")
if ucl_metadata.get("competition") != "ucl" or ucl_metadata.get("temporal_holdout") != "2025-26":
    fail("Metadata eksperimen notebook UCL tidak lengkap.")
ucl_code_cells = [
    cell for cell in ucl_notebook["cells"] if cell.get("cell_type") == "code"
]
for index, cell in enumerate(ucl_code_cells, start=1):
    ast.parse("".join(cell.get("source", [])), filename=f"UCL notebook cell {index}")
    if any(output.get("output_type") == "error" for output in cell.get("outputs", [])):
        fail(f"Notebook UCL menyimpan error pada code cell {index}.")
if len(ucl_notebook["cells"]) < 25 or len(ucl_code_cells) < 12:
    fail("Notebook UCL terlalu sedikit untuk audit training dan evaluasi penuh.")
executed_ucl_cells = sum(cell.get("execution_count") is not None for cell in ucl_code_cells)
print(
    f"[OK] Notebook UCL valid ({len(ucl_notebook['cells'])} cell, "
    f"{executed_ucl_cells}/{len(ucl_code_cells)} code cell memiliki output eksekusi)"
)

ucl_v4_notebook = json.loads(UCL_V4_NOTEBOOK.read_text(encoding="utf-8"))
ucl_v4_code_cells = [
    cell for cell in ucl_v4_notebook["cells"] if cell.get("cell_type") == "code"
]
ucl_v4_source = "\n".join(
    "".join(cell.get("source", [])) for cell in ucl_v4_code_cells
)
for index, cell in enumerate(ucl_v4_code_cells, start=1):
    ast.parse("".join(cell.get("source", [])), filename=f"UCL v4 notebook cell {index}")
    if any(output.get("output_type") == "error" for output in cell.get("outputs", [])):
        fail(f"Notebook UCL v4 menyimpan error pada code cell {index}.")
for marker in ("FORBIDDEN", "future-label invariance", "apply_calibration", "matchiq-ucl-v4-audited"):
    if marker not in ucl_v4_source:
        fail(f"Notebook UCL v4 tidak memiliki kontrol audit: {marker}")
print(f"[OK] Notebook UCL v4 audited valid ({len(ucl_v4_code_cells)} code cell)")

(PROJECT_ROOT / "outputs").mkdir(parents=True, exist_ok=True)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.competitions import COMPETITIONS  # noqa: E402
from matchiq.engine import MatchIQEngine  # noqa: E402
from matchiq.web import create_app  # noqa: E402

for competition_id, spec in COMPETITIONS.items():
    engine = MatchIQEngine(spec.model_path(PROJECT_ROOT))
    if engine.competition_id != competition_id:
        fail(f"Runtime {competition_id} berisi kompetisi {engine.competition_id}.")
    if competition_id == "ucl" and engine.pipeline_version != "ucl_v4_audited":
        fail(f"Runtime UCL bukan v4 audited: {engine.pipeline_version}")
    prediction = engine.predict(spec.default_home, spec.default_away, handicap=-1.5)
    outcome_total = sum(prediction["one_x_two"].values())
    if abs(outcome_total - 1.0) >= 1e-4:
        fail(f"Probabilitas 1X2 {competition_id} tidak valid: total={outcome_total}")
    print(
        f"[OK] Runtime {spec.name_id} valid "
        f"({engine.metadata['training_matches']} pertandingan latih, "
        f"data s.d. {engine.metadata['data_until']})"
    )

app = create_app({"TESTING": True})
with app.test_client() as client:
    if client.get("/").status_code != 200:
        fail("Halaman utama Flask gagal dibuka.")
    if client.get("/health").status_code != 200:
        fail("Health check Flask gagal.")
    competitions_response = client.get("/api/competitions")
    if competitions_response.status_code != 200:
        fail("Registry kompetisi API gagal dibuka.")
    api_response = client.post(
        "/api/predict",
        json={
            "competition": "world_cup",
            "home_team": "France",
            "away_team": "England",
            "handicap": -1.5,
        },
    )
    if api_response.status_code != 200:
        fail(f"API prediksi Piala Dunia gagal: {api_response.get_data(as_text=True)}")
    ucl_response = client.post(
        "/api/predict",
        json={
            "competition": "ucl",
            "home_team": "Real Madrid",
            "away_team": "FC Barcelona",
            "handicap": -1.5,
        },
    )
    if ucl_response.status_code != 200:
        fail(f"API prediksi UCL gagal: {ucl_response.get_data(as_text=True)}")
print("[OK] Flask UI dan API Piala Dunia/UCL berfungsi")

print("\nVERIFIKASI BERHASIL: MatchIQ WC + UCL dan seluruh notebook siap digunakan.")
