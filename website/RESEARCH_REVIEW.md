# Script review for the Bengaluru Heat Atlas

Reviewed the 51 numbered scripts (00–50, including 12a), `verify.py`, the supporting `src/urban_heat` modules, the handoff, and final JSON/CSV outputs. This was a source review and local data cross-check, not a rerun of Earth Engine or model training. No analysis script, model, classification or original export was changed.

## Pipeline understood

| Scripts | Role |
|---|---|
| 00–14 | Earth Engine connection; Landsat LST / optical indices; cloud masking; Sentinel-2 and ERA5 matching; initial samples |
| 15–18 | Data exploration; linear regression and Random Forest; saved baseline; first predicted heat map |
| 19–23 | Multi-year sampling and V1–V3 features / temporal model comparisons |
| 24–30 | Date evaluation, V4 spatial context, April 17 investigation, V5 overpass weather, final model and predictions |
| 31–34 | Cooling scores, early 500 m greening plan, 1 km persistent summaries and map |
| 35–41 | Complete grid, spatial features, imputation, V5 predictions, surface agreement, hybrid merge, final cooling scenario |
| 42–45 | Map, locality labels, eight-neighbour clusters, intensity and planning significance |
| 46–50 | Charts, report summaries and the six website JSON exports |

## Details that affect website interpretation

1. **The “observation” source labels do not mean measured map temperatures.** Script 30 predicts `Predicted_LST`; 31 carries it forward; 33 aggregates that column into `Median_Predicted_LST`. Script 40 renames those values to `Reliable_Median_LST` and prioritizes them in the merge. Thus the final map combines two model-derived summaries, with differing observational support. The website preserves the original data-source labels and explains their meaning.
2. **Limited cells are not numerically blended observations + predictions.** Script 40 selects the complete-grid V5 values when no reliable earlier summary exists. The Limited label distinguishes one or two sampled dates of support, not an arithmetic blend.
3. **The final classes are recomputed.** Script 40 retains earlier temperature/frequency/spatial summaries where available but normalizes the final grid and recomputes its heat score and percentile-based classes. The handoff's statement about preserving earlier persistent results should not be read as preserving their original classes.
4. **Hot frequency has two denominators.** Script 33 divides hot sample rows by total sample rows. Multiple samples per date contribute. Script 38 averages flags over grid-date predictions. Their hot thresholds also come from different prediction distributions. Neither is a fraction of all days in the season.
5. **Model comparisons have different sample populations.** The final common V5-dataset comparison gives V3 MAE 2.4238, RMSE 3.1134 and R² 0.5959. Earlier V3 values in the handoff refer to a different comparison. The website uses the saved common-dataset table and identifies the earlier figures separately.
6. **Model selection used the 2026 evaluation.** Training uses years through 2025; V3–V5 are compared on 2026, which is then used for selection. Do not call it an untouched final test or a spatially independent validation. Applying point-trained models to cell-average features is also a scale change.
7. **Surface agreement is not ground validation.** Script 39 compares two predicted surfaces with different score formulas. Its 38.05% class agreement is not model classification accuracy against measured ground truth.
8. **Cluster scoring uses transformations.** Script 45 normalizes `log1p(area)` and `log1p(Very High count)`, plus normalized heat/frequency terms. A plain weighted sum of raw km², counts and scores would not reproduce the rankings. Cluster adjacency includes diagonals.
9. **Tree counts are per-cell rounded scenarios.** Script 41 computes cooling area, applies a built-probability-dependent tree share, divides canopy target by 30 m², and rounds upward in each cell. It does not model species, survival, planting feasibility or degrees of cooling.

## Earlier script and documentation issues to revisit

- Script 03's rectangle has `7.75` as the east longitude instead of `77.75`. Later final-dataset scripts use `77.75`; do not infer that this typo contaminated the final outputs without rerunning provenance checks.
- Script 07 labels a green/SWIR normalized difference as NDWI, whereas script 06 and the final dataset scripts use green/NIR. These are different indices; the final website documents the final green/NIR version.
- Script 12a sorts on `CLOUD_PIXEL_PERCENTAGE`; the filtering property and later scripts use `CLOUDY_PIXEL_PERCENTAGE`.
- Script 20 is named `train_multidate_model` but builds the enhanced dataset. Its filename does not describe its actual role.
- The root README and `src/urban_heat` package describe an earlier pilot with a different grid and stricter QA rules; the numbered workflow is now much further along. The website does not claim that unused pilot checks were applied to the final outputs.
- Script 42 reads the pre-locality CSV; rerunning it alone will not add script 43's locality names. The website reads the final locality-enriched JSON.
- Some generated chart/map templates contain replacement characters for degree/squared symbols. The new website uses proper Unicode and live data-driven charts.

## Cross-checked output totals

- 1,320 records and 1,320 unique grid IDs; 73 clusters.
- Priority cells: Low 660; Moderate 330; High 198; Very High 132.
- Reliability: Strong 111; Moderate 567; Limited 578; Model Only 64.
- Tree scenario: 1,362,505 total.
- Actual exported bounds: 12.7919511319–13.1512756019° N, 77.4459721532–77.7501879705° E.

`prepare_data.py` copies the original six JSON exports unchanged into `dist/data`. It also exports the original `Grid_ID → Cluster_ID` mapping from script 44's output and the saved model comparison/feature metrics. It does not recalculate the research.
