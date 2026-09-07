# Data Dictionary — `ucl_matches.csv`

| Column | Type | Description |
|---|---|---|
| `match_id` | string | Stable match identifier generated per season |
| `competition` | string | UEFA Champions League |
| `season` | string | Season label such as `2025-26` |
| `date` | date | Match date, `YYYY-MM-DD` |
| `kickoff_time` | time | Local source kickoff time |
| `kickoff_datetime` | datetime | Combined sortable kickoff timestamp |
| `stage_raw` | string | Original stage label from source |
| `stage` | category | Normalized competition stage |
| `stage_order` | integer | Ordered stage code from qualifier to final |
| `matchday` | integer/null | League/playoff matchday where available |
| `group` | string/null | Group A-H where available |
| `leg` | category | `1`, `2`, `single`, or `not_applicable` |
| `is_qualifier` | 0/1 | Indicates a qualification-stage match |
| `neutral` | 0/1 | Inferred neutral venue flag |
| `home_team_id` | string | Stable normalized home club ID |
| `away_team_id` | string | Stable normalized away club ID |
| `home_team` | string | Canonical home club display name |
| `away_team` | string | Canonical away club display name |
| `home_team_raw` | string | Original home name from source |
| `away_team_raw` | string | Original away name from source |
| `home_country_code` | string | Source association code |
| `away_country_code` | string | Source association code |
| `home_goals` | integer | Home goals after 90 minutes |
| `away_goals` | integer | Away goals after 90 minutes |
| `home_goals_final` | integer | Home goals after extra time, if used |
| `away_goals_final` | integer | Away goals after extra time, if used |
| `home_goals_ht` | integer/null | Home goals at half-time where available |
| `away_goals_ht` | integer/null | Away goals at half-time where available |
| `home_penalty` | integer/null | Home penalty-shootout score |
| `away_penalty` | integer/null | Away penalty-shootout score |
| `decided_by` | category | Normal Time, Extra Time, or Penalties |
| `result` | category | Regulation-time result: H, D, or A |
| `total_goals` | integer | Regulation-time total goals |
| `goal_diff` | integer | Home goals minus away goals |
| `btts` | 0/1 | Both teams scored in regulation time |
| `home_elo_pre` | float | Home Elo immediately before kickoff |
| `away_elo_pre` | float | Away Elo immediately before kickoff |
| `elo_diff_pre` | float | Home Elo plus advantage minus away Elo |
| `home_matches_before` | integer | Prior UCL matches available for home club |
| `away_matches_before` | integer | Prior UCL matches available for away club |
| `score_raw` | string | Original score notation |
| `source_file` | string | Traceable source file path |
| `source_line` | integer | Traceable line number in source file |
| `source_commit` | string | Exact Git commit used |
