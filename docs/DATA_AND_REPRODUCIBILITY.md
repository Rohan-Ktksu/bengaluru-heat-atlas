# Data and reproducibility

The original scripts and saved `src/` datasets are preserved. Some earlier pilot modules and configurations predate the completed analysis. Use `website/RESEARCH_REVIEW.md` to distinguish the final pipeline from experiments.

- Landsat: https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2
- Sentinel-2: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- ERA5-Land: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY
- ERA5: https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_HOURLY
- Dynamic World: https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1
- OpenStreetMap attribution / licensing: https://www.openstreetmap.org/copyright

Consult each provider's terms before redistributing or adapting derived datasets. Locality labels were obtained using Nominatim, and are approximate labels at cell centres. All model outputs and scenario estimates require the limitations described on the website.

`website/data/` retains original research JSON. `website/prepare_data.py` copies it and generates compact transport data, exact cluster membership, score inputs, and saved model comparisons. It does not train, fetch satellite imagery, or alter research CSVs.

Large model files are provided as GitHub release assets; `MODEL_MANIFEST.json` records their SHA-256 checksums and sizes. Original model runtime versions are recorded in `research-environment.txt` from the local environment when available. This is a provenance record, not a guarantee that future installs will reproduce historical satellite processing bit-for-bit.

Credentials, local virtual environments, temporary preview archives, and nested Git databases are excluded from the public repository. No Google Cloud project credentials are required for the static site.
