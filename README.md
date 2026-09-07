# MatchIQ — Hybrid AI Football Predictor

MatchIQ adalah aplikasi prediksi sepak bola lokal berbasis Flask untuk dua kompetisi:

- **Piala Dunia** — tim nasional;
- **UEFA Champions League (UCL)** — klub.

Antarmuka tersedia dalam bahasa Indonesia dan Inggris. Mesin **Hybrid v3** menggabungkan distribusi skor Dixon–Coles dengan classifier XGBoost terkalibrasi. Dataset dan runtime kedua kompetisi sengaja dipisahkan agar pola pertandingan klub tidak tercampur dengan tim nasional.

Saat setup pertama, MatchIQ membangun kedua runtime secara native memakai Python dan package aktif di Windows. File `.joblib` tidak disertakan di paket karena artifact XGBoost dari OS atau versi package lain dapat memunculkan `input stream corrupted`. Membuka aplikasi berikutnya tidak melatih ulang model selama runtime masih kompatibel.

## Setup tercepat di Windows

Persyaratan:

- Windows 10/11 64-bit;
- Python 3.12 64-bit;
- koneksi internet saat setup pertama untuk memasang package.

Langkah pertama kali:

1. Ekstrak ZIP ke folder biasa, misalnya `D:\Projects\MatchIQ`.
2. Buka folder `MatchIQ` di VS Code.
3. Buka terminal PowerShell VS Code.
4. Jalankan:

   ```powershell
   .\setup_windows.bat
   ```

5. Tunggu hingga runtime Piala Dunia dan UCL selesai dibuat serta muncul `SETUP BERHASIL`.
6. Jalankan aplikasi:

   ```powershell
   .\run_matchiq.bat
   ```

Browser akan membuka **http://127.0.0.1:5000**. Tekan `Ctrl+C` di terminal untuk menghentikan server.

Alternatif di VS Code: buka **Run and Debug**, pilih **MatchIQ: Flask UI**, lalu tekan `F5`.

Virtual environment dibuat di luar folder proyek:

```text
%LOCALAPPDATA%\piala-dunia-26-hybrid-ai-v4-venv
```

Lokasi tersebut menghindari masalah `WinError 5: Access is denied` yang sebelumnya terjadi saat membuat `.venv` di folder proyek.

## Menggunakan aplikasi

1. Pilih **Piala Dunia** atau **Liga Champions UEFA**.
2. Pilih tim kandang dan tandang. Daftar tim akan menyesuaikan kompetisi.
3. Atur handicap kandang bila diperlukan.
4. Klik **Analisis pertandingan**.
5. Gunakan tombol **ID / EN** untuk mengganti bahasa.

Hasil yang tersedia mencakup probabilitas 1X2, expected goals, skor paling mungkin, heatmap skor 0–0 sampai 7–7, BTTS, Over/Under 0.5–5.5, peluang lolos, handicap, odd/even, double chance, win to nil, exact total goals, dan skor resiliensi.

## Cakupan data dan model

| Kompetisi | Data produksi | Tim tersedia | Runtime |
|---|---:|---:|---|
| Piala Dunia | 964 laga, 1930–2022 | 48 tim utama | `models/matchiq_runtime.joblib` |
| UCL | 1.997 laga, 2011-12–2025-26 | 161 klub; 36 klub musim terkini ditandai utama | `models/ucl_runtime.joblib` |

Setiap runtime memakai alur berikut:

- **Dixon–Coles (40%)** untuk distribusi gol dan matriks skor;
- **XGBoost terkalibrasi (60%)** untuk membaca ELO, form, tren gol, clean sheet, BTTS, home/away split, dan fitur time-aware lainnya;
- tim dengan histori terbatas memakai fallback netral dan diberi label kedalaman data terbatas.

Evaluasi UCL memakai holdout temporal: musim 2011-12 sampai 2024-25 untuk training dan 2025-26 untuk pengujian. Hasil tersimpan pada `reports/ucl_model_evaluation.json`:

- accuracy: **52,91%**;
- multiclass log loss: **1,0041**;
- multiclass Brier: **0,6015**.

Setelah evaluasi, runtime produksi dilatih ulang memakai seluruh pertandingan selesai sampai 2025-26.

## Menjalankan tanpa file BAT

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\app.py --open-browser
```

Untuk memakai port lain:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\app.py --port 5050 --open-browser
```

## Melatih ulang model

Setup pertama menjalankan pemeriksa yang hanya membangun runtime yang hilang, rusak, atau tidak kompatibel.

Latih ulang kedua kompetisi:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\build_runtime_model.py --competition all
```

Latih ulang UCL saja:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\train_ucl_runtime.py
```

Pilihan lain untuk `--competition` adalah `world_cup` dan `ucl`. Sesudah training, jalankan:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\verify_setup.py
```

Evaluasi temporal UCL dapat diulang dengan:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\evaluate_ucl_model.py
```

## Memvalidasi dataset UCL

```powershell
py -3.12 .\scripts\validate_ucl_dataset.py
```

Output valid berisi `"status": "passed"` dengan 1.997 pertandingan utama, 2.179 pertandingan termasuk kualifikasi, 161 klub, dan nol ID pertandingan duplikat.

## API lokal

| Endpoint | Fungsi |
|---|---|
| `GET /api/competitions` | Daftar kompetisi dan matchup bawaan |
| `GET /api/teams?competition=ucl` | Daftar klub UCL |
| `GET /api/model?competition=world_cup` | Metadata runtime kompetisi |
| `POST /api/predict` | Prediksi pertandingan |
| `GET /health` | Status kedua runtime |

Contoh payload prediksi UCL:

```json
{
  "competition": "ucl",
  "home_team": "Real Madrid",
  "away_team": "FC Barcelona",
  "handicap": 0
}
```

Payload lama tanpa `competition` tetap kompatibel dan otomatis memakai `world_cup`.

## Notebook riset

Proyek menyediakan dua notebook terpisah:

| Notebook | Isi |
|---|---|
| `Piala_Dunia_26_Hybrid_AI_v4_VSCode.ipynb` | Eksperimen Piala Dunia asli, 199 cell |
| `notebooks/MatchIQ_UCL_Hybrid_AI_Training.ipynb` | Audit data, EDA, split temporal, training, kalibrasi, evaluasi, error analysis, dan uji runtime UCL |

Notebook UCL sudah dijalankan penuh dan menyimpan tabel serta grafik hasil evaluasi. Untuk menjalankannya kembali:

1. Buka notebook yang diinginkan di VS Code.
2. Klik pilihan kernel di kanan atas.
3. Pilih **Python 3.12 (MatchIQ Hybrid AI)**.
4. Klik **Run All**.

Notebook UCL menahan musim 2025-26 sebagai test set, membandingkan class-prior baseline,
Dixon–Coles, XGBoost terkalibrasi, dan Hybrid v3, lalu menguji artifact yang sama dengan Flask.
Cell refit produksi dibuat `False` secara default agar Run All tidak menimpa runtime tanpa disengaja.

Untuk menghasilkan ulang struktur notebook UCL dari source builder:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\build_ucl_notebook.py
```

Untuk prediksi sehari-hari, gunakan Flask karena runtime sudah siap pakai.

## Struktur proyek

| Lokasi | Fungsi |
|---|---|
| `app.py` | Entry point server Flask |
| `matchiq/competitions.py` | Registry kompetisi, dataset, dan runtime |
| `matchiq/engine.py` | Training, inference Hybrid v3, dan kalkulasi pasar |
| `matchiq/web.py` | Route halaman dan API multi-kompetisi |
| `models/dixon_coles_params.json` | Parameter Dixon–Coles Piala Dunia |
| `models/ucl_dixon_coles_params.json` | Parameter Dixon–Coles UCL |
| `config/`, `data/processed/`, `data/raw/`, `reports/` | Dataset, konfigurasi, validator, manifest, dan laporan UCL |
| `templates/index.html` | Struktur UI bilingual |
| `static/css/app.css` | Desain responsif dark minimal |
| `static/js/app.js` | Kompetisi, interaksi, heatmap, dan ID/EN |
| `scripts/build_runtime_model.py` | Training satu atau semua runtime |
| `scripts/train_ucl_runtime.py` | Training khusus UCL |
| `scripts/evaluate_ucl_model.py` | Evaluasi temporal UCL |
| `scripts/build_ucl_notebook.py` | Membangun ulang notebook audit UCL |
| `scripts/ensure_runtime_model.py` | Pemeriksaan kompatibilitas dan rebuild otomatis |
| `scripts/verify_setup.py` | Verifikasi package, data, model, Flask, dan API |
| `notebooks/MatchIQ_UCL_Hybrid_AI_Training.ipynb` | Notebook training dan evaluasi UCL transparan |
| `notebooks/original_colab/` | Salinan notebook Colab asli |

## Troubleshooting

### `No module named flask` atau `jinja2`

Jalankan ulang `setup_windows.bat`.

### Browser tidak otomatis terbuka

Buka `http://127.0.0.1:5000` secara manual dan pastikan server masih aktif di terminal.

### Port 5000 sudah dipakai

Gunakan contoh port 5050 pada bagian “Menjalankan tanpa file BAT”.

### Kernel notebook tidak muncul

Tekan `Ctrl+Shift+P` → **Developer: Reload Window**, lalu pilih kernel proyek kembali.

### `input stream corrupted` atau runtime tidak kompatibel

Jalankan:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\ensure_runtime_model.py
```

Script akan membangun ulang hanya runtime yang bermasalah secara native di Windows.

### Peringatan folder `~klearn` saat instalasi

Peringatan `Failed to remove contents in a temporary directory ... ~klearn` tidak menggagalkan setup. Folder tersebut adalah sisa sementara pip dan dapat dihapus manual setelah VS Code/Python ditutup.

## Catatan penggunaan

MatchIQ menyajikan estimasi statistik, bukan kepastian hasil dan bukan saran taruhan atau keuangan. Prediksi tim dengan histori terbatas memiliki ketidakpastian lebih tinggi.
