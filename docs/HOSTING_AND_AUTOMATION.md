# Hosting and automated updates

Reviewed 14 September 2026. The atlas currently shows a fixed 2026 research snapshot. Its source-code deployment and satellite-data refresh are separate processes.

## Free hosting options

| Option | Fit for this project | Current limits / caveats |
|---|---|---|
| GitHub Pages | Recommended simple public static host, deployed from this repository | Free with public repositories; published site up to 1 GB; soft 100 GB monthly bandwidth limit |
| Cloudflare Pages | Alternative static CDN with GitHub integration | Free plan: 500 builds/month, 20,000 files/site, 25 MiB/file; static output here fits |
| Existing Sites URL | Current atlas deployment | Publication is separate from GitHub Pages; no continuous Earth Engine server runs inside the website |

GitHub Pages is configured by `.github/workflows/pages.yml`. Cloudflare could instead use `python website/prepare_data.py` as the build command and `website/dist` as output. No domain purchase is required for either provider's default URL. Recheck provider terms before relying on a free tier at higher traffic.

Sources: [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [Cloudflare limits](https://developers.cloudflare.com/pages/platform/limits/).

## Can it update every day?

A scheduler can **check every day**, but cannot guarantee new cloud-free imagery daily. Sentinel-2 nominal constellation revisit is 5 days. Landsat 8/9 together revisit roughly every 8 days; the existing trained pipeline uses Landsat 8 and adding Landsat 9 requires harmonization and validation. Clouds and processing availability can delay usable scenes. ERA5T initial data is about 5 days behind real time; Earth Engine ingestion may add further delay. Always read actual catalog timestamps rather than assuming today's date.

Sources: [Sentinel-2 mission](https://sentiwiki.copernicus.eu/web/s2-mission), [USGS Landsat constellation](https://www.usgs.gov/faqs/what-landsat-satellite-constellation), [ECMWF ERA5T](https://www.ecmwf.int/en/forecasts/dataset/era5t-era5-initial-release-data), [Earth Engine catalog status](https://developers.google.com/earth-engine/datasets/status).

## Low-cost architecture

1. GitHub Actions checks catalogs once daily. No continuously running VM is needed.
2. Earth Engine performs expensive spatial masking/reduction remotely, only for new eligible scenes.
3. Match Sentinel-2 and weather inputs to Landsat acquisition times. Require sufficient valid cell coverage and every V5 feature; never silently substitute today's weather for satellite overpass weather.
4. Run the saved, versioned model on the extracted cell features. Do not retrain every day.
5. Validate freshness, completeness, missingness, bounds, outliers, and model drift. Retain the last good published result if the update fails.
6. Export compact JSON and deploy the static website after successful validation. Show last checked, acquisition date, last successful analysis, model version, and cloud coverage separately.

Keep the original 2026 study accessible. A rolling monitoring layer must have a separately defined window (for example the latest 60–90 days). Do not blend new observations into a multi-year persistent score or recompute relative priority thresholds without labelling the changed comparison population. Validate monsoon and later-season generalization before presenting the original seasonal model as operational year-round monitoring.

## What is implemented now

- Website build/data validation and GitHub Pages publication workflow.
- `automation/check_catalog.py`: four lightweight catalog metadata queries, including Landsat 8, Sentinel-2, ERA5 and ERA5-Land.
- An opt-in daily workflow at 02:23 UTC / 07:53 IST, with manual dispatch and a 10-minute timeout.
- The check writes a downloadable Actions artifact. It does **not** update temperatures, mark the atlas live, or publish new predictions.

The catalog job is enabled on this repository and has a successful authenticated cloud run. Stage 2 AOI-based usable-scene detection is also working. [Stage 3](STAGE3_LATEST_FEATURES.md) adds manual, artifact-only processing and validation; latest ML inference and website publication remain unimplemented.

## Google setup (already completed for this repository)

Use an Earth Engine-enabled Cloud project with verified noncommercial eligibility. Configure GitHub OIDC Workload Identity Federation restricted to this exact repository and its main branch, with a service account allowed to use Earth Engine in that project. Prefer short-lived OIDC credentials; do not commit private keys or personal Earth Engine refresh tokens.

Set repository variables:

- `EE_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `ENABLE_CATALOG_CHECK=true` only after manual authentication succeeds

[Google authentication action](https://github.com/google-github-actions/auth) documents the identity setup. Run the catalog workflow manually and verify its artifact before enabling scheduled checks.

Verified noncommercial Earth Engine Community projects have a monthly allocation of 150 EECU-hours under the current tiers; annual eligibility verification is required. Repeated raster extraction can exhaust this allocation even when the scheduler itself is free. [Earth Engine noncommercial tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers).

GitHub standard hosted runners are free for public repositories, subject to service limits and acceptable use. Schedules can be delayed, and public-repository schedules are disabled after 60 days without repository activity. This is not a guaranteed daily SLA. [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

## Remaining engineering before automatic map refresh

Refactor scripts 28 and 36–41 into parameterized functions that accept dates, noninteractive credentials and output directories. Current script 37 merges weather from the historical V5 dataset, so it cannot obtain new-date weather as written. Define a versioned feature schema, handle late/reprocessed inputs, add masked-coverage tests and a last-good checkpoint, validate the frozen model on later periods, and implement an atomic release of website data. No credentials, live cloud setup, or verified operational refresh are implied by the supplied workflow.
