from __future__ import annotations

import json
import math
import platform
import sys
import unicodedata
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

from .competitions import COMPETITIONS, DEFAULT_COMPETITION_ID, resolve_competition_id


RANDOM_SEED = 42
MODEL_SCHEMA_VERSION = 2
DC_PARAMS_SCHEMA_VERSION = 1
MAX_GOALS = 7
OVER_UNDER_LINES = (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)

FEAT_COLS_V3 = [
    "h_avg_gs_5", "h_avg_gs_10", "h_avg_gc_5", "h_avg_gc_10",
    "a_avg_gs_5", "a_avg_gs_10", "a_avg_gc_5", "a_avg_gc_10",
    "h_ewma_gs", "h_ewma_gc", "a_ewma_gs", "a_ewma_gc",
    "h_form_5", "h_form_10", "a_form_5", "a_form_10",
    "h_btts_5", "a_btts_5", "h_cs_5", "a_cs_5",
    "h_home_gs_5", "h_home_gc_5", "a_away_gs_5", "a_away_gc_5",
    "h_gd_5", "a_gd_5", "h_attack_idx", "a_attack_idx",
    "elo_diff", "h_elo", "a_elo", "h_gs_var", "a_gs_var",
]
DC_FEAT_COLS = ["dc_p_h", "dc_p_d", "dc_p_a"]
ALL_FEATS_V3 = FEAT_COLS_V3 + DC_FEAT_COLS


# Display names follow current usage; model IDs retain the historical dataset names.
FEATURED_TEAMS: Tuple[Tuple[str, str], ...] = (
    ("Algeria", "Algeria"),
    ("Argentina", "Argentina"),
    ("Australia", "Australia"),
    ("Austria", "Austria"),
    ("Belgium", "Belgium"),
    ("Bosnia and Herzegovina", "Bosnia & Herzegovina"),
    ("Brazil", "Brazil"),
    ("Canada", "Canada"),
    ("Cabo Verde", "Cape Verde"),
    ("Colombia", "Colombia"),
    ("Zaire", "DR Congo"),
    ("Croatia", "Croatia"),
    ("Curacao", "Curaçao"),
    ("Czech Republic", "Czechia"),
    ("Ivory Coast", "Côte d’Ivoire"),
    ("Ecuador", "Ecuador"),
    ("Egypt", "Egypt"),
    ("England", "England"),
    ("France", "France"),
    ("Germany", "Germany"),
    ("Ghana", "Ghana"),
    ("Haiti", "Haiti"),
    ("Iran", "Iran"),
    ("Iraq", "Iraq"),
    ("Japan", "Japan"),
    ("Jordan", "Jordan"),
    ("Korea Republic", "South Korea"),
    ("Mexico", "Mexico"),
    ("Morocco", "Morocco"),
    ("Netherlands", "Netherlands"),
    ("New Zealand", "New Zealand"),
    ("Norway", "Norway"),
    ("Panama", "Panama"),
    ("Paraguay", "Paraguay"),
    ("Portugal", "Portugal"),
    ("Qatar", "Qatar"),
    ("Saudi Arabia", "Saudi Arabia"),
    ("Scotland", "Scotland"),
    ("Senegal", "Senegal"),
    ("South Africa", "South Africa"),
    ("Spain", "Spain"),
    ("Sweden", "Sweden"),
    ("Switzerland", "Switzerland"),
    ("Tunisia", "Tunisia"),
    ("Turkey", "Türkiye"),
    ("United States", "United States"),
    ("Uruguay", "Uruguay"),
    ("Uzbekistan", "Uzbekistan"),
)

DISPLAY_OVERRIDES = dict(FEATURED_TEAMS)

TEAM_CODES = {
    "Algeria": "DZ", "Angola": "AO", "Argentina": "AR", "Australia": "AU",
    "Austria": "AT", "Belgium": "BE", "Bolivia": "BO",
    "Bosnia and Herzegovina": "BA", "Brazil": "BR", "Bulgaria": "BG",
    "Cabo Verde": "CV", "Cameroon": "CM", "Canada": "CA", "Chile": "CL",
    "China": "CN", "Colombia": "CO", "Costa Rica": "CR", "Croatia": "HR",
    "Cuba": "CU", "Curacao": "CW", "Czech Republic": "CZ",
    "Czechoslovakia": "CZ", "Denmark": "DK", "Ecuador": "EC", "Egypt": "EG",
    "El Salvador": "SV", "England": "GB", "France": "FR", "Germany": "DE",
    "Germany Dr": "DE", "Ghana": "GH", "Greece": "GR", "Haiti": "HT",
    "Honduras": "HN", "Hungary": "HU", "Iceland": "IS", "Iran": "IR",
    "Iraq": "IQ", "Israel": "IL", "Italy": "IT", "Ivory Coast": "CI",
    "Jamaica": "JM", "Japan": "JP", "Jordan": "JO", "Korea Dpr": "KP",
    "Korea Republic": "KR", "Kuwait": "KW", "Mexico": "MX", "Morocco": "MA",
    "Netherlands": "NL", "New Zealand": "NZ", "Nigeria": "NG",
    "Northern Ireland": "GB", "Norway": "NO", "Panama": "PA", "Paraguay": "PY",
    "Peru": "PE", "Poland": "PL", "Portugal": "PT", "Qatar": "QA",
    "Republic of Ireland": "IE", "Romania": "RO", "Russia": "RU",
    "Saudi Arabia": "SA", "Scotland": "GB", "Senegal": "SN", "Serbia": "RS",
    "Serbia and Montenegro": "RS", "Slovakia": "SK", "Slovenia": "SI",
    "South Africa": "ZA", "Soviet Union": "RU", "Spain": "ES", "Sweden": "SE",
    "Switzerland": "CH", "Togo": "TG", "Trinidad and Tobago": "TT",
    "Tunisia": "TN", "Turkey": "TR", "Ukraine": "UA", "United Arab Emirates": "AE",
    "United States": "US", "Uruguay": "UY", "Uzbekistan": "UZ", "Wales": "GB",
    "West Germany": "DE", "Yugoslavia": "RS", "Zaire": "CD",
}

UEFA_ASSOCIATION_TO_ISO2 = {
    "ALB": "AL", "AND": "AD", "ARM": "AM", "AUT": "AT", "AZE": "AZ",
    "BEL": "BE", "BIH": "BA", "BLR": "BY", "BUL": "BG", "CRO": "HR",
    "CYP": "CY", "CZE": "CZ", "DEN": "DK", "ENG": "GB", "ESP": "ES",
    "EST": "EE", "FIN": "FI", "FRA": "FR", "FRO": "FO", "GEO": "GE",
    "GER": "DE", "GIB": "GI", "GRE": "GR", "HUN": "HU", "IRL": "IE",
    "ISL": "IS", "ISR": "IL", "ITA": "IT", "KAZ": "KZ", "KOS": "XK",
    "LTU": "LT", "LUX": "LU", "LVA": "LV", "MCO": "MC", "MDA": "MD",
    "MKD": "MK", "MLT": "MT", "MNE": "ME", "NED": "NL", "NIR": "GB",
    "NOR": "NO", "POL": "PL", "POR": "PT", "ROU": "RO", "RUS": "RU",
    "SCO": "GB", "SMR": "SM", "SRB": "RS", "SUI": "CH", "SVK": "SK",
    "SVN": "SI", "SWE": "SE", "TUR": "TR", "UKR": "UA", "WAL": "GB",
}

RAW_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "united states of america": "United States",
    "south korea": "Korea Republic",
    "republic of korea": "Korea Republic",
    "korea republic": "Korea Republic",
    "north korea": "Korea Dpr",
    "dpr korea": "Korea Dpr",
    "turkiye": "Turkey",
    "türkiye": "Turkey",
    "czechia": "Czech Republic",
    "cote d ivoire": "Ivory Coast",
    "côte d ivoire": "Ivory Coast",
    "cape verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",
    "curacao": "Curacao",
    "curaçao": "Curacao",
    "dr congo": "Zaire",
    "congo dr": "Zaire",
    "congo democratic republic": "Zaire",
    "bosnia herzegovina": "Bosnia and Herzegovina",
    "bosnia and herzegovina": "Bosnia and Herzegovina",
    "ir iran": "Iran",
}


class ModelArtifactError(RuntimeError):
    """Raised when the portable runtime model is missing or incompatible."""


def _normalization_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).strip().casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    for token in ("-", "_", ".", "’", "'"):
        value = value.replace(token, " ")
    return " ".join(value.split())


ALIASES = {_normalization_key(k): v for k, v in RAW_ALIASES.items()}


def _flag_from_code(code: str) -> str:
    if not code or len(code) != 2:
        return "⚽"
    return "".join(chr(127397 + ord(char)) for char in code.upper())


def poisson_pmf(k: np.ndarray, lam: float) -> np.ndarray:
    if lam < 0:
        raise ValueError("lambda must be non-negative")
    values = np.asarray(k, dtype=float)
    with np.errstate(divide="ignore"):
        log_lam = np.where(values == 0, 0.0, values * np.log(max(lam, 1e-12)))
    pmf = np.exp(log_lam - lam - gammaln(values + 1))
    if lam == 0:
        pmf = np.where(values == 0, 1.0, 0.0)
    return pmf


def dixon_coles_tau(
    x: np.ndarray,
    y: np.ndarray,
    lam: np.ndarray | float,
    mu: np.ndarray | float,
    rho: float,
) -> np.ndarray:
    tau = np.ones_like(x, dtype=float)
    tau = np.where((x == 0) & (y == 0), 1 - lam * mu * rho, tau)
    tau = np.where((x == 0) & (y == 1), 1 + lam * rho, tau)
    tau = np.where((x == 1) & (y == 0), 1 + mu * rho, tau)
    tau = np.where((x == 1) & (y == 1), 1 - rho, tau)
    return tau


def _poisson_logpmf(k: np.ndarray, lam: np.ndarray) -> np.ndarray:
    lam = np.clip(lam, 1e-10, None)
    return k * np.log(lam) - lam - gammaln(k + 1)


@dataclass
class DixonColesModel:
    xi: float = 0.0
    ridge: float = 1e-3
    rho_bounds: Tuple[float, float] = (-0.3, 0.3)
    teams_: List[str] = field(default_factory=list)
    team_idx_: Dict[str, int] = field(default_factory=dict)
    log_attack_: Optional[np.ndarray] = None
    log_defense_: Optional[np.ndarray] = None
    log_home_advantage_: float = 0.0
    rho_: float = 0.0
    fit_result_: Optional[object] = None

    def fit(
        self,
        matches: pd.DataFrame,
        seed_ratings: Optional[pd.DataFrame] = None,
        verbose: bool = True,
    ) -> "DixonColesModel":
        self.teams_ = sorted(set(matches["home_team"]) | set(matches["away_team"]))
        self.team_idx_ = {team: index for index, team in enumerate(self.teams_)}
        count = len(self.teams_)

        home_index = matches["home_team"].map(self.team_idx_).to_numpy()
        away_index = matches["away_team"].map(self.team_idx_).to_numpy()
        home_goals = matches["home_goals"].to_numpy(dtype=float)
        away_goals = matches["away_goals"].to_numpy(dtype=float)

        if self.xi > 0:
            days_ago = (matches["date"].max() - matches["date"]).dt.days.to_numpy()
            weights = np.exp(-self.xi * days_ago)
        else:
            weights = np.ones(len(matches))

        attack_seed = np.zeros(count)
        defense_seed = np.zeros(count)
        if seed_ratings is not None:
            for team, index in self.team_idx_.items():
                if team in seed_ratings.index:
                    attack = max(float(seed_ratings.loc[team, "attack_rating_raw"]), 0.2)
                    defense = max(float(seed_ratings.loc[team, "defense_rating_raw"]), 0.2)
                    attack_seed[index] = np.log(attack)
                    defense_seed[index] = np.log(max(1.0 / defense, 0.2))

        initial = np.concatenate([attack_seed, defense_seed, [np.log(1.15), 0.0]])

        def objective(params: np.ndarray) -> float:
            attack = params[:count]
            defense = params[count:2 * count]
            home_advantage, rho = params[2 * count], params[2 * count + 1]
            lam = np.exp(attack[home_index] + defense[away_index] + home_advantage)
            mu = np.exp(attack[away_index] + defense[home_index])
            tau = np.clip(
                dixon_coles_tau(home_goals, away_goals, lam, mu, rho),
                1e-10,
                None,
            )
            likelihood = (
                np.log(tau)
                + _poisson_logpmf(home_goals, lam)
                + _poisson_logpmf(away_goals, mu)
            ) * weights
            penalty = self.ridge * (np.sum(attack**2) + np.sum(defense**2))
            return float(-np.sum(likelihood) + penalty)

        bounds = [(None, None)] * (2 * count) + [(None, None), self.rho_bounds]
        result = minimize(
            objective,
            initial,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 1000, "maxfun": 250000, "ftol": 1e-10},
        )
        self.fit_result_ = result
        self.log_attack_ = result.x[:count]
        self.log_defense_ = result.x[count:2 * count]
        self.log_home_advantage_ = float(result.x[2 * count])
        self.rho_ = float(result.x[2 * count + 1])
        if verbose:
            status = "converged" if result.success else "stopped"
            print(f"Dixon-Coles {status}; negative log-likelihood={result.fun:.2f}")
        return self

    def _team_params(self, team: str) -> Tuple[float, float]:
        if team not in self.team_idx_:
            return 0.0, 0.0
        index = self.team_idx_[team]
        return float(self.log_attack_[index]), float(self.log_defense_[index])

    def predict_lambda(self, home_team: str, away_team: str) -> Tuple[float, float]:
        home_attack, home_defense = self._team_params(home_team)
        away_attack, away_defense = self._team_params(away_team)
        lam = math.exp(home_attack + away_defense + self.log_home_advantage_)
        mu = math.exp(away_attack + home_defense)
        return float(lam), float(mu)

    def score_matrix(self, home_team: str, away_team: str, max_goals: int) -> np.ndarray:
        lam, mu = self.predict_lambda(home_team, away_team)
        goals = np.arange(max_goals + 1)
        base = np.outer(poisson_pmf(goals, lam), poisson_pmf(goals, mu))
        home_grid, away_grid = np.meshgrid(goals, goals, indexing="ij")
        tau = dixon_coles_tau(home_grid, away_grid, lam, mu, self.rho_)
        adjusted = np.clip(base * tau, 0, None)
        return adjusted / adjusted.sum()

    def is_known(self, team: str) -> bool:
        return team in self.team_idx_


def matrix_outcome_probs(probability_matrix: np.ndarray) -> Dict[str, float]:
    size = probability_matrix.shape[0]
    home, away = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    return {
        "H": float(probability_matrix[home > away].sum()),
        "D": float(probability_matrix[home == away].sum()),
        "A": float(probability_matrix[home < away].sum()),
    }


def build_professional_features(matches: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, dict]]:
    """Recreate the notebook's time-aware Model v3 feature set."""
    frame = matches.sort_values("date").reset_index(drop=True).copy()
    frame["home_score"] = pd.to_numeric(frame["home_goals"], errors="coerce").fillna(0)
    frame["away_score"] = pd.to_numeric(frame["away_goals"], errors="coerce").fillna(0)
    frame["total_goals"] = frame["home_score"] + frame["away_score"]
    frame["btts"] = ((frame["home_score"] > 0) & (frame["away_score"] > 0)).astype(int)

    team_stats: Dict[str, dict] = {}

    def update(team: str, scored: int, conceded: int, result: str, is_home: bool) -> None:
        state = team_stats.setdefault(
            team,
            {
                "gs": [], "gc": [], "res": [], "btts": [], "cs": [],
                "home_gs": [], "home_gc": [], "away_gs": [], "away_gc": [],
                "elo": 1500.0,
            },
        )
        state["gs"].append(scored)
        state["gc"].append(conceded)
        state["res"].append(1 if result == "W" else (0.5 if result == "D" else 0))
        state["btts"].append(1 if scored > 0 and conceded > 0 else 0)
        state["cs"].append(1 if conceded == 0 else 0)
        if is_home:
            state["home_gs"].append(scored)
            state["home_gc"].append(conceded)
        else:
            state["away_gs"].append(scored)
            state["away_gc"].append(conceded)

    def rolling(values: List[float], window: int) -> float:
        return float(np.mean(values[-window:])) if values else 1.0

    def ewma(values: List[float], span: int = 5) -> float:
        if not values:
            return 1.0
        return float(pd.Series(values).ewm(span=span, adjust=False).mean().iloc[-1])

    rows: List[dict] = []
    for _, match in frame.iterrows():
        home_team, away_team = str(match["home_team"]), str(match["away_team"])
        home = team_stats.get(home_team, {})
        away = team_stats.get(away_team, {})
        home_elo = float(home.get("elo", 1500.0))
        away_elo = float(away.get("elo", 1500.0))

        hgs, hgc = home.get("gs", []), home.get("gc", [])
        ags, agc = away.get("gs", []), away.get("gc", [])
        hres, ares = home.get("res", []), away.get("res", [])
        hbtts, abtts = home.get("btts", []), away.get("btts", [])
        hcs, acs = home.get("cs", []), away.get("cs", [])
        hhgs, hhgc = home.get("home_gs", []), home.get("home_gc", [])
        aags, aagc = away.get("away_gs", []), away.get("away_gc", [])

        rows.append(
            {
                "h_avg_gs_5": rolling(hgs, 5), "h_avg_gs_10": rolling(hgs, 10),
                "h_avg_gc_5": rolling(hgc, 5), "h_avg_gc_10": rolling(hgc, 10),
                "a_avg_gs_5": rolling(ags, 5), "a_avg_gs_10": rolling(ags, 10),
                "a_avg_gc_5": rolling(agc, 5), "a_avg_gc_10": rolling(agc, 10),
                "h_ewma_gs": ewma(hgs), "h_ewma_gc": ewma(hgc),
                "a_ewma_gs": ewma(ags), "a_ewma_gc": ewma(agc),
                "h_form_5": rolling(hres, 5), "h_form_10": rolling(hres, 10),
                "a_form_5": rolling(ares, 5), "a_form_10": rolling(ares, 10),
                "h_btts_5": rolling(hbtts, 5), "a_btts_5": rolling(abtts, 5),
                "h_cs_5": rolling(hcs, 5), "a_cs_5": rolling(acs, 5),
                "h_home_gs_5": rolling(hhgs, 5), "h_home_gc_5": rolling(hhgc, 5),
                "a_away_gs_5": rolling(aags, 5), "a_away_gc_5": rolling(aagc, 5),
                "h_gd_5": rolling(hgs, 5) - rolling(hgc, 5),
                "a_gd_5": rolling(ags, 5) - rolling(agc, 5),
                "h_attack_idx": ewma(hgs) / max(ewma(agc), 0.5),
                "a_attack_idx": ewma(ags) / max(ewma(hgc), 0.5),
                "h_elo": home_elo, "a_elo": away_elo, "elo_diff": home_elo - away_elo,
                "h_gs_var": float(np.var(hgs[-10:])) if len(hgs) >= 3 else 1.0,
                "a_gs_var": float(np.var(ags[-10:])) if len(ags) >= 3 else 1.0,
            }
        )

        home_score = int(match["home_score"])
        away_score = int(match["away_score"])
        home_result = "W" if home_score > away_score else ("D" if home_score == away_score else "L")
        away_result = "W" if away_score > home_score else ("D" if home_score == away_score else "L")
        update(home_team, home_score, away_score, home_result, True)
        update(away_team, away_score, home_score, away_result, False)

        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        actual_home = 1.0 if home_result == "W" else (0.5 if home_result == "D" else 0.0)
        shift = 32 * (actual_home - expected_home)
        team_stats[home_team]["elo"] = float(home_elo + shift)
        team_stats[away_team]["elo"] = float(away_elo - shift)

    return frame.join(pd.DataFrame(rows, index=frame.index)), team_stats


def compute_lambda(
    home_team: str,
    away_team: str,
    team_stats: Dict[str, dict],
    global_avg_home: float = 1.4,
    global_avg_away: float = 1.1,
    home_advantage: float = 0.1,
) -> Tuple[float, float]:
    def ewma_safe(values: Iterable[float], default: float) -> float:
        values = list(values)
        if not values:
            return default
        return float(pd.Series(values).ewm(span=5, adjust=False).mean().iloc[-1])

    home = team_stats.get(home_team, {})
    away = team_stats.get(away_team, {})
    home_attack = ewma_safe(home.get("gs", []), global_avg_home)
    away_defense = ewma_safe(away.get("gc", []), global_avg_away)
    away_attack = ewma_safe(away.get("gs", []), global_avg_away)
    home_defense = ewma_safe(home.get("gc", []), global_avg_home)
    home_elo = float(home.get("elo", 1500.0))
    away_elo = float(away.get("elo", 1500.0))
    elo_factor = 1.0 + float(np.clip((home_elo - away_elo) / 800.0, -0.3, 0.3))
    league_average = (global_avg_home + global_avg_away) / 2
    lam_home = home_attack * away_defense / league_average * (1 + home_advantage) * elo_factor
    lam_away = away_attack * home_defense / league_average / (1 + home_advantage) / elo_factor
    return float(np.clip(lam_home, 0.2, 5.0)), float(np.clip(lam_away, 0.2, 5.0))


def _feature_row(
    home_team: str,
    away_team: str,
    team_stats: Dict[str, dict],
    dc_probs: Dict[str, float],
) -> pd.DataFrame:
    def rolling(values: List[float], window: int) -> float:
        return float(np.mean(values[-window:])) if values else 1.0

    def ewma(values: List[float]) -> float:
        return float(pd.Series(values).ewm(span=5, adjust=False).mean().iloc[-1]) if values else 1.0

    home = team_stats.get(home_team, {})
    away = team_stats.get(away_team, {})
    hgs, hgc = home.get("gs", []), home.get("gc", [])
    ags, agc = away.get("gs", []), away.get("gc", [])
    home_elo = float(home.get("elo", 1500.0))
    away_elo = float(away.get("elo", 1500.0))
    values = {
        "h_avg_gs_5": rolling(hgs, 5), "h_avg_gs_10": rolling(hgs, 10),
        "h_avg_gc_5": rolling(hgc, 5), "h_avg_gc_10": rolling(hgc, 10),
        "a_avg_gs_5": rolling(ags, 5), "a_avg_gs_10": rolling(ags, 10),
        "a_avg_gc_5": rolling(agc, 5), "a_avg_gc_10": rolling(agc, 10),
        "h_ewma_gs": ewma(hgs), "h_ewma_gc": ewma(hgc),
        "a_ewma_gs": ewma(ags), "a_ewma_gc": ewma(agc),
        "h_form_5": rolling(home.get("res", []), 5),
        "h_form_10": rolling(home.get("res", []), 10),
        "a_form_5": rolling(away.get("res", []), 5),
        "a_form_10": rolling(away.get("res", []), 10),
        "h_btts_5": rolling(home.get("btts", []), 5),
        "a_btts_5": rolling(away.get("btts", []), 5),
        "h_cs_5": rolling(home.get("cs", []), 5),
        "a_cs_5": rolling(away.get("cs", []), 5),
        "h_home_gs_5": rolling(home.get("home_gs", []), 5),
        "h_home_gc_5": rolling(home.get("home_gc", []), 5),
        "a_away_gs_5": rolling(away.get("away_gs", []), 5),
        "a_away_gc_5": rolling(away.get("away_gc", []), 5),
        "h_gd_5": rolling(hgs, 5) - rolling(hgc, 5),
        "a_gd_5": rolling(ags, 5) - rolling(agc, 5),
        "h_attack_idx": ewma(hgs) / max(ewma(agc), 0.5),
        "a_attack_idx": ewma(ags) / max(ewma(hgc), 0.5),
        "elo_diff": home_elo - away_elo,
        "h_elo": home_elo,
        "a_elo": away_elo,
        "h_gs_var": float(np.var(hgs[-10:])) if len(hgs) >= 3 else 1.0,
        "a_gs_var": float(np.var(ags[-10:])) if len(ags) >= 3 else 1.0,
        "dc_p_h": dc_probs["H"],
        "dc_p_d": dc_probs["D"],
        "dc_p_a": dc_probs["A"],
    }
    return pd.DataFrame([values], columns=ALL_FEATS_V3).fillna(0)


def _rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


class MatchIQEngine:
    def __init__(self, artifact_path: Path | str):
        self.artifact_path = Path(artifact_path).resolve()
        if not self.artifact_path.is_file():
            raise ModelArtifactError(
                f"Model runtime tidak ditemukan: {self.artifact_path}. "
                "Jalankan scripts/ensure_runtime_model.py."
            )
        try:
            artifact = joblib.load(self.artifact_path)
        except Exception as exc:
            raise ModelArtifactError(f"Model runtime gagal dibaca: {exc}") from exc
        if artifact.get("schema_version") != MODEL_SCHEMA_VERSION:
            raise ModelArtifactError("Versi model runtime tidak didukung; bangun ulang model.")
        for key in ("dc_model", "model_v3", "team_stats", "feature_columns", "metadata"):
            if key not in artifact:
                raise ModelArtifactError(f"Model runtime tidak lengkap: {key} tidak ada.")
        self.dc_model: DixonColesModel = artifact["dc_model"]
        self.model_v3 = artifact["model_v3"]
        self.team_stats: Dict[str, dict] = artifact["team_stats"]
        self.feature_columns: List[str] = artifact["feature_columns"]
        self.metadata: Dict[str, Any] = artifact["metadata"]
        competition = self.metadata.get("competition") or COMPETITIONS[
            DEFAULT_COMPETITION_ID
        ].public_payload()
        self.competition_id = resolve_competition_id(competition.get("id"))
        self.competition: Dict[str, Any] = {
            **COMPETITIONS[self.competition_id].public_payload(),
            **competition,
        }

        catalog = artifact.get("team_catalog")
        if not isinstance(catalog, dict) or not catalog:
            known_ids = sorted(set(self.dc_model.teams_) | set(DISPLAY_OVERRIDES))
            catalog = {
                team_id: {
                    "name": DISPLAY_OVERRIDES.get(team_id, team_id),
                    "code": TEAM_CODES.get(team_id, ""),
                    "featured": team_id in DISPLAY_OVERRIDES,
                }
                for team_id in known_ids
            }
        self.team_catalog: Dict[str, dict] = catalog
        self._featured_ids = [
            team_id
            for team_id, team in self.team_catalog.items()
            if bool(team.get("featured"))
        ]
        self._known_ids = sorted(set(self.dc_model.teams_) | set(self.team_catalog))
        self._lookup = {_normalization_key(team): team for team in self._known_ids}
        aliases = artifact.get("aliases")
        if isinstance(aliases, dict):
            self._lookup.update(
                {
                    _normalization_key(alias): canonical
                    for alias, canonical in aliases.items()
                    if canonical in self._known_ids
                }
            )
        if self.competition_id == DEFAULT_COMPETITION_ID:
            self._lookup.update(ALIASES)
        for team_id, team in self.team_catalog.items():
            self._lookup[_normalization_key(team.get("name", team_id))] = team_id

    def normalize_team(self, team: str) -> str:
        key = _normalization_key(team)
        if not key or key not in self._lookup:
            raise ValueError(f"Tim tidak dikenali: {team}")
        return self._lookup[key]

    def display_name(self, team_id: str) -> str:
        return str(self.team_catalog.get(team_id, {}).get("name", team_id))

    def team_payload(self, team_id: str) -> dict:
        team = self.team_catalog.get(team_id, {})
        code = str(team.get("code", ""))
        return {
            "id": team_id,
            "name": self.display_name(team_id),
            "code": code,
            "flag": str(team.get("flag") or _flag_from_code(code)),
            "featured": team_id in self._featured_ids,
            "historical_data": self.dc_model.is_known(team_id),
            "association_code": team.get("association_code"),
        }

    def teams(self) -> List[dict]:
        featured = [self.team_payload(team_id) for team_id in self._featured_ids]
        remaining = [
            self.team_payload(team_id)
            for team_id in self._known_ids
            if team_id not in self._featured_ids
        ]
        return featured + sorted(remaining, key=lambda team: team["name"])

    def predict(self, home_team: str, away_team: str, handicap: float = -1.5) -> dict:
        home_id = self.normalize_team(home_team)
        away_id = self.normalize_team(away_team)
        if home_id == away_id:
            raise ValueError("Pilih dua tim yang berbeda.")
        if not -5.0 <= float(handicap) <= 5.0:
            raise ValueError("Handicap harus berada di antara -5.0 dan 5.0.")

        matrix = self.dc_model.score_matrix(home_id, away_id, MAX_GOALS)
        goal_values = np.arange(MAX_GOALS + 1, dtype=float)
        lam_home = float((matrix * goal_values[:, None]).sum())
        lam_away = float((matrix * goal_values[None, :]).sum())
        dc_probs = matrix_outcome_probs(matrix)
        features = _feature_row(home_id, away_id, self.team_stats, dc_probs)
        features = features[self.feature_columns]
        ml_probability = self.model_v3.predict_proba(features)[0]
        blended = np.array(
            [
                0.4 * dc_probs["H"] + 0.6 * ml_probability[0],
                0.4 * dc_probs["D"] + 0.6 * ml_probability[1],
                0.4 * dc_probs["A"] + 0.6 * ml_probability[2],
            ],
            dtype=float,
        )
        blended /= blended.sum()

        home_grid, away_grid = np.meshgrid(
            np.arange(MAX_GOALS + 1), np.arange(MAX_GOALS + 1), indexing="ij"
        )
        total_grid = home_grid + away_grid
        btts_yes = float(matrix[(home_grid > 0) & (away_grid > 0)].sum())
        over_under = []
        for line in OVER_UNDER_LINES:
            over = float(matrix[total_grid > line].sum())
            over_under.append({"line": line, "over": _rounded(over), "under": _rounded(1 - over)})

        flat_indexes = np.argsort(matrix, axis=None)[::-1][:10]
        score_home, score_away = np.unravel_index(flat_indexes, matrix.shape)
        top_scores = []
        for home_goals, away_goals in zip(score_home, score_away):
            probability = float(matrix[home_goals, away_goals])
            confidence_tier = "high" if probability >= 0.12 else ("medium" if probability >= 0.06 else "low")
            top_scores.append(
                {
                    "score": f"{home_goals}-{away_goals}",
                    "probability": _rounded(probability),
                    "confidence": confidence_tier,
                }
            )

        handicap = float(handicap)
        adjusted_margin = home_grid + handicap - away_grid
        home_cover = float(matrix[adjusted_margin > 1e-9].sum())
        push = float(matrix[np.abs(adjusted_margin) <= 1e-9].sum())
        away_cover = max(0.0, 1.0 - home_cover - push)
        even = float(matrix[(total_grid % 2) == 0].sum())
        exact_goals = [
            {"goals": target, "probability": _rounded(matrix[total_grid == target].sum())}
            for target in range(7)
        ]
        exact_goals.append(
            {"goals": "7+", "probability": _rounded(matrix[total_grid >= 7].sum())}
        )
        exact_goals.sort(key=lambda item: item["probability"], reverse=True)

        home_resilience, away_resilience, resilience_status = self._resilience(home_id, away_id)
        entropy = -float(np.sum(blended * np.log(np.clip(blended, 1e-9, 1))))
        confidence = float(np.clip(1 - entropy / np.log(3), 0, 1))
        known_count = int(self.dc_model.is_known(home_id)) + int(self.dc_model.is_known(away_id))
        data_quality = "high" if known_count == 2 else ("medium" if known_count == 1 else "low")

        home_payload = self.team_payload(home_id)
        away_payload = self.team_payload(away_id)
        outcome_index = int(np.argmax(blended))
        outcome_key = ("home", "draw", "away")[outcome_index]

        return {
            "competition": self.competition,
            "match": {"home": home_payload, "away": away_payload, "handicap": handicap},
            "headline": {
                "score": top_scores[0]["score"],
                "outcome": outcome_key,
                "confidence": _rounded(confidence),
                "data_quality": data_quality,
            },
            "expected_goals": {"home": _rounded(lam_home, 3), "away": _rounded(lam_away, 3)},
            "one_x_two": {
                "home": _rounded(blended[0]),
                "draw": _rounded(blended[1]),
                "away": _rounded(blended[2]),
            },
            "btts": {"yes": _rounded(btts_yes), "no": _rounded(1 - btts_yes)},
            "over_under": over_under,
            "top_scores": top_scores,
            "score_matrix": [[_rounded(value) for value in row] for row in matrix.tolist()],
            "extended": {
                "double_chance": {
                    "1x": _rounded(blended[0] + blended[1]),
                    "x2": _rounded(blended[1] + blended[2]),
                    "12": _rounded(blended[0] + blended[2]),
                },
                "qualify": {
                    "home": _rounded(blended[0] + 0.5 * blended[1]),
                    "away": _rounded(blended[2] + 0.5 * blended[1]),
                },
                "handicap": {
                    "line": handicap,
                    "home_cover": _rounded(home_cover),
                    "push": _rounded(push),
                    "away_cover": _rounded(away_cover),
                },
                "odd_even": {"odd": _rounded(1 - even), "even": _rounded(even)},
                "win_to_nil": {
                    "home": _rounded(matrix[1:, 0].sum()),
                    "away": _rounded(matrix[0, 1:].sum()),
                },
                "clean_sheet": {
                    "home": _rounded(matrix[:, 0].sum()),
                    "away": _rounded(matrix[0, :].sum()),
                },
                "resilience": {
                    "home": _rounded(home_resilience, 3),
                    "away": _rounded(away_resilience, 3),
                    "status": resilience_status,
                },
                "exact_goals": exact_goals,
            },
            "model": {
                "name": "MatchIQ Hybrid v3",
                "blend": {"dixon_coles": 0.4, "xgboost": 0.6},
                "backend": self.metadata.get("model_backend", "xgboost"),
                "competition_id": self.competition_id,
                "training_matches": self.metadata.get("training_matches"),
                "data_until": self.metadata.get("data_until"),
            },
        }

    def _resilience(self, home_id: str, away_id: str) -> Tuple[float, float, str]:
        home = self.team_stats.get(home_id, {})
        away = self.team_stats.get(away_id, {})
        home_elo = float(home.get("elo", 1500.0))
        away_elo = float(away.get("elo", 1500.0))
        home_form = float(np.mean(home.get("res", [0.5])[-5:]))
        away_form = float(np.mean(away.get("res", [0.5])[-5:]))
        elo_diff = (home_elo - away_elo) / 400
        home_score = (1 / (1 + np.exp(-elo_diff))) * 0.7 + home_form * 0.3
        away_score = (1 / (1 + np.exp(elo_diff))) * 0.7 + away_form * 0.3
        if abs(home_score - away_score) <= 0.25:
            status = "balanced"
        else:
            status = "home" if home_score > away_score else "away"
        return float(home_score * 10), float(away_score * 10), status


def _load_training_matches(project_root: Path, competition_id: str) -> pd.DataFrame:
    competition_id = resolve_competition_id(competition_id)
    feature_path = COMPETITIONS[competition_id].training_path(project_root)
    if not feature_path.is_file():
        raise FileNotFoundError(
            f"Dataset training {competition_id} tidak ditemukan: {feature_path}"
        )
    frame = pd.read_csv(feature_path)
    required = ["home_team", "away_team", "home_goals", "away_goals", "date", "result"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Kolom dataset fitur tidak lengkap: {missing}")
    frame = frame[
        required
        + [column for column in ("year", "season", "stage") if column in frame.columns]
    ].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["home_goals"] = pd.to_numeric(frame["home_goals"], errors="coerce")
    frame["away_goals"] = pd.to_numeric(frame["away_goals"], errors="coerce")
    frame = frame.dropna(subset=["home_team", "away_team", "home_goals", "away_goals", "date", "result"])
    frame["home_team"] = frame["home_team"].astype(str)
    frame["away_team"] = frame["away_team"].astype(str)
    frame["home_goals"] = frame["home_goals"].astype(int)
    frame["away_goals"] = frame["away_goals"].astype(int)
    return frame.sort_values("date").reset_index(drop=True)


def _load_legacy_dixon_coles(project_root: Path) -> Optional[DixonColesModel]:
    legacy_path = project_root / "outputs" / "model.joblib"
    if not legacy_path.is_file():
        return None
    main_module = sys.modules.get("__main__")
    previous = getattr(main_module, "DixonColesModel", None)
    setattr(main_module, "DixonColesModel", DixonColesModel)
    try:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                bundle = joblib.load(legacy_path)
        except Exception as exc:
            warnings.warn(f"Model Dixon-Coles lama tidak dapat dibaca; akan dilatih ulang: {exc}")
            return None
        model = bundle.get("dixon_coles") if isinstance(bundle, dict) else None
        if isinstance(model, DixonColesModel):
            model.fit_result_ = None
            return model
        return None
    finally:
        if previous is None:
            delattr(main_module, "DixonColesModel")
        else:
            setattr(main_module, "DixonColesModel", previous)


def export_dixon_coles_parameters(model: DixonColesModel, output_path: Path | str) -> None:
    """Save only numeric Dixon-Coles state in cross-platform JSON format."""
    if model.log_attack_ is None or model.log_defense_ is None or not model.teams_:
        raise ValueError("Model Dixon-Coles belum memiliki parameter hasil training.")
    destination = Path(output_path).resolve()
    payload = {
        "schema_version": DC_PARAMS_SCHEMA_VERSION,
        "xi": float(model.xi),
        "ridge": float(model.ridge),
        "rho_bounds": [float(value) for value in model.rho_bounds],
        "teams": list(model.teams_),
        "log_attack": [float(value) for value in model.log_attack_],
        "log_defense": [float(value) for value in model.log_defense_],
        "log_home_advantage": float(model.log_home_advantage_),
        "rho": float(model.rho_),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _load_dixon_coles_parameters(
    project_root: Path,
    competition_id: str,
) -> Optional[DixonColesModel]:
    competition_id = resolve_competition_id(competition_id)
    params_path = (
        project_root
        / "models"
        / COMPETITIONS[competition_id].dc_params_filename
    )
    if not params_path.is_file():
        return None
    try:
        payload = json.loads(params_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != DC_PARAMS_SCHEMA_VERSION:
            raise ValueError("versi parameter tidak didukung")
        teams = [str(team) for team in payload["teams"]]
        log_attack = np.asarray(payload["log_attack"], dtype=float)
        log_defense = np.asarray(payload["log_defense"], dtype=float)
        if len(teams) != len(log_attack) or len(teams) != len(log_defense):
            raise ValueError("jumlah tim dan parameter tidak sama")
        model = DixonColesModel(
            xi=float(payload["xi"]),
            ridge=float(payload["ridge"]),
            rho_bounds=tuple(float(value) for value in payload["rho_bounds"]),
        )
        model.teams_ = teams
        model.team_idx_ = {team: index for index, team in enumerate(teams)}
        model.log_attack_ = log_attack
        model.log_defense_ = log_defense
        model.log_home_advantage_ = float(payload["log_home_advantage"])
        model.rho_ = float(payload["rho"])
        model.fit_result_ = None
        return model
    except Exception as exc:
        warnings.warn(f"Parameter Dixon-Coles portabel tidak valid; akan memakai fallback: {exc}")
        return None


def _build_team_catalog(
    project_root: Path,
    competition_id: str,
    dc_model: DixonColesModel,
) -> Tuple[Dict[str, dict], Dict[str, str]]:
    if competition_id == DEFAULT_COMPETITION_ID:
        featured_ids = {team_id for team_id, _ in FEATURED_TEAMS}
        known_ids = sorted(set(dc_model.teams_) | featured_ids)
        catalog = {
            team_id: {
                "name": DISPLAY_OVERRIDES.get(team_id, team_id),
                "code": TEAM_CODES.get(team_id, ""),
                "featured": team_id in featured_ids,
            }
            for team_id in known_ids
        }
        aliases = dict(RAW_ALIASES)
        aliases.update({display_name: team_id for team_id, display_name in FEATURED_TEAMS})
        return catalog, aliases

    # UCL datasets are kept alongside the other project datasets.  Keep this
    # registry path aligned with CompetitionSpec.training_data and the files
    # committed under data/processed/.
    data_root = project_root / "data" / "processed"
    teams_path = data_root / "ucl_teams.csv"
    aliases_path = data_root / "ucl_team_aliases.csv"
    matches_path = data_root / "ucl_matches.csv"
    for path in (teams_path, aliases_path, matches_path):
        if not path.is_file():
            raise FileNotFoundError(f"Registry UCL tidak ditemukan: {path}")

    teams = pd.read_csv(teams_path).fillna("")
    matches = pd.read_csv(matches_path, usecols=["season", "home_team", "away_team"])
    latest_season = str(matches["season"].max())
    current_clubs = set(
        matches.loc[matches["season"].astype(str) == latest_season, "home_team"].astype(str)
    ) | set(
        matches.loc[matches["season"].astype(str) == latest_season, "away_team"].astype(str)
    )

    catalog: Dict[str, dict] = {}
    for _, row in teams.iterrows():
        team_id = str(row["team_name"])
        association = str(row.get("association_code", ""))
        code = UEFA_ASSOCIATION_TO_ISO2.get(association, "")
        catalog[team_id] = {
            "name": team_id,
            "code": code,
            "flag": _flag_from_code(code),
            "association_code": association,
            "featured": team_id in current_clubs,
            "latest_elo": float(row["latest_elo"]) if row.get("latest_elo", "") != "" else None,
            "matches": int(row["matches"]) if row.get("matches", "") != "" else 0,
        }

    aliases_frame = pd.read_csv(aliases_path).fillna("")
    aliases: Dict[str, str] = {}
    for _, row in aliases_frame.iterrows():
        canonical = str(row["canonical_name"])
        aliases[str(row["raw_name"])] = canonical
        aliases[str(row["team_id"])] = canonical
    return catalog, aliases


def build_runtime_artifact(
    project_root: Path | str,
    output_path: Path | str,
    competition_id: str = DEFAULT_COMPETITION_ID,
) -> Dict[str, Any]:
    """Train and serialize the web runtime once; never called during an HTTP request."""
    from collections import Counter

    import sklearn
    from sklearn.calibration import CalibratedClassifierCV

    try:
        import xgboost
        from xgboost import XGBClassifier

        model_backend = "xgboost"
        xgboost_version = xgboost.__version__
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier

        XGBClassifier = None
        model_backend = "sklearn_hist_gradient_boosting"
        xgboost_version = "not-installed"
        warnings.warn(
            "XGBoost tidak tersedia; memakai fallback sklearn untuk runtime ini. "
            "Jalankan setup_windows.bat agar runtime produksi memakai XGBoost."
        )

    root = Path(project_root).resolve()
    output = Path(output_path).resolve()
    competition_id = resolve_competition_id(competition_id)
    competition = COMPETITIONS[competition_id]
    matches = _load_training_matches(root, competition_id)
    professional, team_stats = build_professional_features(matches)

    dc_model = _load_dixon_coles_parameters(root, competition_id)
    if dc_model is None and competition_id == DEFAULT_COMPETITION_ID:
        dc_model = _load_legacy_dixon_coles(root)
    if dc_model is None:
        ratings = None
        if competition_id == DEFAULT_COMPETITION_ID:
            ratings_path = root / "outputs" / "team_rating.csv"
            if ratings_path.is_file():
                ratings = pd.read_csv(ratings_path).set_index("team")
        dc_model = DixonColesModel(xi=0.0018, ridge=1e-3).fit(matches, ratings)
        export_dixon_coles_parameters(
            dc_model,
            root / "models" / competition.dc_params_filename,
        )

    training = professional.dropna(subset=["result"]).copy()
    training["y"] = training["result"].map({"H": 0, "D": 1, "A": 2})
    training = training.dropna(subset=["y"])
    dc_rows = []
    for _, match in training.iterrows():
        probability = matrix_outcome_probs(
            dc_model.score_matrix(match["home_team"], match["away_team"], MAX_GOALS)
        )
        dc_rows.append(
            {"dc_p_h": probability["H"], "dc_p_d": probability["D"], "dc_p_a": probability["A"]}
        )
    training = training.join(pd.DataFrame(dc_rows, index=training.index))
    x = training[ALL_FEATS_V3].fillna(0)
    y = training["y"].astype(int).to_numpy()
    counts = Counter(y)
    sample_weights = np.array([len(y) / (3 * counts[label]) for label in y])

    if XGBClassifier is not None:
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
    else:
        base_model = HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=220,
            max_leaf_nodes=31,
            l2_regularization=1e-3,
            random_state=RANDOM_SEED,
        )
    model_v3 = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
    model_v3.fit(x, y, sample_weight=sample_weights)

    team_catalog, aliases = _build_team_catalog(root, competition_id, dc_model)

    artifact: Dict[str, Any] = {
        "schema_version": MODEL_SCHEMA_VERSION,
        "dc_model": dc_model,
        "model_v3": model_v3,
        "team_stats": team_stats,
        "feature_columns": list(ALL_FEATS_V3),
        "team_catalog": team_catalog,
        "aliases": aliases,
        "metadata": {
            "model_name": "MatchIQ Hybrid v3",
            "competition": competition.public_payload(),
            "model_backend": model_backend,
            "training_matches": int(len(training)),
            "data_until": matches["date"].max().date().isoformat(),
            "built_at": datetime.now(timezone.utc).isoformat(),
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost_version,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output.with_name(f".{output.name}.tmp")
    try:
        joblib.dump(artifact, temporary_output, compress=3)
        temporary_output.replace(output)
    finally:
        if temporary_output.exists():
            temporary_output.unlink()
    return artifact["metadata"]
