from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
MANIFEST_PATH = ROOT / "config" / "dataset_manifest.json"


def read_csv(name: str) -> list[dict[str, str]]:
    with (PROCESSED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    # Git may check text files out with LF or CRLF depending on the runner.
    # The manifest was generated from CRLF CSV files, so hash a canonical
    # representation to keep validation identical on Windows and Linux.
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    digest = hashlib.sha256(content.replace(b"\n", b"\r\n"))
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    main_rows = read_csv("ucl_matches.csv")
    all_rows = read_csv("ucl_matches_all.csv")
    matchiq_rows = read_csv("ucl_matches_matchiq.csv")
    teams = read_csv("ucl_teams.csv")
    aliases = read_csv("ucl_team_aliases.csv")

    coverage = manifest["coverage"]
    require(len(main_rows) == coverage["main_matches"], "Jumlah main matches tidak cocok")
    require(len(all_rows) == coverage["all_matches"], "Jumlah all matches tidak cocok")
    require(len(matchiq_rows) == len(main_rows), "File kompatibilitas kehilangan baris")
    require(len(teams) == coverage["canonical_teams"], "Jumlah tim tidak cocok")

    match_ids = [row["match_id"] for row in all_rows]
    require(len(match_ids) == len(set(match_ids)), "match_id duplikat")
    required = (
        "match_id", "season", "date", "home_team", "away_team", "home_goals",
        "away_goals", "stage", "result", "home_elo_pre", "away_elo_pre",
    )
    for index, row in enumerate(all_rows, start=2):
        require(all(row.get(column, "") != "" for column in required), f"Nilai wajib kosong di baris {index}")
        require(row["home_team_id"] != row["away_team_id"], f"Tim sama di baris {index}")
        home = int(row["home_goals"])
        away = int(row["away_goals"])
        require(home >= 0 and away >= 0, f"Skor negatif di baris {index}")
        expected = "H" if home > away else "A" if home < away else "D"
        require(row["result"] == expected, f"Result tidak konsisten di baris {index}")
        require(int(row["total_goals"]) == home + away, f"Total gol salah di baris {index}")
        require(int(row["btts"]) == int(home > 0 and away > 0), f"BTTS salah di baris {index}")

    require(all(row["is_qualifier"] == "0" for row in main_rows), "File utama berisi qualifier")
    require(
        Counter(row["season"] for row in main_rows)["2025-26"] == 189,
        "Musim 2025-26 tidak lengkap",
    )
    require(
        min(row["date"] for row in all_rows) <= max(row["date"] for row in all_rows),
        "Rentang tanggal tidak valid",
    )
    require(len({row["team_id"] for row in teams}) == len(teams), "team_id duplikat")
    require(all(row["raw_name"] and row["canonical_name"] for row in aliases), "Alias kosong")

    for name, metadata in manifest["output_files"].items():
        path = PROCESSED / name
        require(path.is_file(), f"Output hilang: {name}")
        require(sha256(path) == metadata["sha256"], f"Checksum berubah: {name}")

    report = {
        "status": "passed",
        "checks": {
            "main_matches": len(main_rows),
            "all_matches": len(all_rows),
            "canonical_teams": len(teams),
            "seasons": len({row["season"] for row in main_rows}),
            "duplicate_match_ids": len(match_ids) - len(set(match_ids)),
            "missing_required_values": 0,
            "checksum_files_verified": len(manifest["output_files"]),
        },
    }
    report_path = ROOT / "reports" / "data_quality_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
