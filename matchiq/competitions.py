from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict


DEFAULT_COMPETITION_ID = "world_cup"


@dataclass(frozen=True)
class CompetitionSpec:
    id: str
    name_id: str
    name_en: str
    short_name: str
    team_type: str
    model_filename: str
    training_data: str
    dc_params_filename: str
    default_home: str
    default_away: str

    def model_path(self, project_root: Path) -> Path:
        return project_root / "models" / self.model_filename

    def training_path(self, project_root: Path) -> Path:
        return project_root / self.training_data

    def public_payload(self) -> dict:
        payload = asdict(self)
        for private_key in ("model_filename", "training_data", "dc_params_filename"):
            payload.pop(private_key)
        payload["default_matchup"] = {
            "home": payload.pop("default_home"),
            "away": payload.pop("default_away"),
        }
        return payload


COMPETITIONS: Dict[str, CompetitionSpec] = {
    "world_cup": CompetitionSpec(
        id="world_cup",
        name_id="Piala Dunia",
        name_en="World Cup",
        short_name="WC",
        team_type="national",
        model_filename="matchiq_runtime.joblib",
        training_data="outputs/feature_dataset.csv",
        dc_params_filename="dixon_coles_params.json",
        default_home="France",
        default_away="England",
    ),
    "ucl": CompetitionSpec(
        id="ucl",
        name_id="Liga Champions UEFA",
        name_en="UEFA Champions League",
        short_name="UCL",
        team_type="club",
        model_filename="ucl_runtime.joblib",
        training_data="data/processed/ucl_matches.csv",
        dc_params_filename="ucl_dixon_coles_params.json",
        default_home="Real Madrid",
        default_away="FC Barcelona",
    ),
}


COMPETITION_ALIASES = {
    "wc": "world_cup",
    "worldcup": "world_cup",
    "world-cup": "world_cup",
    "world_cup": "world_cup",
    "piala-dunia": "world_cup",
    "piala_dunia": "world_cup",
    "ucl": "ucl",
    "champions-league": "ucl",
    "champions_league": "ucl",
    "uefa-champions-league": "ucl",
}


def resolve_competition_id(value: object | None) -> str:
    if value is None or str(value).strip() == "":
        return DEFAULT_COMPETITION_ID
    key = str(value).strip().casefold().replace(" ", "-")
    competition_id = COMPETITION_ALIASES.get(key, key)
    if competition_id not in COMPETITIONS:
        supported = ", ".join(COMPETITIONS)
        raise ValueError(f"Kompetisi tidak dikenali: {value}. Pilihan: {supported}.")
    return competition_id


def competition_payloads() -> list[dict]:
    return [spec.public_payload() for spec in COMPETITIONS.values()]
