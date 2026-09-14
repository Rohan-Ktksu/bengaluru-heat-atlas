# Bengaluru Heat Atlas

Bengaluru surface-heat research by Rohan: satellite-data preparation, V1–V5 model experiments, a 1 km planning grid, hotspot clustering, and an interactive website.

- [Interactive atlas](https://bengaluru-heat-atlas-rohan.mgorumutchu.chatgpt.site)
- [GitHub Pages](https://rohan-ktksu.github.io/bengaluru-heat-atlas/)
- [Model downloads](https://github.com/Rohan-Ktksu/bengaluru-heat-atlas/releases)

The current website is a **research snapshot from 27 January–3 May 2026**, not live monitoring. It contains 1,320 cells and 73 connected hotspot clusters. Displayed temperatures are model-derived land surface temperatures, not air temperatures. Cooling and tree counts are scenarios, not prescriptions.

## Project contents

| Folder | Contents |
|---|---|
| `scripts/` | Original numbered research scripts 00–50 and `verify.py` |
| `src/` | Saved feature datasets, predictions, planning tables, HTML maps, final results, and earlier reusable Python modules |
| `configs/` | Earlier pilot configuration; does not describe the final study |
| `output/` | Saved research outputs |
| `website/` | Authored website, original JSON exports, preparation script, and research review |
| `automation/` | Catalog checks, usable-scene detection and artifact-only latest feature processing |
| `.github/workflows/` | Website publication, daily catalog/detection checks and manual Stage 3 processing |
| `docs/` | Hosting, automation design, provenance, and reproducibility notes |

## Run the website locally

Python 3.11+ and Node.js are sufficient for website preparation and validation. No Earth Engine account is needed to view saved results.

```sh
python website/prepare_data.py
python website/validate_site.py
python -m http.server 5173 --directory website/dist
```

Open http://localhost:5173. On mobile, tap a grid cell or result card for evidence and use **Back to map** to return. More filters exposes reliability and source options.

## Research environment

```sh
python -m venv .venv
# Activate the environment for your operating system, then:
python -m pip install -r requirements.txt
```

Earth Engine scripts require your own registered, eligible Google Cloud project and authentication. Several scripts prompt for its project ID and use fixed historical dates. **Do not run all numbered scripts blindly:** some overwrite prior outputs, and earlier experiments contain issues documented in [the script review](website/RESEARCH_REVIEW.md). The website preparation script only reads saved analysis.

Large serialized models should be stored as release assets rather than ordinary Git history; Stage 3 does not download or load them. Check the release assets before assuming a model is available. Restore them to `models/` using their original filenames. Download only trusted model files: Python pickle/joblib loading can execute code. Model generation is in scripts 17 and 30; exact reproduction also depends on package versions, satellite catalog revisions, and the original input datasets.

## Publish and update

All automated catalog, scene and feature checks use data **through the end of the previous calendar month (UTC)**. A September run uses data through August 31; an October run uses data through September 30. Older unprocessed scenes remain eligible: this is a cutoff, not a monthly average or a last-month-only filter.

For a monthly manual check, open Actions → **Pair scenes and prepare V5 inputs (review only)** → **Run workflow**, select `main`, and leave `validation_date` empty. Start a new run to use the latest code. The artifact records `data_through`; cloud cover, coverage and compatible dates still determine whether usable inputs exist. Full ancillary windows must also finish before the cutoff, so late-month scenes needing subsequent weather or land-cover data can be deferred. Prediction review and website publication remain separate steps.

The GitHub Pages workflow validates and publishes `website/dist` on pushes to `main`. Configure repository Settings → Pages → Source → GitHub Actions. The Sites copy uses its own publication flow; a GitHub push updates GitHub Pages, not the Sites copy.

[Hosting and automated updates](docs/HOSTING_AND_AUTOMATION.md) explains free options and the remaining steps for operational monitoring. Catalog checks and AOI-based usable-scene detection are configured and have successful cloud runs. [Stage 3 feature processing](docs/STAGE3_LATEST_FEATURES.md) and [paired V5 inputs / review inference](docs/STAGE4_PAIRED_INPUTS.md) are tested and artifact-only. A historical replay produced complete inputs and predictions for 1,268 cells; the current new-date check found no compatible satellite pair. The research snapshot is never relabeled as current.

## Provenance and use

Inputs include USGS Landsat, Copernicus Sentinel-2, ECMWF ERA5/ERA5-Land, Dynamic World, SRTM, and JRC Global Surface Water via Google Earth Engine. Basemap/geocoding: OpenStreetMap contributors. Leaflet is bundled with its license. See [data provenance](docs/DATA_AND_REPRODUCIBILITY.md).

This is a student research project, not an official ISRO product. No blanket software or dataset license has been chosen for original work; public availability alone does not grant unrestricted reuse. Third-party licenses continue to apply.
