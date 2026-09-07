from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, render_template, request

from .competitions import (
    COMPETITIONS,
    DEFAULT_COMPETITION_ID,
    competition_payloads,
    resolve_competition_id,
)
from .engine import MatchIQEngine, ModelArtifactError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATHS = {
    competition_id: str(spec.model_path(PROJECT_ROOT))
    for competition_id, spec in COMPETITIONS.items()
}


def create_app(test_config: Optional[dict] = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=16 * 1024,
        JSON_SORT_KEYS=False,
        MODEL_PATH=DEFAULT_MODEL_PATHS[DEFAULT_COMPETITION_ID],
        MODEL_PATHS=dict(DEFAULT_MODEL_PATHS),
    )
    if test_config:
        app.config.update(test_config)

    model_paths = dict(DEFAULT_MODEL_PATHS)
    configured_paths = app.config.get("MODEL_PATHS")
    if isinstance(configured_paths, dict):
        model_paths.update({str(key): str(value) for key, value in configured_paths.items()})
    if test_config and "MODEL_PATH" in test_config:
        model_paths[DEFAULT_COMPETITION_ID] = str(test_config["MODEL_PATH"])
    app.config["MODEL_PATHS"] = model_paths

    engine_lock = threading.Lock()
    engines: dict[str, MatchIQEngine] = {}

    def get_engine(competition_id: str) -> MatchIQEngine:
        competition_id = resolve_competition_id(competition_id)
        if competition_id not in engines:
            with engine_lock:
                if competition_id not in engines:
                    engines[competition_id] = MatchIQEngine(
                        app.config["MODEL_PATHS"][competition_id]
                    )
        return engines[competition_id]

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; font-src 'self'; base-uri 'self'; "
            "form-action 'self'"
        )
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        readiness = {
            competition_id: Path(app.config["MODEL_PATHS"][competition_id]).is_file()
            for competition_id in COMPETITIONS
        }
        ready = all(readiness.values())
        return jsonify(
            {
                "ok": ready,
                "service": "MatchIQ",
                "model_ready": ready,
                "models": readiness,
            }
        ), (200 if ready else 503)

    @app.get("/api/competitions")
    def competitions():
        return jsonify(
            {
                "ok": True,
                "default": DEFAULT_COMPETITION_ID,
                "competitions": competition_payloads(),
            }
        )

    @app.get("/api/teams")
    def teams():
        try:
            competition_id = resolve_competition_id(request.args.get("competition"))
            predictor = get_engine(competition_id)
            return jsonify(
                {
                    "ok": True,
                    "competition": predictor.competition,
                    "teams": predictor.teams(),
                    "model": predictor.metadata,
                }
            )
        except ValueError as exc:
            return jsonify(
                {"ok": False, "error": "invalid_competition", "message": str(exc)}
            ), 400
        except ModelArtifactError as exc:
            return jsonify(
                {"ok": False, "error": "model_unavailable", "message": str(exc)}
            ), 503

    @app.get("/api/model")
    def model_info():
        try:
            competition_id = resolve_competition_id(request.args.get("competition"))
            predictor = get_engine(competition_id)
            return jsonify(
                {
                    "ok": True,
                    "competition": predictor.competition,
                    "model": predictor.metadata,
                }
            )
        except ValueError as exc:
            return jsonify(
                {"ok": False, "error": "invalid_competition", "message": str(exc)}
            ), 400
        except ModelArtifactError as exc:
            return jsonify(
                {"ok": False, "error": "model_unavailable", "message": str(exc)}
            ), 503

    @app.post("/api/predict")
    def predict():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(
                {"ok": False, "error": "invalid_json", "message": "Body JSON tidak valid."}
            ), 400

        try:
            competition_id = resolve_competition_id(payload.get("competition"))
        except ValueError as exc:
            return jsonify(
                {"ok": False, "error": "invalid_competition", "message": str(exc)}
            ), 400

        home_team = str(payload.get("home_team", "")).strip()
        away_team = str(payload.get("away_team", "")).strip()
        if not home_team or not away_team:
            return jsonify(
                {
                    "ok": False,
                    "error": "missing_team",
                    "message": "Pilih tim kandang dan tim tandang.",
                }
            ), 400
        try:
            handicap = float(payload.get("handicap", -1.5))
        except (TypeError, ValueError):
            return jsonify(
                {
                    "ok": False,
                    "error": "invalid_handicap",
                    "message": "Nilai handicap tidak valid.",
                }
            ), 400

        try:
            result = get_engine(competition_id).predict(home_team, away_team, handicap)
        except ValueError as exc:
            return jsonify(
                {"ok": False, "error": "invalid_input", "message": str(exc)}
            ), 400
        except ModelArtifactError as exc:
            return jsonify(
                {"ok": False, "error": "model_unavailable", "message": str(exc)}
            ), 503
        return jsonify(
            {
                "ok": True,
                "competition": result["competition"],
                "prediction": result,
            }
        )

    return app
