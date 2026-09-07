from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from matchiq.web import create_app  # noqa: E402


def main() -> int:
    app = create_app({"TESTING": True})
    with app.test_client() as client:
        health = client.get("/health")
        assert health.status_code == 200, health.get_data(as_text=True)

        home = client.get("/")
        assert home.status_code == 200
        assert b"MatchIQ" in home.data

        competitions = client.get("/api/competitions")
        assert competitions.status_code == 200
        assert [item["id"] for item in competitions.get_json()["competitions"]] == [
            "world_cup",
            "ucl",
        ]

        cases = (
            ("world_cup", "France", "England", 48),
            ("ucl", "Real Madrid", "FC Barcelona", 161),
        )
        for competition, home_team, away_team, team_count in cases:
            teams = client.get(f"/api/teams?competition={competition}")
            assert teams.status_code == 200
            assert len(teams.get_json()["teams"]) >= team_count

            response = client.post(
                "/api/predict",
                json={
                    "competition": competition,
                    "home_team": home_team,
                    "away_team": away_team,
                    "handicap": -1.5,
                },
            )
            assert response.status_code == 200, response.get_data(as_text=True)
            prediction = response.get_json()["prediction"]
            outcomes = prediction["one_x_two"]
            assert prediction["competition"]["id"] == competition
            assert abs(sum(outcomes.values()) - 1.0) < 1e-4
            assert len(prediction["score_matrix"]) == 8
            assert len(prediction["top_scores"]) == 10

    print("[OK] Flask, runtime Piala Dunia/UCL, API, dan halaman MatchIQ berfungsi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
