# MatchIQ — Hybrid AI Football Predictor

MatchIQ adalah aplikasi prediksi sepak bola lokal berbasis Flask untuk dua kompetisi:

- **Piala Dunia** — tim nasional;
- **UEFA Champions League (UCL)** — klub.

Antarmuka tersedia dalam bahasa Indonesia dan Inggris. Piala Dunia memakai **Hybrid v3**, sedangkan UCL memakai **v4 audited** dengan fitur yang seluruhnya tersedia sebelum kick-off, model selection walk-forward, dan kalibrasi temporal. Dataset dan runtime kedua kompetisi dipisahkan agar pola pertandingan klub tidak tercampur dengan tim nasional.

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

- **Dixon–Coles** menyediakan distribusi gol dan matriks skor;
- **UCL v4 audited** memakai nested walk-forward model selection, model XGBoost/logistik, draw policy, dan kalibrasi temporal tanpa fitur skor saat pertandingan;
- **Piala Dunia Hybrid v3** memakai XGBoost terkalibrasi untuk membaca ELO, form, tren gol, clean sheet, BTTS, home/away split, dan fitur time-aware lainnya;
- tim dengan histori terbatas memakai fallback netral dan diberi label kedalaman data terbatas.

Notebook UCL v4 menyimpan evaluasi walk-forward empat outer season (628 pertandingan). Hasil yang terekam di notebook baru:

- argmax accuracy: **56,21%**;
- multiclass log loss: **0,9399**, dibanding Dixon–Coles **1,0024** pada split yang sama;
- confidence ECE: **2,73%**;
- draw-aware accuracy: **52,71%** dengan draw recall **22,12%**.

Angka lama yang memakai skor babak pertama tidak dianggap benchmark pra-pertandingan yang valid. Runtime produksi memakai final state seluruh pertandingan selesai sampai 2025-26; model dasarnya dibekukan sebelum musim kalibrasi terakhir.

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

Audit walk-forward lengkap dapat dihitung ulang dengan menjalankan seluruh cell pada `notebooks/MatchIQ_UCL_v4_Audited.ipynb`. Script `evaluate_ucl_model.py` dipertahankan hanya untuk reproduksi baseline Hybrid v3 lama.

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

Proyek menyediakan tiga notebook terpisah:

| Notebook | Isi |
|---|---|
| `Piala_Dunia_26_Hybrid_AI_v4_VSCode.ipynb` | Eksperimen Piala Dunia asli, 199 cell |
| `notebooks/MatchIQ_UCL_Hybrid_AI_Training.ipynb` | Notebook UCL Hybrid v3 sebelumnya |
| `notebooks/MatchIQ_UCL_v4_Audited.ipynb` | Audit leakage, fitur pra-pertandingan, nested walk-forward, kalibrasi temporal, dan bundle UCL v4 |

Notebook UCL sudah dijalankan penuh dan menyimpan tabel serta grafik hasil evaluasi. Untuk menjalankannya kembali:

1. Buka notebook yang diinginkan di VS Code.
2. Klik pilihan kernel di kanan atas.
3. Pilih **Python 3.12 (MatchIQ Hybrid AI)**.
4. Klik **Run All**.

Notebook UCL v4 menjalankan outer walk-forward pada empat musim terakhir, memisahkan meta-training, tuning, dan kalibrasi, lalu memeriksa parity export/reload. Runtime Flask mengimplementasikan feature builder, model selection, kalibrator, state Elo, dan draw policy yang sama.

Saat dijalankan dari workspace MatchIQ atau folder `notebooks`, notebook v4 otomatis membaca `data/processed/`; `data.zip` hanya diperlukan sebagai fallback di luar repositori atau saat upload ke Colab. Artifact notebook lokal ditulis ke `outputs/ucl_v4_notebook/`.

Untuk menghasilkan ulang notebook UCL v3 lama dari source builder:

```powershell
& "$env:LOCALAPPDATA\piala-dunia-26-hybrid-ai-v4-venv\Scripts\python.exe" .\scripts\build_ucl_notebook.py
```

Untuk prediksi sehari-hari, gunakan Flask karena runtime sudah siap pakai.

## Struktur proyek

| Lokasi | Fungsi |
|---|---|
| `app.py` | Entry point server Flask |
| `matchiq/competitions.py` | Registry kompetisi, dataset, dan runtime |
| `matchiq/engine.py` | Router runtime multi-kompetisi dan kalkulasi pasar |
| `matchiq/ucl_v4.py` | Fitur pra-pertandingan, nested walk-forward, training, kalibrasi, dan inference UCL v4 |
| `matchiq/web.py` | Route halaman dan API multi-kompetisi |
| `models/dixon_coles_params.json` | Parameter Dixon–Coles Piala Dunia |
| `models/ucl_dixon_coles_params.json` | Parameter Dixon–Coles UCL |
| `config/`, `data/processed/`, `data/raw/`, `reports/` | Dataset, konfigurasi, validator, manifest, dan laporan UCL |
| `templates/index.html` | Struktur UI bilingual |
| `static/css/app.css` | Desain responsif dark minimal |
| `static/js/app.js` | Kompetisi, interaksi, heatmap, dan ID/EN |
| `scripts/build_runtime_model.py` | Training satu atau semua runtime |
| `scripts/train_ucl_runtime.py` | Training khusus UCL |
| `scripts/evaluate_ucl_model.py` | Reproduksi evaluasi baseline UCL Hybrid v3 lama |
| `scripts/build_ucl_notebook.py` | Membangun ulang notebook UCL v3 lama |
| `scripts/ensure_runtime_model.py` | Pemeriksaan kompatibilitas dan rebuild otomatis |
| `scripts/verify_setup.py` | Verifikasi package, data, model, Flask, dan API |
| `notebooks/MatchIQ_UCL_v4_Audited.ipynb` | Notebook audit dan evaluasi utama UCL v4 |
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
