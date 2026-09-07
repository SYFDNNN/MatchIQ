from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_URL = "https://github.com/openfootball/champions-league"
COMPETITION = "UEFA Champions League"
BASE_ELO = 1500.0
ELO_K = 20.0
HOME_ADVANTAGE = 65.0
SEASON_CARRYOVER = 0.85

MATCH_RE = re.compile(
    r"^\s*(?:(?P<time>\d{1,2}:\d{2})\s+)?"
    r"(?P<home>.+?)\s+\((?P<home_country>[A-Z]{3})\)\s+v\s+"
    r"(?P<away>.+?)\s+\((?P<away_country>[A-Z]{3})\)\s+"
    r"(?P<score>\d.*)$"
)
DATE_RE = re.compile(
    r"^\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})(?:\s+(?P<year>\d{4}))?\s*$"
)
DECLARED_MATCHES_RE = re.compile(r"^# Matches\s+(\d+)", re.MULTILINE)


ALIASES = {
    "AS Monaco": "AS Monaco",
    "AS Monaco FC": "AS Monaco",
    "Atalanta": "Atalanta",
    "Atalanta BC": "Atalanta",
    "Atlético Madrid": "Atlético Madrid",
    "Club Atlético de Madrid": "Atlético Madrid",
    "Bayer 04 Leverkusen": "Bayer Leverkusen",
    "Bayer Leverkusen": "Bayer Leverkusen",
    "Bayern München": "Bayern Munich",
    "FC Bayern München": "Bayern Munich",
    "Dinamo Zagreb": "Dinamo Zagreb",
    "GNK Dinamo Zagreb": "Dinamo Zagreb",
    "FC Red Bull Salzburg": "RB Salzburg",
    "RB Salzburg": "RB Salzburg",
    "SK Sturm Graz": "Sturm Graz",
    "Sturm Graz": "Sturm Graz",
    "Qarabağ Ağdam FK": "Qarabağ FK",
    "Qarabağ FK": "Qarabağ FK",
    "Royale Union Saint-Gilloise": "Union Saint-Gilloise",
    "Union Saint-Gilloise": "Union Saint-Gilloise",
    "Pafos FC": "Pafos FC",
    "Paphos FC": "Pafos FC",
    "SK Slavia Praha": "Slavia Praha",
    "Slavia Praha": "Slavia Praha",
    "Manchester City": "Manchester City",
    "Manchester City FC": "Manchester City",
    "Manchester United": "Manchester United",
    "Manchester United FC": "Manchester United",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "Tottenham Hotspur FC": "Tottenham Hotspur",
    "Real Madrid": "Real Madrid",
    "Real Madrid CF": "Real Madrid",
    "Real Sociedad": "Real Sociedad",
    "Real Sociedad de Fútbol": "Real Sociedad",
    "Olympique Marseille": "Olympique Marseille",
    "Olympique de Marseille": "Olympique Marseille",
    "Paris Saint-Germain": "Paris Saint-Germain",
    "Paris Saint-Germain FC": "Paris Saint-Germain",
    "Inter": "Inter Milan",
    "FC Internazionale Milano": "Inter Milan",
    "Juventus": "Juventus",
    "Juventus FC": "Juventus",
    "Lazio Roma": "Lazio",
    "SS Lazio": "Lazio",
    "Feyenoord": "Feyenoord",
    "Feyenoord Rotterdam": "Feyenoord",
    "PSV": "PSV Eindhoven",
    "PSV Eindhoven": "PSV Eindhoven",
    "SL Benfica": "Benfica",
    "Sport Lisboa e Benfica": "Benfica",
    "Sporting CP": "Sporting CP",
    "Sporting Clube de Portugal": "Sporting CP",
    "Sporting Braga": "Braga",
    "Sporting Clube de Braga": "Braga",
    "FC Steaua Bucureşti": "FCSB",
    "FCSB": "FCSB",
    "Crvena Zvezda": "Crvena Zvezda",
    "FK Crvena Zvezda": "Crvena Zvezda",
    "Slovan Bratislava": "Slovan Bratislava",
    "ŠK Slovan Bratislava": "Slovan Bratislava",
    "Galatasaray": "Galatasaray",
    "Galatasaray SK": "Galatasaray",
    "FK Shakhtar Donetsk": "Shakhtar Donetsk",
    "Shakhtar Donetsk": "Shakhtar Donetsk",
    "Olympiakos Piraeus": "Olympiacos",
    "PAE Olympiakos SFP": "Olympiacos",
}

ASSOCIATION_OVERRIDES = {
    "AS Monaco": "MCO",
    "Pafos FC": "CYP",
    "Bayern Munich": "GER",
    "Inter Milan": "ITA",
    "Olympiacos": "GRE",
}


def canonical_team(name: str) -> str:
    clean = " ".join(name.split())
    return ALIASES.get(clean, clean)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return f"ucl-{slug}"


def infer_year(season: str, month: int, explicit_year: str | None) -> int:
    if explicit_year:
        return int(explicit_year)
    start_year = int(season.split("-")[0])
    return start_year if month >= 7 else start_year + 1


def parse_stage(raw: str, is_qualifier: bool) -> dict[str, Any]:
    text = raw.strip()
    lowered = text.lower().replace("gruppe", "group")
    matchday_match = re.search(r"matchday\s+(\d+)", lowered)
    matchday = int(matchday_match.group(1)) if matchday_match else ""
    group_match = re.search(r"group\s+([a-h])$", lowered)
    group_name = group_match.group(1).upper() if group_match else ""

    if "final" in lowered and not any(
        key in lowered for key in ("quarter", "semi", "round of 16")
    ):
        stage = "final"
        order = 8
    elif "semi" in lowered:
        stage = "semifinal"
        order = 7
    elif "quarter" in lowered:
        stage = "quarterfinal"
        order = 6
    elif "round of 16" in lowered:
        stage = "round_of_16"
        order = 5
    elif "play" in lowered:
        stage = "playoff"
        order = 4
    elif "league" in lowered:
        stage = "league_phase"
        order = 3
    elif "group" in lowered:
        stage = "group_stage"
        order = 3
    elif is_qualifier and re.search(r"(?:^|\s)(?:1\.|round\s+1)", lowered):
        stage = "qualifying_round_1"
        order = 0
    elif is_qualifier and re.search(r"(?:^|\s)(?:2\.|round\s+2)", lowered):
        stage = "qualifying_round_2"
        order = 1
    elif is_qualifier and re.search(r"(?:^|\s)(?:3\.|round\s+3)", lowered):
        stage = "qualifying_round_3"
        order = 2
    else:
        stage = "other"
        order = -1

    return {
        "stage": stage,
        "stage_order": order,
        "matchday": matchday,
        "group": group_name,
    }


def parse_score(raw: str) -> dict[str, Any]:
    penalty = re.fullmatch(
        r"(\d+)-(\d+) pen\. (\d+)-(\d+) a\.e\.t\. "
        r"\((\d+)-(\d+)(?:, (\d+)-(\d+))?\)",
        raw,
    )
    if penalty:
        values = [int(value) if value is not None else None for value in penalty.groups()]
        pen_h, pen_a, final_h, final_a, rt_h, rt_a, ht_h, ht_a = values
        return {
            "home_goals": rt_h,
            "away_goals": rt_a,
            "home_goals_final": final_h,
            "away_goals_final": final_a,
            "home_goals_ht": ht_h,
            "away_goals_ht": ht_a,
            "home_penalty": pen_h,
            "away_penalty": pen_a,
            "decided_by": "Penalties",
        }

    extra_time = re.fullmatch(
        r"(\d+)-(\d+) a\.e\.t\. \((\d+)-(\d+)(?:, (\d+)-(\d+))?\)",
        raw,
    )
    if extra_time:
        values = [int(value) if value is not None else None for value in extra_time.groups()]
        final_h, final_a, rt_h, rt_a, ht_h, ht_a = values
        return {
            "home_goals": rt_h,
            "away_goals": rt_a,
            "home_goals_final": final_h,
            "away_goals_final": final_a,
            "home_goals_ht": ht_h,
            "away_goals_ht": ht_a,
            "home_penalty": None,
            "away_penalty": None,
            "decided_by": "Extra Time",
        }

    normal = re.fullmatch(r"(\d+)-(\d+)(?: \((\d+)-(\d+)\))?", raw)
    if not normal:
        raise ValueError(f"Format skor tidak dikenal: {raw}")
    home, away, ht_home, ht_away = [
        int(value) if value is not None else None for value in normal.groups()
    ]
    return {
        "home_goals": home,
        "away_goals": away,
        "home_goals_final": home,
        "away_goals_final": away,
        "home_goals_ht": ht_home,
        "away_goals_ht": ht_away,
        "home_penalty": None,
        "away_penalty": None,
        "decided_by": "Normal Time",
    }


def parse_file(path: Path, raw_root: Path, source_commit: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    season = path.parent.name
    is_qualifier = path.stem == "clq"
    text = path.read_text(encoding="utf-8-sig")
    declared_match = DECLARED_MATCHES_RE.search(text)
    declared = int(declared_match.group(1)) if declared_match else None
    current_stage = "Unknown"
    current_date: datetime | None = None
    current_time = ""
    rows: list[dict[str, Any]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("▪"):
            current_stage = stripped[1:].strip()
            continue

        date_match = DATE_RE.match(line)
        if date_match:
            month = datetime.strptime(date_match.group("month"), "%b").month
            year = infer_year(season, month, date_match.group("year"))
            current_date = datetime(year, month, int(date_match.group("day")))
            current_time = ""
            continue

        match = MATCH_RE.match(line)
        if not match:
            continue
        if current_date is None:
            raise ValueError(f"Tanggal belum ditemukan sebelum {path}:{line_number}")
        if match.group("time"):
            current_time = match.group("time")
        if not current_time:
            current_time = "00:00"

        home_raw = " ".join(match.group("home").split())
        away_raw = " ".join(match.group("away").split())
        home = canonical_team(home_raw)
        away = canonical_team(away_raw)
        score = parse_score(match.group("score").strip())
        stage_info = parse_stage(current_stage, is_qualifier)
        kickoff = datetime.combine(
            current_date.date(), datetime.strptime(current_time, "%H:%M").time()
        )
        neutral = int(
            stage_info["stage"] == "final"
            or (
                season == "2019-20"
                and stage_info["stage"] in {"quarterfinal", "semifinal"}
            )
        )
        row = {
            "competition": COMPETITION,
            "season": season,
            "date": current_date.strftime("%Y-%m-%d"),
            "kickoff_time": current_time,
            "kickoff_datetime": kickoff.strftime("%Y-%m-%dT%H:%M:00"),
            "stage_raw": current_stage,
            **stage_info,
            "is_qualifier": int(is_qualifier),
            "neutral": neutral,
            "home_team_id": slugify(home),
            "away_team_id": slugify(away),
            "home_team": home,
            "away_team": away,
            "home_team_raw": home_raw,
            "away_team_raw": away_raw,
            "home_country_code": match.group("home_country"),
            "away_country_code": match.group("away_country"),
            **score,
            "score_raw": match.group("score").strip(),
            "source_file": str(path.relative_to(raw_root)).replace("\\", "/"),
            "source_line": line_number,
            "source_commit": source_commit,
        }
        rows.append(row)

    if declared is not None and declared != len(rows):
        raise ValueError(
            f"Jumlah pertandingan {path} tidak cocok: declared={declared}, parsed={len(rows)}"
        )
    return rows, {
        "season": season,
        "file": str(path.relative_to(raw_root)).replace("\\", "/"),
        "is_qualifier": int(is_qualifier),
        "declared_matches": declared,
        "parsed_matches": len(rows),
    }


def assign_legs(rows: list[dict[str, Any]]) -> None:
    knockout = {
        "qualifying_round_1",
        "qualifying_round_2",
        "qualifying_round_3",
        "playoff",
        "round_of_16",
        "quarterfinal",
        "semifinal",
    }
    groups: dict[tuple[str, str, tuple[str, str]], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] not in knockout:
            row["leg"] = "single" if row["stage"] == "final" else "not_applicable"
            continue
        pair = tuple(sorted((row["home_team_id"], row["away_team_id"])))
        groups[(row["season"], row["stage"], pair)].append(row)

    for matches in groups.values():
        matches.sort(key=lambda item: (item["kickoff_datetime"], item["source_file"], item["source_line"]))
        if len(matches) == 1:
            matches[0]["leg"] = "single"
        else:
            for index, match in enumerate(matches, start=1):
                match["leg"] = index


def add_derived_fields(rows: list[dict[str, Any]]) -> None:
    sequence_by_season_kind: Counter[tuple[str, int]] = Counter()
    for row in rows:
        key = (row["season"], row["is_qualifier"])
        sequence_by_season_kind[key] += 1
        kind = "Q" if row["is_qualifier"] else "M"
        row["match_id"] = (
            f"UCL-{row['season']}-{kind}-{sequence_by_season_kind[key]:04d}"
        )
        home = int(row["home_goals"])
        away = int(row["away_goals"])
        row["year"] = int(row["date"][:4])
        row["result"] = "H" if home > away else "A" if home < away else "D"
        row["total_goals"] = home + away
        row["goal_diff"] = home - away
        row["btts"] = int(home > 0 and away > 0)


def add_time_aware_elo(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    ratings: defaultdict[str, float] = defaultdict(lambda: BASE_ELO)
    appearances: Counter[str] = Counter()
    goals_for: Counter[str] = Counter()
    goals_against: Counter[str] = Counter()
    first_season: dict[str, str] = {}
    last_season: dict[str, str] = {}
    last_date: dict[str, str] = {}

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["season"], row["kickoff_datetime"])].append(row)

    current_season: str | None = None
    for (season, _kickoff), matches in sorted(groups.items()):
        if season != current_season:
            if current_season is not None:
                for team in list(ratings):
                    ratings[team] = BASE_ELO + SEASON_CARRYOVER * (ratings[team] - BASE_ELO)
            current_season = season

        deltas: defaultdict[str, float] = defaultdict(float)
        for row in matches:
            home = row["home_team_id"]
            away = row["away_team_id"]
            home_pre = ratings[home]
            away_pre = ratings[away]
            advantage = 0.0 if row["neutral"] else HOME_ADVANTAGE
            expected_home = 1.0 / (1.0 + 10.0 ** ((away_pre - home_pre - advantage) / 400.0))
            actual_home = 1.0 if row["result"] == "H" else 0.0 if row["result"] == "A" else 0.5
            delta = ELO_K * (actual_home - expected_home)

            row["home_elo_pre"] = round(home_pre, 2)
            row["away_elo_pre"] = round(away_pre, 2)
            row["elo_diff_pre"] = round(home_pre + advantage - away_pre, 2)
            row["home_matches_before"] = appearances[home]
            row["away_matches_before"] = appearances[away]
            deltas[home] += delta
            deltas[away] -= delta

        for team, delta in deltas.items():
            ratings[team] += delta

        for row in matches:
            home = row["home_team_id"]
            away = row["away_team_id"]
            appearances[home] += 1
            appearances[away] += 1
            goals_for[home] += int(row["home_goals"])
            goals_against[home] += int(row["away_goals"])
            goals_for[away] += int(row["away_goals"])
            goals_against[away] += int(row["home_goals"])
            first_season.setdefault(home, row["season"])
            first_season.setdefault(away, row["season"])
            last_season[home] = row["season"]
            last_season[away] = row["season"]
            last_date[home] = row["date"]
            last_date[away] = row["date"]

    stats: dict[str, dict[str, Any]] = {}
    for team_id in sorted(ratings):
        stats[team_id] = {
            "latest_elo": round(ratings[team_id], 2),
            "matches": appearances[team_id],
            "goals_for": goals_for[team_id],
            "goals_against": goals_against[team_id],
            "first_season": first_season.get(team_id, ""),
            "last_season": last_season.get(team_id, ""),
            "last_match_date": last_date.get(team_id, ""),
        }
    return stats


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(root: Path) -> dict[str, Any]:
    raw_root = root / "data" / "raw" / "openfootball"
    processed = root / "data" / "processed"
    source_commit = (raw_root / "SOURCE_COMMIT.txt").read_text(encoding="utf-8").strip()
    source_files = sorted(raw_root.glob("*/cl.txt")) + sorted(raw_root.glob("*/clq.txt"))
    if not source_files:
        raise FileNotFoundError(f"Tidak ada cl.txt/clq.txt di {raw_root}")

    rows: list[dict[str, Any]] = []
    source_checks: list[dict[str, Any]] = []
    for source in source_files:
        parsed, check = parse_file(source, raw_root, source_commit)
        rows.extend(parsed)
        source_checks.append(check)

    rows.sort(key=lambda item: (
        item["kickoff_datetime"], item["is_qualifier"], item["source_file"], item["source_line"]
    ))
    assign_legs(rows)
    add_derived_fields(rows)
    team_stats = add_time_aware_elo(rows)

    team_variants: defaultdict[str, set[str]] = defaultdict(set)
    team_countries: defaultdict[str, Counter[str]] = defaultdict(Counter)
    team_names: dict[str, str] = {}
    for row in rows:
        for side in ("home", "away"):
            team_id = row[f"{side}_team_id"]
            name = row[f"{side}_team"]
            raw_name = row[f"{side}_team_raw"]
            country = row[f"{side}_country_code"]
            team_names[team_id] = name
            team_variants[team_id].add(raw_name)
            team_countries[team_id][country] += 1

    detailed_fields = [
        "match_id", "competition", "season", "date", "kickoff_time", "kickoff_datetime",
        "stage_raw", "stage", "stage_order", "matchday", "group", "leg",
        "is_qualifier", "neutral", "home_team_id", "away_team_id", "home_team", "away_team",
        "home_team_raw", "away_team_raw", "home_country_code", "away_country_code",
        "home_goals", "away_goals", "home_goals_final", "away_goals_final",
        "home_goals_ht", "away_goals_ht", "home_penalty", "away_penalty", "decided_by",
        "result", "total_goals", "goal_diff", "btts", "home_elo_pre", "away_elo_pre",
        "elo_diff_pre", "home_matches_before", "away_matches_before", "score_raw",
        "source_file", "source_line", "source_commit",
    ]
    main_rows = [row for row in rows if row["is_qualifier"] == 0]
    matchiq_fields = [
        "home_team", "away_team", "home_goals", "away_goals", "date", "year", "stage",
        "decided_by", "home_penalty", "away_penalty", "stage_order", "result",
        "total_goals", "goal_diff", "btts", "attendance",
    ]
    matchiq_rows = []
    for row in main_rows:
        matchiq_rows.append({**row, "attendance": ""})

    teams = []
    for team_id, name in team_names.items():
        country = ASSOCIATION_OVERRIDES.get(name)
        if not country:
            country = team_countries[team_id].most_common(1)[0][0]
        teams.append({
            "team_id": team_id,
            "team_name": name,
            "association_code": country,
            **team_stats[team_id],
            "source_variants": " | ".join(sorted(team_variants[team_id])),
        })
    teams.sort(key=lambda item: (-float(item["latest_elo"]), item["team_name"]))

    aliases = []
    for team in sorted(teams, key=lambda item: item["team_name"]):
        for variant in sorted(team_variants[team["team_id"]]):
            aliases.append({
                "raw_name": variant,
                "canonical_name": team["team_name"],
                "team_id": team["team_id"],
                "association_code": team["association_code"],
            })

    season_summary = []
    for season in sorted({row["season"] for row in rows}):
        for qualifier_flag, label in ((0, "main"), (1, "qualifier")):
            subset = [
                row for row in rows
                if row["season"] == season and row["is_qualifier"] == qualifier_flag
            ]
            if not subset:
                continue
            total_goals = sum(int(row["total_goals"]) for row in subset)
            season_summary.append({
                "season": season,
                "scope": label,
                "matches": len(subset),
                "teams": len({row["home_team_id"] for row in subset} | {row["away_team_id"] for row in subset}),
                "home_wins": sum(row["result"] == "H" for row in subset),
                "draws": sum(row["result"] == "D" for row in subset),
                "away_wins": sum(row["result"] == "A" for row in subset),
                "goals": total_goals,
                "goals_per_match": round(total_goals / len(subset), 3),
            })

    outputs = {
        "ucl_matches.csv": (main_rows, detailed_fields),
        "ucl_matches_all.csv": (rows, detailed_fields),
        "ucl_matches_matchiq.csv": (matchiq_rows, matchiq_fields),
        "ucl_teams.csv": (teams, list(teams[0].keys())),
        "ucl_team_aliases.csv": (aliases, list(aliases[0].keys())),
        "ucl_season_summary.csv": (season_summary, list(season_summary[0].keys())),
    }
    for filename, (data, fields) in outputs.items():
        write_csv(processed / filename, data, fields)

    output_files = {
        name: {
            "rows": len(data),
            "sha256": sha256(processed / name),
            "bytes": (processed / name).stat().st_size,
        }
        for name, (data, _fields) in outputs.items()
    }
    manifest = {
        "dataset_name": "MatchIQ UEFA Champions League Dataset",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {
            "name": "OpenFootball Champions League",
            "url": SOURCE_URL,
            "license": "CC0-1.0 / Public Domain",
            "commit": source_commit,
        },
        "coverage": {
            "first_season": min(row["season"] for row in rows),
            "last_season": max(row["season"] for row in rows),
            "main_matches": len(main_rows),
            "qualifier_matches": len(rows) - len(main_rows),
            "all_matches": len(rows),
            "canonical_teams": len(teams),
        },
        "score_policy": "home_goals/away_goals are 90-minute scores; extra-time and penalties are separate",
        "recommended_training_file": "data/processed/ucl_matches.csv",
        "matchiq_compatibility_file": "data/processed/ucl_matches_matchiq.csv",
        "output_files": output_files,
        "source_validation": source_checks,
        "elo": {
            "base": BASE_ELO,
            "k_factor": ELO_K,
            "home_advantage": HOME_ADVANTAGE,
            "season_carryover": SEASON_CARRYOVER,
            "time_aware": True,
        },
    }
    (root / "config" / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized UCL datasets for MatchIQ")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Root package MatchIQ_UCL_Dataset",
    )
    args = parser.parse_args()
    manifest = build(args.root.resolve())
    print(json.dumps(manifest["coverage"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
