# Stage 3: latest scene features, for review only

This processor consumes the existing Stage 2 v2 detector report. It extracts only selected scenes newer than `automation/update_state.json`, preserving all 1,320 IDs and rectangles from `src/bengaluru_complete_1km_grid.csv`. It does not advance state, publish website data, train, load a model, or compute new cooling priorities.

Run **Process latest scene features (artifact only)** manually in GitHub Actions. It uses the existing repository Workload Identity variables, runs the existing detector, processes selected scenes and uploads a 14-day review artifact. No daily Stage 3 schedule is enabled.

## Outputs

- `metadata/selected_scenes.json`: exact asset IDs, acquisition times and detector cloud results.
- `metadata/processing_status.json`: transformations, coverage, sensor date separation, overpass weather, and hashes of protected inputs.
- `grid/latest_grid_features.json`: all 1,320 cell IDs, source timestamps, validity fractions, and mean features.
- `summaries/latest_summary.json`: counts of cells passing coverage checks.
- `metadata/validation.json`: independent structural/range/provenance check.

The output folder must be new and under `latest_data/`. Existing folders are rejected to avoid mixing runs. No-new-scenes runs produce a status artifact. Failed runs do not advance state; use Actions logs and any detector artifact for diagnosis.

## Methodology preserved

- **Landsat reflectance:** raw SR × 0.0000275 − 0.2, from script 36.
- **NDVI:** (B5 − B4)/(B5 + B4), after scaling.
- **NDBI:** (B6 − B5)/(B6 + B5), after scaling.
- **NDWI:** (B3 − B5)/(B3 + B5), after scaling. This is the final project's green/NIR definition, not the earlier green/SWIR experiment.
- **Albedo:** 0.356 blue + 0.130 red + 0.373 NIR + 0.085 SWIR1 + 0.072 SWIR2 − 0.0018, from script 36.
- **LST:** ST_B10 × 0.00341802 + 149 − 273.15 °C, from scripts 13/19. The L2 surface-temperature product already contains the retrieval corrections; no extra emissivity formula is applied. `PROCESSING_LEVEL=L2SP` is required.
- **Sentinel NDVI:** (B8 − B4)/(B8 + B4), from script 36. Multiplicative reflectance scale cancels.
- **Grid:** mean at 30 m, using the same canonical rectangles. Stage 3 explicitly fixes EPSG:32643 for deterministic sampling; script 36 allowed Earth Engine to infer projection. This can cause minor differences in boundary sampling.
- **Weather:** script 28's +/-90-minute window about Landsat UTC acquisition. Average hourly images, then average over its original `[77.45,12.80,77.75,13.15]` weather AOI at 10 km. Temperature and dewpoint convert K→°C; RH uses the original 17.625/243.04 expression; wind is magnitude of mean components; hourly solar accumulation divides J/m² by 1e6; ERA5 total cloud cover multiplies by 100. These are AOI weather values, not independently resolved 1 km measurements.

## Explicit validity differences

Landsat retains historical cloud/shadow bits 3/4 and also excludes fill bit 0. Sentinel excludes Stage 2's classes 3/8/9/10/11, plus no-data/defective classes 0/1. Script 36 did not exclude class 11; that stricter Stage 2 choice is retained and documented. Near-zero index denominators are masked, not assigned arbitrary ratios. No extra cloud dilation, saturation correction or replacement formula is silently applied.

Each source's valid fraction counts pixels with all requested bands valid, including uncovered parts of the cell as zero. A default 70% valid-pixel threshold is an **initial review policy**, not a scientifically calibrated guarantee. Values below it remain JSON null; no historical/neighbor/global-mean filling is used. Valid-cell values outside broad review ranges fail validation rather than being clipped. All cell IDs remain present even if imagery covers only part of the study.

## Interpretation and remaining gates

The detector's AOI cloud mean can omit masked/out-of-footprint pixels. Its `usable` label therefore does not guarantee full grid coverage. Stage 3 reports full-cell coverage separately. For Landsat, missing thermal emissivity data may reduce valid fractions even where optical imagery is clear.

The detector can choose Landsat and Sentinel scenes weeks apart. These are **independent scene summaries**, not temporally paired V5 inputs. `sensor_date_gap_days` makes this explicit. Before ML, match Sentinel within the historical +/-5-day rule and validate cloud/coverage, complete all 25 model features (including Dynamic World and historical weather windows), validate the model runtime, and decide an operational comparison window. No full V5 inference is possible from this artifact alone.

ERA5 absence is recorded as unavailable; future/different-day weather is never substituted. The current processor retrieves only the five script 28 overpass features. Daily/3-day/7-day meteorological features are deferred to the model-compatibility stage.

Inspect distributions, per-cell masks, temporal alignment, coverage and comparison with known historical scenes before any public latest-conditions view. Passing these tests means the artifact meets its declared schema, not that it is scientifically validated for operational decisions.

Official dataset references: [Landsat 8 L2](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2), [Sentinel-2 SR](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED).

Local tests: `python -m unittest discover -s automation -p test_latest.py -v`.
