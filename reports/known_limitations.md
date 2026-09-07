# Known Limitations

1. **UCL-only context**  
   The derived Elo rating observes only matches contained in this Champions League source.
   Domestic league form is not included, so clubs entering the competition for the first time
   start close to the baseline rating.

2. **No xG or squad availability**  
   Expected goals, line-ups, player injuries, suspensions, market odds, and coaching changes are
   not available in the source. They should be added as separate, time-stamped features if needed.

3. **Qualifier coverage**  
   Qualifier files are present only for 2024-25 and 2025-26. For consistency, the recommended
   training file excludes qualifiers; they remain available in `ucl_matches_all.csv`.

4. **Neutral venue inference**  
   Finals are marked neutral. Quarterfinals and semifinals in the Lisbon 2019-20 finish are also
   marked neutral. Other exceptional relocations cannot be inferred reliably from the source.

5. **Club identity normalization**  
   Renamed variants such as `Real Madrid CF`/`Real Madrid`, `Inter`/`FC Internazionale Milano`,
   and `Bayern München`/`FC Bayern München` are merged. Review `ucl_team_aliases.csv` before
   adding another data source.

6. **Prediction interpretation**  
   The 1X2 target refers to 90 minutes. Extra time and penalties must not be folded into the
   regulation-time result. Qualification probability for two-legged ties needs aggregate-state
   features that are not part of a normal single-match 1X2 prediction.
