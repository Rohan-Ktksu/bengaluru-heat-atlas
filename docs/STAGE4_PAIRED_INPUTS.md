# Paired V5 inputs and experimental inference

The manual **Pair scenes and prepare V5 inputs (review only)** workflow searches new Landsat 8 scenes and looks for Sentinel-2 within the historical `[-5 days, +5 days)` window. It never uses the independently selected Stage 3 Sentinel date without checking the temporal match.

## Gates and bounded search

- Initial midnight state dates represent whole processed days, preventing reprocessing May 3 as a new observation just because the satellite overpass occurred after midnight.
- Search the latest 10 new Landsat L2SP scenes with scene cloud <20%. For each, inspect up to 10 Sentinel scenes with scene cloud <20% within the matching window. Limits are explicit: no result means no pair among these bounded candidates, not proof that no possible imagery exists.
- Require at least 80% jointly valid area across the entire canonical study footprint. Masked/uncovered pixels count as invalid. The Landsat mask includes the surface-temperature band, making the coverage gate conservative where thermal retrieval is missing.
- Preserve all 1,320 IDs. Only cells with at least 70% valid coverage and all 25 finite, in-range features are eligible for inference. These are initial review thresholds, not calibrated confidence levels.
- Preserve the historical scientific formulas and report missing data rather than imputing old values into new dates.

No-compatible-pair runs produce a successful, explicit **no compatible pair** report with candidate diagnostics and zero inference-eligible cells. Such a result must not advance state or trigger predictions/publication.

## Completed feature contract

`v5_schema.py` freezes all 25 ordered features from script 30. Tests compare it directly to that original script.

Spatial inputs use the Landsat/Sentinel formulas from Stage 3 plus SRTM elevation, script 36's JRC occurrence >=50% water-distance transform (100 m UTM grid, 250-pixel neighbourhood, capped at 25 km), and Dynamic World mean tree/built probabilities within Landsat +/-5 days.

The 11 non-overpass weather features reproduce script 22's transformations and UTC windows:

- Air temperature, wind magnitude of mean components, relative humidity and soil moisture: acquisition to acquisition +24 hours.
- Precipitation: sums over the preceding 1, 3 and 7 days, metres to millimetres.
- Solar radiation: previous-day hourly accumulations summed, J/m² to MJ/m².
- Cloud cover: previous-day ERA5 mean, fraction to percent.
- Air temperature history: preceding 3/7-day means, kelvin to Celsius.

Every hourly window must contain the expected unique consecutive timestamps. Because four inputs use the 24 hours **after** acquisition, this is retrospective inference, not a live forecast. The five overpass variables retain script 28's +/-90-minute/AOI averaging method.

To reproduce script 37's date-level weather summaries, weather is sampled at 30 m over the original weather AOI using up to 750 requested samples under the valid feature mask, then median-aggregated. New dates use deterministic seed 42. Historical scripts used scene-loop-dependent seeds and somewhat different masks; this sampling difference must be checked before operational use. No scaler is applied. Historical script 37 imputed missing spatial values; this workflow deliberately excludes incomplete cells instead and documents that change.

## Inference helper

`predict_v5_review.py` accepts a validated input artifact and a local model path. Before loading the pickle, it checks the original V5 SHA-256 against `MODEL_MANIFEST.json`, checks the recorded scikit-learn/numpy/joblib versions, and verifies the serialized feature order. It predicts eligible cells only and writes an experimental result and observed-LST comparison inside the review artifact.

```sh
python automation/predict_v5_review.py latest_data/v5-inputs --model /trusted/path/urban_heat_model_v5.pkl
```

No model is downloaded automatically. No model is retrained. Predictions are not added to the historical website or labeled operationally validated. Comparing predicted grid means with observed grid means is a diagnostic; it is not an independent accuracy certification of a model trained on pixel samples.

State advancement, rolling heat scores, hotspot recalculation and public latest-conditions deployment remain outside this workflow.
