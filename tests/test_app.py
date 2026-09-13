from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import numpy as np

from matchiq.web import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MatchIQAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()

    def test_home_and_health(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        markup = home.get_data(as_text=True)
        self.assertIn('id="result-score-home"', markup)
        self.assertIn('class="score-separator"', markup)
        self.assertNotIn('id="result-home-flag"', markup)
        self.assertNotIn('id="result-away-flag"', markup)
        self.assertIn('id="competition"', markup)
        self.assertIn('id="result-model-chip"', markup)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_competition_registry_contract(self):
        response = self.client.get("/api/competitions")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["default"], "world_cup")
        self.assertEqual(
            [competition["id"] for competition in payload["competitions"]],
            ["world_cup", "ucl"],
        )

    def test_teams_include_world_cup_selection(self):
        response = self.client.get("/api/teams")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        featured = [team for team in payload["teams"] if team["featured"]]
        self.assertEqual(len(featured), 48)

    def test_ucl_team_catalog_and_prediction(self):
        teams_response = self.client.get("/api/teams?competition=ucl")
        self.assertEqual(teams_response.status_code, 200)
        teams_payload = teams_response.get_json()
        self.assertEqual(teams_payload["competition"]["id"], "ucl")
        self.assertEqual(len(teams_payload["teams"]), 161)
        featured = [team for team in teams_payload["teams"] if team["featured"]]
        self.assertEqual(len(featured), 36)
        team_ids = {team["id"] for team in teams_payload["teams"]}
        self.assertIn("Real Madrid", team_ids)
        self.assertIn("FC Barcelona", team_ids)

        prediction_response = self.client.post(
            "/api/predict",
            json={
                "competition": "ucl",
                "home_team": "Real Madrid",
                "away_team": "FC Barcelona",
                "handicap": -1.5,
            },
        )
        self.assertEqual(prediction_response.status_code, 200)
        prediction = prediction_response.get_json()["prediction"]
        self.assertEqual(prediction["competition"]["id"], "ucl")
        self.assertEqual(prediction["model"]["competition_id"], "ucl")
        self.assertEqual(prediction["model"]["pipeline_version"], "ucl_v4_audited")
        self.assertEqual(prediction["model"]["name"], "MatchIQ UCL v4 Audited")
        self.assertEqual(prediction["model"]["training_matches"], 1997)
        self.assertAlmostEqual(sum(prediction["one_x_two"].values()), 1.0, places=4)
        self.assertEqual(len(prediction["score_matrix"]), 8)
        matrix = np.asarray(prediction["score_matrix"])
        home_grid, away_grid = np.meshgrid(np.arange(8), np.arange(8), indexing="ij")
        self.assertAlmostEqual(
            float(matrix[home_grid > away_grid].sum()),
            prediction["one_x_two"]["home"],
            places=4,
        )
        self.assertAlmostEqual(
            float(matrix[home_grid == away_grid].sum()),
            prediction["one_x_two"]["draw"],
            places=4,
        )
        self.assertAlmostEqual(
            float(matrix[home_grid < away_grid].sum()),
            prediction["one_x_two"]["away"],
            places=4,
        )

    def test_invalid_competition_is_rejected(self):
        response = self.client.post(
            "/api/predict",
            json={
                "competition": "premier_league",
                "home_team": "France",
                "away_team": "England",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "invalid_competition")

    def test_prediction_contract(self):
        response = self.client.post(
            "/api/predict",
            json={"home_team": "France", "away_team": "England", "handicap": -1.5},
        )
        self.assertEqual(response.status_code, 200)
        prediction = response.get_json()["prediction"]
        self.assertAlmostEqual(sum(prediction["one_x_two"].values()), 1.0, places=4)
        self.assertEqual(len(prediction["score_matrix"]), 8)
        self.assertEqual(len(prediction["score_matrix"][0]), 8)
        self.assertEqual(len(prediction["over_under"]), 6)

    def test_alias_and_validation(self):
        alias_response = self.client.post(
            "/api/predict",
            json={"home_team": "USA", "away_team": "South Korea", "handicap": 0},
        )
        self.assertEqual(alias_response.status_code, 200)

        same_team = self.client.post(
            "/api/predict",
            json={"home_team": "Brazil", "away_team": "Brazil"},
        )
        self.assertEqual(same_team.status_code, 400)

    def test_score_market_regression_matches_notebook_output(self):
        response = self.client.post(
            "/api/predict",
            json={"home_team": "Mexico", "away_team": "South Africa", "handicap": -1.5},
        )
        prediction = response.get_json()["prediction"]
        over_25 = next(item for item in prediction["over_under"] if item["line"] == 2.5)
        self.assertEqual(prediction["headline"]["score"], "1-0")
        self.assertAlmostEqual(prediction["btts"]["yes"], 0.2552, places=3)
        self.assertAlmostEqual(over_25["over"], 0.2013, places=3)

    def test_frontend_motion_and_team_option_contract(self):
        css = (PROJECT_ROOT / "static" / "css" / "app.css").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn("@keyframes hero-title-shimmer", css)
        self.assertIn("@keyframes signal-float", css)
        self.assertIn("@keyframes model-grid-wave", css)
        self.assertIn("@keyframes model-line-wave", css)
        self.assertIn("@keyframes model-orbit-tracer", css)
        self.assertNotIn("@keyframes result-text-shimmer", css)
        self.assertNotIn("@keyframes result-bar-flow", css)
        self.assertNotIn("@keyframes donut-breathe", css)
        self.assertNotIn("transition: width 700ms", css)
        self.assertIn("option.textContent = team.name;", js)
        self.assertNotIn("option.textContent = `${team.flag}", js)
        self.assertIn('competition: state.competitionId', js)
        self.assertIn('/api/competitions', js)

    def test_ucl_notebook_training_and_evaluation_contract(self):
        path = PROJECT_ROOT / "notebooks" / "MatchIQ_UCL_Hybrid_AI_Training.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        metadata = notebook["metadata"]["matchiq"]
        self.assertEqual(metadata["competition"], "ucl")
        self.assertEqual(metadata["pipeline"], "hybrid_v3")
        self.assertEqual(metadata["temporal_holdout"], "2025-26")

        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertGreaterEqual(len(code_cells), 12)
        for index, cell in enumerate(code_cells, start=1):
            ast.parse("".join(cell["source"]), filename=f"ucl-notebook-cell-{index}")
            self.assertFalse(
                any(output.get("output_type") == "error" for output in cell.get("outputs", []))
            )

        source = "\n".join("".join(cell["source"]) for cell in code_cells)
        self.assertIn('HOLDOUT_SEASON = "2025-26"', source)
        self.assertIn("DixonColesModel", source)
        self.assertIn("XGBClassifier", source)
        self.assertIn("hybrid_probabilities", source)
        self.assertIn("calibration_curve", source)
        self.assertIn("MatchIQEngine", source)

    def test_ucl_v4_audited_notebook_contract(self):
        path = PROJECT_ROOT / "notebooks" / "MatchIQ_UCL_v4_Audited.ipynb"
        notebook = json.loads(path.read_text(encoding="utf-8"))
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertGreaterEqual(len(code_cells), 10)
        for index, cell in enumerate(code_cells, start=1):
            ast.parse("".join(cell["source"]), filename=f"ucl-v4-cell-{index}")
            self.assertFalse(
                any(output.get("output_type") == "error" for output in cell.get("outputs", []))
            )
        source = "\n".join("".join(cell["source"]) for cell in code_cells)
        self.assertIn("FORBIDDEN", source)
        self.assertIn("future-label invariance", source)
        self.assertIn("apply_calibration", source)
        self.assertIn("matchiq-ucl-v4-audited", source)


if __name__ == "__main__":
    unittest.main()
