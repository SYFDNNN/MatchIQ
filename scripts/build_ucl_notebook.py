from __future__ import annotations

import textwrap
from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "notebooks" / "MatchIQ_UCL_Hybrid_AI_Training.ipynb"


def clean(source: str) -> str:
    return textwrap.dedent(source).strip() + "\n"


def markdown(source: str):
    return nbf.v4.new_markdown_cell(clean(source))


def code(source: str):
    return nbf.v4.new_code_cell(clean(source))


def build_notebook() -> nbf.NotebookNode:
    cells = [
        markdown(
            """
            # MatchIQ UCL — Hybrid AI Training & Evaluation

            Notebook ini mendokumentasikan pipeline **UEFA Champions League** yang digunakan oleh
            aplikasi Flask MatchIQ. Fokusnya bukan sekadar menghasilkan prediksi, tetapi membuat
            proses data, feature engineering, training, evaluasi temporal, dan integrasi runtime
            dapat diaudit serta direproduksi.

            **Pipeline:** data UCL → fitur rolling/Elo time-aware → Dixon–Coles → XGBoost
            terkalibrasi → Hybrid v3 (60% ML + 40% Dixon–Coles).

            > Target 1X2 memakai skor setelah 90 menit. Notebook ini adalah eksperimen UCL terpisah;
            > dataset klub tidak dicampur dengan model Piala Dunia.
            """
        ),
        markdown(
            """
            ## 0. Environment dan konfigurasi

            Jalankan notebook memakai kernel **Python 3.12 (MatchIQ Hybrid AI)** dari folder proyek
            MatchIQ. Pencarian root di bawah dibuat robust agar tetap bekerja ketika current working
            directory berada di root proyek maupun folder `notebooks`.
            """
        ),
        code(
            """
            from __future__ import annotations

            import json
            import platform
            import sys
            import warnings
            from collections import Counter
            from datetime import datetime, timezone
            from pathlib import Path

            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import sklearn
            import xgboost
            from IPython.display import Markdown, display

            warnings.filterwarnings("ignore", category=FutureWarning)
            pd.set_option("display.max_columns", 80)
            pd.set_option("display.float_format", lambda value: f"{value:,.4f}")
            plt.style.use("seaborn-v0_8-whitegrid")


            def find_project_root() -> Path:
                start = Path.cwd().resolve()
                for candidate in (start, *start.parents):
                    if (candidate / "matchiq" / "engine.py").is_file() and (
                        candidate / "data" / "ucl"
                    ).is_dir():
                        return candidate
                raise FileNotFoundError(
                    "Root MatchIQ tidak ditemukan. Buka folder proyek MatchIQ di VS Code."
                )


            PROJECT_ROOT = find_project_root()
            if str(PROJECT_ROOT) not in sys.path:
                sys.path.insert(0, str(PROJECT_ROOT))

            from matchiq.competitions import COMPETITIONS
            from matchiq.engine import (
                ALL_FEATS_V3,
                FEAT_COLS_V3,
                MAX_GOALS,
                RANDOM_SEED,
                DixonColesModel,
                MatchIQEngine,
                ModelArtifactError,
                _load_training_matches,
                build_professional_features,
                build_runtime_artifact,
                matrix_outcome_probs,
            )

            UCL_SPEC = COMPETITIONS["ucl"]
            DATA_PATH = UCL_SPEC.training_path(PROJECT_ROOT)
            ALL_MATCHES_PATH = PROJECT_ROOT / "data/processed/ucl_matches_all.csv"
            TEAMS_PATH = PROJECT_ROOT / "data/processed/ucl_teams.csv"
            RUNTIME_PATH = UCL_SPEC.model_path(PROJECT_ROOT)
            REPORT_PATH = PROJECT_ROOT / "reports/ucl_model_evaluation.json"
            NOTEBOOK_REPORT_PATH = PROJECT_ROOT / "outputs/ucl_notebook_evaluation.json"

            print(f"Project root : {PROJECT_ROOT}")
            print(f"Python       : {platform.python_version()}")
            print(f"pandas       : {pd.__version__}")
            print(f"scikit-learn : {sklearn.__version__}")
            print(f"XGBoost      : {xgboost.__version__}")
            print(f"Dataset      : {DATA_PATH.relative_to(PROJECT_ROOT)}")
            """
        ),
        markdown(
            """
            ## 1. Memuat data dan memeriksa kontrak dataset

            Dataset utama berisi pertandingan fase kompetisi UCL. File `ucl_matches_all.csv`
            menambahkan kualifikasi yang tersedia, sedangkan training produksi memakai
            `ucl_matches.csv` agar cakupan antarmusim konsisten.
            """
        ),
        code(
            """
            raw_matches = pd.read_csv(DATA_PATH)
            all_matches = pd.read_csv(ALL_MATCHES_PATH)
            teams = pd.read_csv(TEAMS_PATH)
            matches = _load_training_matches(PROJECT_ROOT, "ucl")

            dataset_summary = pd.DataFrame(
                {
                    "Nilai": [
                        len(raw_matches),
                        len(all_matches),
                        teams["team_name"].nunique(),
                        raw_matches["season"].nunique(),
                        str(matches["date"].min().date()),
                        str(matches["date"].max().date()),
                    ]
                },
                index=[
                    "Pertandingan utama",
                    "Pertandingan termasuk kualifikasi",
                    "Klub kanonis",
                    "Musim",
                    "Tanggal awal",
                    "Tanggal akhir",
                ],
            )
            display(dataset_summary)
            display(raw_matches.head(5))
            """
        ),
        code(
            """
            required_columns = [
                "match_id",
                "date",
                "season",
                "home_team",
                "away_team",
                "home_goals",
                "away_goals",
                "result",
            ]
            missing_columns = sorted(set(required_columns) - set(raw_matches.columns))
            missing_required_values = int(
                raw_matches[[column for column in required_columns if column in raw_matches]].isna().sum().sum()
            )
            duplicate_match_ids = int(raw_matches["match_id"].duplicated().sum())
            invalid_scores = int(
                ((raw_matches["home_goals"] < 0) | (raw_matches["away_goals"] < 0)).sum()
            )

            checks = pd.DataFrame(
                [
                    ("Kolom wajib hilang", 0, len(missing_columns)),
                    ("Nilai wajib kosong", 0, missing_required_values),
                    ("Match ID duplikat", 0, duplicate_match_ids),
                    ("Skor negatif", 0, invalid_scores),
                    ("Pertandingan utama", 1997, len(raw_matches)),
                    ("Pertandingan seluruhnya", 2179, len(all_matches)),
                    ("Klub kanonis", 161, teams["team_name"].nunique()),
                    ("Jumlah musim", 15, raw_matches["season"].nunique()),
                ],
                columns=["Pemeriksaan", "Ekspektasi", "Aktual"],
            )
            checks["Status"] = np.where(checks["Ekspektasi"] == checks["Aktual"], "PASS", "FAIL")
            display(checks)

            assert missing_columns == [], missing_columns
            assert (checks["Status"] == "PASS").all(), "Validasi dataset UCL gagal."
            print("[OK] Kontrak dataset, ID pertandingan, skor, dan cakupan data valid.")
            """
        ),
        markdown(
            """
            ## 2. Exploratory Data Analysis (EDA)

            Grafik berikut memperlihatkan komposisi 1X2, distribusi total gol, dan jumlah laga per
            musim. EDA dilakukan sebelum modeling untuk mendeteksi ketidakseimbangan kelas dan
            perubahan volume kompetisi.
            """
        ),
        code(
            """
            result_names = {"H": "Home", "D": "Draw", "A": "Away"}
            result_distribution = (
                matches["result"].map(result_names).value_counts().reindex(["Home", "Draw", "Away"])
            )
            result_percent = (result_distribution / result_distribution.sum() * 100).round(2)
            goal_summary = (matches["home_goals"] + matches["away_goals"]).describe().to_frame("total_goals")

            display(pd.DataFrame({"matches": result_distribution, "percent": result_percent}))
            display(goal_summary)

            fig, axes = plt.subplots(1, 3, figsize=(17, 4.5))
            colors = ["#6D5EF5", "#A8A8A8", "#28D7B0"]
            result_percent.plot.bar(ax=axes[0], color=colors, rot=0)
            axes[0].set(title="Distribusi hasil 1X2", xlabel="Hasil", ylabel="Persentase (%)")

            total_goals = matches["home_goals"] + matches["away_goals"]
            bins = np.arange(0, int(total_goals.max()) + 2) - 0.5
            axes[1].hist(total_goals, bins=bins, color="#6D5EF5", edgecolor="white")
            axes[1].set(title="Distribusi total gol", xlabel="Total gol", ylabel="Pertandingan")

            season_counts = matches.groupby("season", sort=False).size()
            axes[2].plot(season_counts.index, season_counts.values, marker="o", color="#168CF4")
            axes[2].tick_params(axis="x", rotation=60)
            axes[2].set(title="Volume pertandingan per musim", xlabel="Musim", ylabel="Pertandingan")
            plt.tight_layout()
            plt.show()

            top_clubs = teams.nlargest(12, "matches")[["team_name", "association_code", "matches", "latest_elo"]]
            display(top_clubs.reset_index(drop=True))
            """
        ),
        markdown(
            """
            ## 3. Split temporal dan kontrol data leakage

            Evaluasi tidak memakai random split. Musim **2025-26** ditahan sebagai test set dan
            tidak digunakan untuk fitting model. Fitur form serta Elo dihitung berurutan: baris
            pertandingan hanya membaca pertandingan yang sudah terjadi sebelumnya.

            Untuk laga-laga berikutnya di musim test, fitur boleh memanfaatkan hasil laga test yang
            sudah selesai. Ini merupakan simulasi **rolling-origin/online prediction**, bukan leakage.
            """
        ),
        code(
            """
            HOLDOUT_SEASON = "2025-26"
            train_mask = matches["season"].astype(str) != HOLDOUT_SEASON
            test_mask = matches["season"].astype(str) == HOLDOUT_SEASON
            train_matches = matches.loc[train_mask].copy()
            test_matches = matches.loc[test_mask].copy()

            split_summary = pd.DataFrame(
                [
                    ("Train", ", ".join(sorted(train_matches["season"].unique())), len(train_matches),
                     train_matches["date"].min().date(), train_matches["date"].max().date()),
                    ("Test", HOLDOUT_SEASON, len(test_matches),
                     test_matches["date"].min().date(), test_matches["date"].max().date()),
                ],
                columns=["Split", "Musim", "Pertandingan", "Tanggal awal", "Tanggal akhir"],
            )
            display(split_summary)

            assert len(train_matches) == 1808
            assert len(test_matches) == 189
            assert train_matches["date"].max() < test_matches["date"].min()
            print("[OK] Train/test terpisah secara kronologis.")
            """
        ),
        markdown(
            """
            ## 4. Feature engineering time-aware

            Fitur meliputi rolling goals, kebobolan, form, BTTS, clean sheet, home/away split,
            EWMA, variasi gol, attack index, dan Elo. Fungsi yang dipanggil sama dengan engine Flask.
            """
        ),
        code(
            """
            professional, rolling_team_state = build_professional_features(matches)
            feature_audit = professional[
                ["date", "home_team", "away_team", "result", *FEAT_COLS_V3]
            ].copy()

            print(f"Fitur rolling/Elo : {len(FEAT_COLS_V3)}")
            print(f"Baris fitur       : {len(feature_audit)}")
            print(f"Nilai inf         : {int(np.isinf(feature_audit[FEAT_COLS_V3].to_numpy()).sum())}")
            print(f"Nilai kosong      : {int(feature_audit[FEAT_COLS_V3].isna().sum().sum())}")
            display(feature_audit.head(4))

            assert len(professional) == len(matches)
            assert not np.isinf(feature_audit[FEAT_COLS_V3].to_numpy()).any()
            """
        ),
        markdown(
            """
            ## 5. Dixon–Coles pada data train

            Dixon–Coles memodelkan jumlah gol kandang/tandang dan memberi koreksi pada skor rendah.
            Model di bawah hanya di-fit pada musim train. Probabilitas 1X2-nya kemudian menjadi tiga
            fitur tambahan untuk classifier Hybrid v3.
            """
        ),
        code(
            """
            dc_model = DixonColesModel(xi=0.0018, ridge=1e-3).fit(train_matches)

            dc_rows = []
            for _, match in matches.iterrows():
                matrix = dc_model.score_matrix(match["home_team"], match["away_team"], MAX_GOALS)
                probabilities = matrix_outcome_probs(matrix)
                dc_rows.append(
                    {
                        "dc_p_h": probabilities["H"],
                        "dc_p_d": probabilities["D"],
                        "dc_p_a": probabilities["A"],
                    }
                )

            modeling_frame = professional.join(pd.DataFrame(dc_rows, index=professional.index))
            modeling_frame["y"] = modeling_frame["result"].map({"H": 0, "D": 1, "A": 2})

            dc_diagnostics = pd.DataFrame(
                {
                    "Nilai": [
                        bool(dc_model.fit_result_.success),
                        float(dc_model.fit_result_.fun),
                        float(dc_model.rho_),
                        len(dc_model.teams_),
                    ]
                },
                index=["Optimizer success", "Negative log-likelihood", "Rho", "Tim terlatih"],
            )
            display(dc_diagnostics)
            assert np.allclose(
                modeling_frame[["dc_p_h", "dc_p_d", "dc_p_a"]].sum(axis=1), 1.0, atol=1e-6
            )
            """
        ),
        markdown(
            """
            ## 6. Training XGBoost terkalibrasi dan Hybrid v3

            Class weight dihitung dari data train. XGBoost dan calibrator tidak pernah menerima
            target musim test. Probabilitas akhir Hybrid v3 adalah 60% ML dan 40% Dixon–Coles.
            """
        ),
        code(
            """
            from sklearn.calibration import CalibratedClassifierCV
            from xgboost import XGBClassifier

            x_train = modeling_frame.loc[train_mask, ALL_FEATS_V3].fillna(0)
            y_train = modeling_frame.loc[train_mask, "y"].astype(int).to_numpy()
            x_test = modeling_frame.loc[test_mask, ALL_FEATS_V3].fillna(0)
            y_test = modeling_frame.loc[test_mask, "y"].astype(int).to_numpy()

            class_counts = Counter(y_train)
            sample_weights = np.array(
                [len(y_train) / (3 * class_counts[label]) for label in y_train], dtype=float
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
            calibrated_model = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
            calibrated_model.fit(x_train, y_train, sample_weight=sample_weights)

            ml_probabilities = calibrated_model.predict_proba(x_test)
            dc_probabilities = x_test[["dc_p_h", "dc_p_d", "dc_p_a"]].to_numpy()
            hybrid_probabilities = 0.6 * ml_probabilities + 0.4 * dc_probabilities
            hybrid_probabilities /= hybrid_probabilities.sum(axis=1, keepdims=True)

            print(f"Train matrix : {x_train.shape}")
            print(f"Test matrix  : {x_test.shape}")
            print(f"Feature total: {len(ALL_FEATS_V3)}")
            print("[OK] Training XGBoost terkalibrasi selesai.")
            """
        ),
        markdown(
            """
            ## 7. Evaluasi temporal: baseline vs Dixon–Coles vs ML vs Hybrid

            - **Accuracy** lebih besar lebih baik.
            - **Log loss** dan **Brier score** lebih kecil lebih baik karena menilai kualitas
              probabilitas, bukan hanya kelas pemenang.
            """
        ),
        code(
            """
            from sklearn.metrics import accuracy_score, log_loss

            labels = [0, 1, 2]
            one_hot = np.eye(3)[y_test]
            class_prior = np.bincount(y_train, minlength=3) / len(y_train)
            baseline_probabilities = np.tile(class_prior, (len(y_test), 1))


            def probability_metrics(name: str, probabilities: np.ndarray) -> dict:
                probabilities = np.asarray(probabilities, dtype=float)
                probabilities /= probabilities.sum(axis=1, keepdims=True)
                predictions = probabilities.argmax(axis=1)
                return {
                    "Model": name,
                    "Accuracy": accuracy_score(y_test, predictions),
                    "Log loss": log_loss(y_test, probabilities, labels=labels),
                    "Brier multiclass": np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)),
                }


            evaluation_table = pd.DataFrame(
                [
                    probability_metrics("Class-prior baseline", baseline_probabilities),
                    probability_metrics("Dixon-Coles", dc_probabilities),
                    probability_metrics("XGBoost calibrated", ml_probabilities),
                    probability_metrics("Hybrid v3 (60/40)", hybrid_probabilities),
                ]
            ).set_index("Model")
            display(evaluation_table.style.format("{:.4f}").highlight_min(
                subset=["Log loss", "Brier multiclass"], color="#d8f5e8"
            ).highlight_max(subset=["Accuracy"], color="#d8f5e8"))

            hybrid_metrics = evaluation_table.loc["Hybrid v3 (60/40)"]
            print(
                f"Hybrid holdout — accuracy={hybrid_metrics['Accuracy']:.4f}, "
                f"log_loss={hybrid_metrics['Log loss']:.4f}, "
                f"brier={hybrid_metrics['Brier multiclass']:.4f}"
            )
            """
        ),
        markdown(
            """
            ## 8. Confusion matrix dan calibration curve

            Confusion matrix menunjukkan kelas yang paling sering tertukar. Calibration curve
            membandingkan probabilitas prediksi dengan frekuensi aktual untuk Home/Draw/Away.
            """
        ),
        code(
            """
            from sklearn.calibration import calibration_curve
            from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix

            hybrid_predictions = hybrid_probabilities.argmax(axis=1)
            class_names = ["Home", "Draw", "Away"]

            fig, axes = plt.subplots(1, 2, figsize=(13, 5))
            matrix = confusion_matrix(y_test, hybrid_predictions, labels=labels)
            ConfusionMatrixDisplay(matrix, display_labels=class_names).plot(
                ax=axes[0], cmap="Purples", colorbar=False
            )
            axes[0].set_title("Hybrid v3 — confusion matrix")

            for class_index, class_name in enumerate(class_names):
                observed, predicted = calibration_curve(
                    (y_test == class_index).astype(int),
                    hybrid_probabilities[:, class_index],
                    n_bins=7,
                    strategy="quantile",
                )
                axes[1].plot(predicted, observed, marker="o", label=class_name)
            axes[1].plot([0, 1], [0, 1], "--", color="#777777", label="Ideal")
            axes[1].set(
                title="Hybrid v3 — calibration curve",
                xlabel="Probabilitas prediksi",
                ylabel="Frekuensi aktual",
                xlim=(0, 1),
                ylim=(0, 1),
            )
            axes[1].legend()
            plt.tight_layout()
            plt.show()
            """
        ),
        markdown(
            """
            ## 9. Feature importance dan error analysis

            Importance dirata-ratakan dari estimator XGBoost pada seluruh fold kalibrasi.
            Tabel error menampilkan kesalahan dengan confidence tertinggi sehingga kegagalan model
            dapat diperiksa secara konkret.
            """
        ),
        code(
            """
            fold_importances = []
            for calibrated in getattr(calibrated_model, "calibrated_classifiers_", []):
                estimator = getattr(calibrated, "estimator", None)
                if estimator is not None and hasattr(estimator, "feature_importances_"):
                    fold_importances.append(estimator.feature_importances_)

            if fold_importances:
                importance = pd.Series(
                    np.mean(fold_importances, axis=0), index=ALL_FEATS_V3, name="importance"
                ).sort_values(ascending=False)
                display(importance.head(15).to_frame())
                importance.head(15).sort_values().plot.barh(
                    figsize=(8, 6), color="#6D5EF5", title="Top 15 feature importance"
                )
                plt.xlabel("Mean XGBoost importance")
                plt.tight_layout()
                plt.show()
            else:
                print("Feature importance tidak tersedia pada versi estimator aktif.")

            label_to_result = {0: "H", 1: "D", 2: "A"}
            error_analysis = matches.loc[test_mask, [
                "date", "home_team", "away_team", "home_goals", "away_goals", "result"
            ]].reset_index(drop=True)
            error_analysis["prediction"] = [label_to_result[value] for value in hybrid_predictions]
            error_analysis["confidence"] = hybrid_probabilities.max(axis=1)
            error_analysis["p_home"] = hybrid_probabilities[:, 0]
            error_analysis["p_draw"] = hybrid_probabilities[:, 1]
            error_analysis["p_away"] = hybrid_probabilities[:, 2]
            error_analysis["correct"] = error_analysis["prediction"] == error_analysis["result"]

            high_confidence_errors = (
                error_analysis.loc[~error_analysis["correct"]]
                .sort_values("confidence", ascending=False)
                .head(10)
            )
            display(high_confidence_errors)
            """
        ),
        markdown(
            """
            ## 10. Menyimpan laporan evaluasi notebook

            Laporan JSON ringan menyimpan split, metrik, dan kontrol leakage. File ini bukan model;
            runtime produksi tetap dibangun oleh `scripts/train_ucl_runtime.py` atau setup Windows.
            """
        ),
        code(
            """
            notebook_report = {
                "status": "passed",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "competition": "ucl",
                "notebook": "notebooks/MatchIQ_UCL_Hybrid_AI_Training.ipynb",
                "split": {
                    "train_seasons": sorted(str(value) for value in train_matches["season"].unique()),
                    "test_season": HOLDOUT_SEASON,
                    "train_matches": int(len(train_matches)),
                    "test_matches": int(len(test_matches)),
                },
                "metrics": {
                    model_name: {
                        "accuracy": round(float(row["Accuracy"]), 6),
                        "multiclass_log_loss": round(float(row["Log loss"]), 6),
                        "multiclass_brier": round(float(row["Brier multiclass"]), 6),
                    }
                    for model_name, row in evaluation_table.iterrows()
                },
                "leakage_controls": [
                    "Holdout season 2025-26 is excluded from model fitting.",
                    "Rolling form and Elo features use only completed earlier matches.",
                    "Production refit is separate from holdout evaluation.",
                ],
            }
            NOTEBOOK_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            NOTEBOOK_REPORT_PATH.write_text(
                json.dumps(notebook_report, indent=2, ensure_ascii=False) + "\\n",
                encoding="utf-8",
            )
            print(f"[OK] Laporan tersimpan: {NOTEBOOK_REPORT_PATH.relative_to(PROJECT_ROOT)}")
            display(pd.DataFrame(notebook_report["metrics"]).T)
            """
        ),
        markdown(
            """
            ## 11. Uji integrasi runtime MatchIQ

            Setelah `setup_windows.bat` dijalankan, cell ini memuat `models/ucl_runtime.joblib`
            dan melakukan prediksi melalui class yang sama dengan API Flask. Jika runtime belum ada,
            cell memberi instruksi dan tetap membiarkan notebook evaluasi selesai.
            """
        ),
        code(
            """
            if RUNTIME_PATH.is_file():
                try:
                    engine = MatchIQEngine(RUNTIME_PATH)
                    sample = engine.predict("Real Madrid", "FC Barcelona", handicap=0)
                    sample_summary = pd.DataFrame(
                        {
                            "Nilai": [
                                sample["headline"]["score"],
                                sample["one_x_two"]["home"],
                                sample["one_x_two"]["draw"],
                                sample["one_x_two"]["away"],
                                sample["expected_goals"]["home"],
                                sample["expected_goals"]["away"],
                                sample["model"]["training_matches"],
                                sample["model"]["data_until"],
                            ]
                        },
                        index=[
                            "Skor paling mungkin",
                            "P(Home)",
                            "P(Draw)",
                            "P(Away)",
                            "xG home",
                            "xG away",
                            "Pertandingan training",
                            "Data sampai",
                        ],
                    )
                    display(sample_summary)
                    assert sample["competition"]["id"] == "ucl"
                    assert abs(sum(sample["one_x_two"].values()) - 1.0) < 1e-4
                    print("[OK] Runtime UCL dan kontrak prediksi Flask valid.")
                except ModelArtifactError as exc:
                    print(f"Runtime ada tetapi tidak kompatibel: {exc}")
                    print("Jalankan scripts/ensure_runtime_model.py lalu ulangi cell ini.")
            else:
                print("Runtime UCL belum dibuat.")
                print("Windows: jalankan setup_windows.bat")
                print("Manual : python scripts/train_ucl_runtime.py")
            """
        ),
        markdown(
            """
            ## 12. Refit produksi (opsional dan disengaja)

            Evaluasi holdout di atas harus diselesaikan **sebelum** refit produksi. Setelah metrik
            dicatat, runtime produksi boleh dilatih ulang memakai seluruh pertandingan selesai.

            Ubah `REBUILD_PRODUCTION_RUNTIME` menjadi `True` hanya jika memang ingin menimpa runtime
            UCL aktif pada komputer ini.
            """
        ),
        code(
            """
            REBUILD_PRODUCTION_RUNTIME = False

            if REBUILD_PRODUCTION_RUNTIME:
                production_metadata = build_runtime_artifact(
                    PROJECT_ROOT,
                    RUNTIME_PATH,
                    competition_id="ucl",
                )
                display(pd.Series(production_metadata, name="production_runtime").to_frame())
                print(f"[OK] Runtime produksi diperbarui: {RUNTIME_PATH.relative_to(PROJECT_ROOT)}")
            else:
                print("Refit produksi dilewati (aman).")
                print("Aktifkan hanya setelah evaluasi holdout diterima.")
            """
        ),
        markdown(
            """
            ## Kesimpulan dan batasan

            Notebook ini memisahkan evaluasi temporal dari refit produksi dan memakai fungsi yang
            sama dengan aplikasi MatchIQ. Dengan demikian, angka di notebook dapat ditelusuri sampai
            ke dataset dan implementasi runtime.

            Batasan penting:

            - dataset belum memiliki xG, line-up, cedera, odds, atau performa liga domestik;
            - Elo hanya dihitung dari pertandingan UCL yang tersedia;
            - kualifikasi lengkap baru tersedia untuk dua musim terakhir dan tidak dipakai pada
              training utama;
            - hasil adalah estimasi statistik, bukan kepastian dan bukan saran taruhan.

            Untuk membangun ulang runtime UCL tanpa notebook:

            ```powershell
            & "$env:LOCALAPPDATA\\piala-dunia-26-hybrid-ai-v4-venv\\Scripts\\python.exe" .\\scripts\\train_ucl_runtime.py
            ```
            """
        ),
    ]

    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata = {
        "kernelspec": {
            "display_name": "Python 3.12 (MatchIQ Hybrid AI)",
            "language": "python",
            "name": "piala-dunia-26-hybrid-ai-v4",
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.12",
        },
        "matchiq": {
            "competition": "ucl",
            "pipeline": "hybrid_v3",
            "temporal_holdout": "2025-26",
        },
    }
    return notebook


def main() -> int:
    notebook = build_notebook()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(notebook, OUTPUT_PATH)
    print(f"[OK] Notebook dibuat: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"     Cells: {len(notebook.cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
