from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln


PIPELINE_VERSION = "ucl_v4_audited"
RANDOM_SEED = 42
TRAINING_MAX_GOALS = 12
H2H_HALF_LIFE_DAYS = 730.0
H2H_PRIOR_STRENGTH = 5.0
ELO_K_FACTORS = {
    "group_stage": 24.0,
    "league_phase": 24.0,
    "playoff": 28.0,
    "round_of_16": 32.0,
    "quarterfinal": 36.0,
    "semifinal": 40.0,
    "final": 48.0,
}
STAGES = list(ELO_K_FACTORS)
LABELS = ("home", "draw", "away")


def _normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(probabilities, dtype=float), 1e-8, 1 - 1e-8)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    return values / values.sum(axis=1, keepdims=True)


def poisson_pmf(k: np.ndarray, lam: float) -> np.ndarray:
    values = np.asarray(k, dtype=float)
    rate = np.asarray(lam, dtype=float)
    return np.exp(
        values * np.log(np.clip(rate, 1e-10, None))
        - rate
        - gammaln(values + 1)
    )


def dixon_coles_tau(
    x: np.ndarray,
    y: np.ndarray,
    lam: np.ndarray | float,
    mu: np.ndarray | float,
    rho: float,
) -> np.ndarray:
    x_values, y_values = np.asarray(x), np.asarray(y)
    tau = np.ones(np.broadcast(x_values, y_values, lam, mu).shape, dtype=float)
    tau = np.where((x_values == 0) & (y_values == 0), 1 - lam * mu * rho, tau)
    tau = np.where((x_values == 0) & (y_values == 1), 1 + lam * rho, tau)
    tau = np.where((x_values == 1) & (y_values == 0), 1 + mu * rho, tau)
    tau = np.where((x_values == 1) & (y_values == 1), 1 - rho, tau)
    return tau


def _poisson_logpmf(k: np.ndarray, lam: np.ndarray) -> np.ndarray:
    rate = np.clip(lam, 1e-10, None)
    return k * np.log(rate) - rate - gammaln(k + 1)


@dataclass
class UCLDixonColesModel:
    xi: float = 0.0018
    ridge: float = 0.01
    rho_bounds: Tuple[float, float] = (-0.3, 0.3)
    teams_: List[str] = field(default_factory=list)
    team_idx_: Dict[str, int] = field(default_factory=dict)
    log_attack_: Optional[np.ndarray] = None
    log_defense_: Optional[np.ndarray] = None
    log_home_advantage_: float = 0.0
    rho_: float = 0.0
    fit_result_: Optional[object] = None

    def fit(self, frame: pd.DataFrame, verbose: bool = True) -> "UCLDixonColesModel":
        data = frame.sort_values("date").reset_index(drop=True)
        self.teams_ = sorted(set(data["home_team"]) | set(data["away_team"]))
        self.team_idx_ = {team: index for index, team in enumerate(self.teams_)}
        count = len(self.teams_)
        home_index = data["home_team"].map(self.team_idx_).to_numpy()
        away_index = data["away_team"].map(self.team_idx_).to_numpy()
        home_goals = data["home_goals"].to_numpy(dtype=float)
        away_goals = data["away_goals"].to_numpy(dtype=float)
        home_factor = 1 - data["neutral"].to_numpy(dtype=float)
        days_ago = (data["date"].max() - data["date"]).dt.days.to_numpy()
        weights = np.exp(-self.xi * days_ago) if self.xi > 0 else np.ones(len(data))
        initial = np.concatenate([np.zeros(count * 2), [np.log(1.15), 0.0]])

        def objective(params: np.ndarray) -> float:
            attack = params[:count]
            defense = params[count : 2 * count]
            home_advantage, rho = params[2 * count], params[2 * count + 1]
            lam = np.exp(
                attack[home_index]
                + defense[away_index]
                + home_advantage * home_factor
            )
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
        if not result.success:
            raise RuntimeError(f"Dixon-Coles UCL gagal konvergen: {result.message}")
        self.fit_result_ = result
        self.log_attack_ = result.x[:count]
        self.log_defense_ = result.x[count : 2 * count]
        self.log_home_advantage_ = float(result.x[2 * count])
        self.rho_ = float(result.x[2 * count + 1])
        if verbose:
            print(f"Dixon-Coles UCL v4 converged; NLL={result.fun:.2f}")
        return self

    def _team_parameters(self, team: str) -> Tuple[float, float]:
        if team not in self.team_idx_:
            return 0.0, 0.0
        index = self.team_idx_[team]
        return float(self.log_attack_[index]), float(self.log_defense_[index])

    def predict_lambda(
        self, home_team: str, away_team: str, neutral: int = 0
    ) -> Tuple[float, float]:
        home_attack, home_defense = self._team_parameters(home_team)
        away_attack, away_defense = self._team_parameters(away_team)
        lam = math.exp(
            home_attack
            + away_defense
            + self.log_home_advantage_ * (1 - int(neutral))
        )
        mu = math.exp(away_attack + home_defense)
        return float(lam), float(mu)

    def score_matrix(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = TRAINING_MAX_GOALS,
        neutral: int = 0,
    ) -> np.ndarray:
        lam, mu = self.predict_lambda(home_team, away_team, neutral=neutral)
        goals = np.arange(max_goals + 1)
        matrix = np.outer(poisson_pmf(goals, lam), poisson_pmf(goals, mu))
        home_grid, away_grid = np.meshgrid(goals, goals, indexing="ij")
        matrix *= dixon_coles_tau(home_grid, away_grid, lam, mu, self.rho_)
        matrix = np.clip(matrix, 0, None)
        return matrix / matrix.sum()

    def is_known(self, team: str) -> bool:
        return team in self.team_idx_


def matrix_outcome_probabilities(matrix: np.ndarray) -> np.ndarray:
    size = matrix.shape[0]
    home, away = np.meshgrid(np.arange(size), np.arange(size), indexing="ij")
    return np.asarray(
        [
            matrix[home > away].sum(),
            matrix[home == away].sum(),
            matrix[home < away].sum(),
        ],
        dtype=float,
    )


def new_state() -> dict:
    return {"teams": {}, "pairs": {}, "draws": 0, "n": 0, "last_date": None}


def _team_state(state: dict, name: str) -> dict:
    return state["teams"].get(name, {"elo": 1500.0, "games": [], "last_date": None})


def _weighted_stat(
    games: list[dict], key: str, window: int, prior: float, strength: float = 3.0
) -> float:
    values = [game[key] for game in games[-window:]]
    if not values:
        return prior
    weights = np.power(0.85, np.arange(len(values) - 1, -1, -1))
    return float((np.dot(weights, values) + strength * prior) / (weights.sum() + strength))


def match_features(
    state: dict,
    home: str,
    away: str,
    date: Any,
    stage: str = "league_phase",
    leg: str = "not_applicable",
    neutral: int = 0,
) -> dict:
    match_date = pd.Timestamp(date)
    home_state, away_state = _team_state(state, home), _team_state(state, away)
    neutral = int(neutral)
    leg = str(leg).replace(".0", "")
    draw_prior = (state["draws"] + 5) / (state["n"] + 25)
    values = {
        "neutral": neutral,
        "home_elo_pre": home_state["elo"],
        "away_elo_pre": away_state["elo"],
        "elo_diff_pre": home_state["elo"] - away_state["elo"],
        "abs_elo_diff": abs(home_state["elo"] - away_state["elo"]),
        "is_knockout": int(stage not in ("group_stage", "league_phase")),
        "leg_first": int(leg in ("1", "first")),
        "leg_second": int(leg in ("2", "second")),
        "leg_single": int(leg == "single"),
    }
    for prefix, team in (("h", home_state), ("a", away_state)):
        games = team["games"]
        values[f"{prefix}_history"] = min(len(games), 40)
        values[f"{prefix}_rest_days"] = (
            min((match_date - team["last_date"]).days, 90)
            if team["last_date"] is not None
            else 90
        )
        for size in (5, 10):
            for key, prior in (
                ("gs", 1.3),
                ("gc", 1.3),
                ("points", 1.3),
                ("draw", draw_prior),
            ):
                values[f"{prefix}_{key}_{size}"] = _weighted_stat(
                    games, key, size, prior
                )
        values[f"{prefix}_goal_variance"] = (
            float(np.var([game["gs"] for game in games[-10:]]))
            if len(games) >= 3
            else 1.3
        )
    values["xg_proxy_home"] = float(
        np.clip((values["h_gs_10"] + values["a_gc_10"]) / 2 + 0.15 * (1 - neutral), 0.2, 5)
    )
    values["xg_proxy_away"] = float(
        np.clip((values["a_gs_10"] + values["h_gc_10"]) / 2, 0.2, 5)
    )
    values["xg_total"] = values["xg_proxy_home"] + values["xg_proxy_away"]
    values["xg_abs_diff"] = abs(values["xg_proxy_home"] - values["xg_proxy_away"])
    values["draw_balance"] = float(
        np.exp(-values["xg_abs_diff"] - values["abs_elo_diff"] / 300)
        / (1 + np.exp(values["xg_total"] - 2.5))
    )
    history = state["pairs"].get(tuple(sorted((home, away))), [])
    weighted_history = [
        (2 ** (-(match_date - previous_date).days / H2H_HALF_LIFE_DAYS), draw)
        for previous_date, draw in history
        if previous_date < match_date and (match_date - previous_date).days <= 3650
    ]
    effective = sum(weight for weight, _ in weighted_history)
    values["h2h_effective_meetings"] = effective
    values["h2h_weighted_draw_rate"] = (
        sum(weight * draw for weight, draw in weighted_history)
        + draw_prior * H2H_PRIOR_STRENGTH
    ) / (effective + H2H_PRIOR_STRENGTH)
    values.update({f"stage_{name}": int(stage == name) for name in STAGES})
    return values


def update_state(state: dict, row: Any) -> None:
    home, away, date = row.home_team, row.away_team, pd.Timestamp(row.date)
    for team in (home, away):
        state["teams"].setdefault(
            team, {"elo": 1500.0, "games": [], "last_date": None}
        )
    home_state, away_state = state["teams"][home], state["teams"][away]
    home_goals, away_goals = int(row.home_goals), int(row.away_goals)
    draw = int(home_goals == away_goals)
    expected = 1 / (
        1 + 10 ** ((away_state["elo"] - home_state["elo"] - 70 * (1 - int(row.neutral))) / 400)
    )
    actual = 1.0 if home_goals > away_goals else (0.5 if draw else 0.0)
    leg = str(row.leg).replace(".0", "")
    leg_multiplier = 0.85 if leg in ("1", "first") else (1.15 if leg in ("2", "second") else 1.0)
    margin = min(1.6, 1 + np.log1p(abs(home_goals - away_goals)) / 3)
    shift = ELO_K_FACTORS.get(row.stage, 24.0) * leg_multiplier * margin * (actual - expected)
    home_state["elo"] += shift
    away_state["elo"] -= shift
    for team, scored, conceded in (
        (home_state, home_goals, away_goals),
        (away_state, away_goals, home_goals),
    ):
        team["games"].append(
            {
                "gs": scored,
                "gc": conceded,
                "draw": draw,
                "points": 3 if scored > conceded else (1 if draw else 0),
            }
        )
        team["last_date"] = date
    state["pairs"].setdefault(tuple(sorted((home, away))), []).append((date, draw))
    state["draws"] += draw
    state["n"] += 1
    state["last_date"] = date


def make_features(frame: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    data = frame.sort_values(["date", "match_id"], kind="stable").reset_index(drop=True)
    state, rows = new_state(), []
    for _, daily_matches in data.groupby("date", sort=True):
        for row in daily_matches.itertuples():
            rows.append(
                match_features(
                    state,
                    row.home_team,
                    row.away_team,
                    row.date,
                    row.stage,
                    row.leg,
                    row.neutral,
                )
            )
        for row in daily_matches.itertuples():
            update_state(state, row)
    features = pd.DataFrame(rows)
    overlap = [column for column in features if column in data]
    return data.drop(columns=overlap).join(features), state


def load_matches(path: Path | str) -> pd.DataFrame:
    required = [
        "match_id",
        "season",
        "date",
        "stage",
        "leg",
        "neutral",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "result",
    ]
    frame = pd.read_csv(path)
    missing = [column for column in required if column not in frame]
    if missing:
        raise ValueError(f"Kolom dataset UCL v4 tidak lengkap: {missing}")
    frame = frame[required].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in ("home_goals", "away_goals", "neutral"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[required].isna().any().any():
        raise ValueError("Dataset UCL v4 mengandung nilai wajib kosong.")
    frame["home_goals"] = frame["home_goals"].astype(int)
    frame["away_goals"] = frame["away_goals"].astype(int)
    frame["neutral"] = frame["neutral"].astype(int)
    return frame.sort_values(["date", "match_id"], kind="stable").reset_index(drop=True)


MODEL_SPECS = {
    "xgb_compact": {"kind": "direct", "features": "compact", "depth": 2, "trees": 240, "reg": 6},
    "xgb_full": {"kind": "direct", "features": "full", "depth": 2, "trees": 320, "reg": 8},
    "xgb_depth3": {"kind": "direct", "features": "full", "depth": 3, "trees": 220, "reg": 12},
    "two_stage_full": {"kind": "two_stage", "features": "full", "depth": 2, "trees": 300, "reg": 8},
    "two_stage_compact": {"kind": "two_stage", "features": "compact", "depth": 2, "trees": 240, "reg": 6},
    "logistic_compact": {"kind": "logistic", "features": "compact"},
}


def predict_model(bundle: dict, frame: pd.DataFrame) -> np.ndarray:
    values = frame[bundle["columns"]].to_numpy(dtype=float)
    if bundle["kind"] == "direct":
        return _normalize_probabilities(bundle["models"][0].predict_proba(values))
    draw = bundle["models"][0].predict_proba(values)[:, 1]
    home = bundle["models"][1].predict_proba(values)[:, 1]
    return _normalize_probabilities(
        np.column_stack(((1 - draw) * home, draw, (1 - draw) * (1 - home)))
    )


def apply_calibration(calibration: dict, probabilities: np.ndarray) -> np.ndarray:
    values = _normalize_probabilities(probabilities)
    log_temperature, draw_bias, log_draw_slope = calibration["parameters"]
    logits = np.log(values) / np.exp(log_temperature)
    logits -= logits.max(axis=1, keepdims=True)
    calibrated = _normalize_probabilities(np.exp(logits))
    draw = np.clip(calibrated[:, 1], 1e-7, 1 - 1e-7)
    draw_logit = np.log(draw / (1 - draw))
    draw = 1 / (
        1
        + np.exp(
            -np.clip(np.exp(log_draw_slope) * draw_logit + draw_bias, -25, 25)
        )
    )
    side_home = calibrated[:, 0] / (calibrated[:, 0] + calibrated[:, 2])
    return _normalize_probabilities(
        np.column_stack(((1 - draw) * side_home, draw, (1 - draw) * (1 - side_home)))
    )


def _meta_features(predictions: dict[str, np.ndarray]) -> np.ndarray:
    keys = ("dc", "xgb_compact", "two_stage_full", "logistic_compact")
    return np.concatenate([np.log(_normalize_probabilities(predictions[key])) for key in keys], axis=1)


def combine_predictions(config: dict, predictions: dict[str, np.ndarray]) -> np.ndarray:
    if config["kind"] == "stack":
        return _normalize_probabilities(config["model"].predict_proba(_meta_features(predictions)))
    weight = float(config["weight"])
    return _normalize_probabilities(
        weight * predictions[config["component"]] + (1 - weight) * predictions["dc"]
    )


def predict_pipeline(pipeline: dict, frame: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    predictions = {
        name: predict_model(model, frame) for name, model in pipeline["models"].items()
    }
    predictions["dc"] = _normalize_probabilities(
        np.asarray(
            [
                matrix_outcome_probabilities(
                    pipeline["dc"].score_matrix(
                        row.home_team,
                        row.away_team,
                        max_goals=TRAINING_MAX_GOALS,
                        neutral=int(row.neutral),
                    )
                )
                for row in frame.itertuples()
            ]
        )
    )
    raw = combine_predictions(pipeline["config"], predictions)
    calibrated = apply_calibration(pipeline["calibration"], raw)
    decisions = calibrated.copy()
    decisions[:, 1] *= float(pipeline["multiplier"])
    return calibrated, decisions.argmax(axis=1)


class _Trainer:
    def __init__(self, professional: pd.DataFrame, feature_sets: dict[str, list[str]]):
        self.professional = professional
        self.feature_sets = feature_sets
        self.seasons = sorted(professional["season"].unique())
        self.model_cache: dict[tuple[str, str], dict] = {}
        self.dc_cache: dict[str, UCLDixonColesModel] = {}
        self.prediction_cache: dict[str, dict[str, np.ndarray]] = {}

    @staticmethod
    def _target(frame: pd.DataFrame) -> np.ndarray:
        return frame["result"].map({"H": 0, "D": 1, "A": 2}).to_numpy(dtype=int)

    def _fit_model(self, frame: pd.DataFrame, name: str) -> dict:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from xgboost import XGBClassifier

        spec = MODEL_SPECS[name]
        columns = list(self.feature_sets[spec["features"]])
        x_values = frame[columns].to_numpy(dtype=float)
        y_values = self._target(frame)
        age = (frame["date"].max() - frame["date"]).dt.days.to_numpy()
        weights = 2 ** (-age / (5 * 365.25))
        if spec["kind"] == "logistic":
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(C=0.1, max_iter=1500, random_state=RANDOM_SEED),
            )
            model.fit(x_values, y_values, logisticregression__sample_weight=weights)
            return {"kind": "direct", "models": [model], "columns": columns}
        kwargs = {
            "n_estimators": spec["trees"],
            "max_depth": spec["depth"],
            "reg_lambda": spec["reg"],
            "min_child_weight": 6,
            "reg_alpha": 0.15,
            "learning_rate": 0.03,
            "subsample": 0.9,
            "colsample_bytree": 0.85,
            "tree_method": "hist",
            "n_jobs": 2,
            "random_state": RANDOM_SEED,
        }
        if spec["kind"] == "direct":
            model = XGBClassifier(
                **kwargs,
                objective="multi:softprob",
                num_class=3,
                eval_metric="mlogloss",
            )
            model.fit(x_values, y_values, sample_weight=weights)
            models = [model]
        else:
            draw_model = XGBClassifier(**kwargs, objective="binary:logistic", eval_metric="logloss")
            side_model = XGBClassifier(**kwargs, objective="binary:logistic", eval_metric="logloss")
            draw_model.fit(x_values, (y_values == 1).astype(int), sample_weight=weights)
            mask = y_values != 1
            side_model.fit(
                x_values[mask],
                (y_values[mask] == 0).astype(int),
                sample_weight=weights[mask],
            )
            models = [draw_model, side_model]
        return {"kind": spec["kind"], "models": models, "columns": columns}

    def _model_before(self, season: str, name: str) -> dict:
        key = (season, name)
        if key not in self.model_cache:
            self.model_cache[key] = self._fit_model(
                self.professional.loc[self.professional["season"] < season], name
            )
        return self.model_cache[key]

    def _dc_before(self, season: str) -> UCLDixonColesModel:
        if season not in self.dc_cache:
            self.dc_cache[season] = UCLDixonColesModel().fit(
                self.professional.loc[self.professional["season"] < season],
                verbose=False,
            )
        return self.dc_cache[season]

    def _oof(self, season: str) -> dict[str, np.ndarray]:
        if season not in self.prediction_cache:
            frame = self.professional.loc[self.professional["season"] == season]
            predictions = {
                name: predict_model(self._model_before(season, name), frame)
                for name in MODEL_SPECS
            }
            dc_model = self._dc_before(season)
            predictions["dc"] = _normalize_probabilities(
                np.asarray(
                    [
                        matrix_outcome_probabilities(
                            dc_model.score_matrix(
                                row.home_team,
                                row.away_team,
                                max_goals=TRAINING_MAX_GOALS,
                                neutral=int(row.neutral),
                            )
                        )
                        for row in frame.itertuples()
                    ]
                )
            )
            self.prediction_cache[season] = predictions
            print(f"OOF UCL v4 ready: {season}", flush=True)
        return self.prediction_cache[season]

    def _pooled(self, seasons: list[str]) -> Tuple[pd.DataFrame, dict[str, np.ndarray]]:
        frame = self.professional.loc[self.professional["season"].isin(seasons)].copy()
        predictions = {
            key: np.concatenate([self._oof(season)[key] for season in seasons])
            for key in (*MODEL_SPECS, "dc")
        }
        return frame, predictions

    @staticmethod
    def _fit_stacker(predictions: dict[str, np.ndarray], target: np.ndarray, c_value: float):
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        return make_pipeline(
            StandardScaler(),
            LogisticRegression(C=c_value, max_iter=1500, random_state=RANDOM_SEED),
        ).fit(_meta_features(predictions), target)

    @staticmethod
    def _fit_calibration(target: np.ndarray, probabilities: np.ndarray, method: str) -> dict:
        from sklearn.metrics import log_loss

        if method == "none":
            return {"method": method, "parameters": [0.0, 0.0, 0.0]}
        bounds = (
            [(-0.5, 0.8), (0.0, 0.0), (0.0, 0.0)]
            if method == "temperature"
            else [(-0.5, 0.8), (-1.0, 1.0), (-0.4, 0.4)]
        )

        def objective(parameters: np.ndarray) -> float:
            calibrated = apply_calibration({"parameters": parameters}, probabilities)
            return float(
                log_loss(target, calibrated, labels=[0, 1, 2])
                + 0.03 * np.sum(parameters**2)
            )

        result = minimize(objective, np.zeros(3), method="L-BFGS-B", bounds=bounds)
        if not result.success:
            raise RuntimeError(f"Kalibrasi UCL v4 gagal: {result.message}")
        return {"method": method, "parameters": result.x.tolist()}

    @staticmethod
    def _choose_multiplier(target: np.ndarray, probabilities: np.ndarray) -> float:
        from sklearn.metrics import accuracy_score, f1_score

        base_accuracy = accuracy_score(target, probabilities.argmax(axis=1))
        candidates = []
        for multiplier in np.arange(1, 2.01, 0.1):
            scores = probabilities.copy()
            scores[:, 1] *= multiplier
            predictions = scores.argmax(axis=1)
            accuracy = accuracy_score(target, predictions)
            if accuracy >= base_accuracy - 0.03:
                candidates.append(
                    (
                        f1_score(target, predictions, labels=[0, 1, 2], average="macro", zero_division=0),
                        accuracy,
                        -float(multiplier),
                    )
                )
        return -max(candidates)[2]

    def train(self) -> Tuple[dict, dict]:
        from sklearn.metrics import log_loss

        window = self.seasons[-6:]
        if len(window) != 6:
            raise ValueError("Pipeline UCL v4 memerlukan sedikitnya enam musim.")
        meta_seasons = window[:2]
        dev_calibration = window[2]
        tuning_seasons = window[3:5]
        final_calibration = window[5]
        meta_frame, meta_predictions = self._pooled(meta_seasons)
        dev_frame, dev_predictions = self._pooled([dev_calibration])
        tuning_frame, tuning_predictions = self._pooled(tuning_seasons)
        candidates = [
            {"kind": "blend", "component": name, "weight": float(weight)}
            for name in MODEL_SPECS
            for weight in (0.25, 0.5, 0.75, 1.0)
        ]
        candidates.append({"kind": "blend", "component": "dc", "weight": 1.0})
        for c_value in (0.01, 0.1, 1.0):
            candidates.append(
                {
                    "kind": "stack",
                    "C": c_value,
                    "model": self._fit_stacker(
                        meta_predictions, self._target(meta_frame), c_value
                    ),
                }
            )
        choices = []
        for config in candidates:
            development_raw = combine_predictions(config, dev_predictions)
            tuning_raw = combine_predictions(config, tuning_predictions)
            for method in ("none", "temperature", "draw_temperature"):
                calibration = self._fit_calibration(
                    self._target(dev_frame), development_raw, method
                )
                probabilities = apply_calibration(calibration, tuning_raw)
                seasonal_losses = [
                    log_loss(
                        self._target(tuning_frame.loc[tuning_frame["season"] == season]),
                        probabilities[tuning_frame["season"].to_numpy() == season],
                        labels=[0, 1, 2],
                    )
                    for season in tuning_seasons
                ]
                choices.append(
                    (
                        float(np.mean(seasonal_losses)),
                        float(np.mean(np.sum((probabilities - np.eye(3)[self._target(tuning_frame)]) ** 2, axis=1))),
                        config,
                        method,
                        probabilities,
                    )
                )
        _, _, selected_config, calibration_method, tuning_probabilities = min(
            choices, key=lambda choice: (choice[0], choice[1])
        )
        selected_config = selected_config.copy()
        multiplier = self._choose_multiplier(
            self._target(tuning_frame), tuning_probabilities
        )
        if selected_config["kind"] == "stack":
            stack_frame, stack_predictions = self._pooled(
                meta_seasons + [dev_calibration] + tuning_seasons
            )
            selected_config["model"] = self._fit_stacker(
                stack_predictions,
                self._target(stack_frame),
                float(selected_config["C"]),
            )
        models = {
            name: self._model_before(final_calibration, name) for name in MODEL_SPECS
        }
        dc_model = self._dc_before(final_calibration)
        calibration_frame = self.professional.loc[
            self.professional["season"] == final_calibration
        ]
        calibration_predictions = {
            name: predict_model(model, calibration_frame)
            for name, model in models.items()
        }
        calibration_predictions["dc"] = self._oof(final_calibration)["dc"]
        calibration = self._fit_calibration(
            self._target(calibration_frame),
            combine_predictions(selected_config, calibration_predictions),
            calibration_method,
        )
        dc_model.fit_result_ = None
        split = {
            "meta": meta_seasons,
            "dev_calibration": dev_calibration,
            "tuning": tuning_seasons,
            "final_calibration": final_calibration,
            "kind": selected_config["kind"],
            "component": selected_config.get("component", "stack"),
            "weight": selected_config.get("weight"),
            "calibration_method": calibration_method,
            "draw_multiplier": multiplier,
        }
        return {
            "models": models,
            "dc": dc_model,
            "config": selected_config,
            "calibration": calibration,
            "multiplier": multiplier,
        }, split


def train_ucl_v4(path: Path | str) -> dict:
    matches = load_matches(path)
    professional, final_state = make_features(matches)
    features = list(
        match_features(
            new_state(),
            "A",
            "B",
            matches["date"].min(),
            "group_stage",
            "not_applicable",
            0,
        )
    )
    forbidden = {
        "home_goals_ht",
        "away_goals_ht",
        "home_goals",
        "away_goals",
        "result",
        "total_goals",
        "home_penalty",
        "away_penalty",
        "goal_diff",
        "btts",
    }
    overlap = forbidden.intersection(features)
    if overlap:
        raise RuntimeError(f"Fitur UCL v4 mengalami target leakage: {sorted(overlap)}")
    if not np.isfinite(professional[features].to_numpy(dtype=float)).all():
        raise RuntimeError("Fitur UCL v4 mengandung nilai non-finite.")
    h2h = [column for column in features if column.startswith("h2h_")]
    compact = [
        "neutral",
        "elo_diff_pre",
        "abs_elo_diff",
        "h_gs_10",
        "h_gc_10",
        "a_gs_10",
        "a_gc_10",
        "h_points_10",
        "a_points_10",
        "h_draw_10",
        "a_draw_10",
        "xg_total",
        "xg_abs_diff",
        "draw_balance",
        *h2h,
    ]
    pipeline, split = _Trainer(
        professional, {"full": features, "compact": compact}
    ).train()
    return {
        "pipeline": pipeline,
        "team_state": final_state,
        "feature_columns": features,
        "training_matches": len(matches),
        "data_until": matches["date"].max().date().isoformat(),
        "split": split,
    }
