# Bengaluru Heat Atlas

Static, responsive research website using the final analysis exports. Pages: overview, interactive map, connected hotspot rankings, methodology, and project information.

The `dist` directory is the deployable website. No backend or Earth Engine credentials are needed to use the atlas. Leaflet 1.9.4 is vendored locally. OpenStreetMap tiles and Google Fonts require an internet connection; the research grid and tables still work if the basemap is unavailable.

From the ISRO project directory:

```powershell
.\.venv\Scripts\python.exe website\prepare_data.py
.\.venv\Scripts\python.exe -m http.server 5173 --bind 127.0.0.1 --directory website\dist
```

Open http://127.0.0.1:5173/ in a browser. Use HTTP rather than double-clicking HTML files because the site loads JSON with fetch.

`website/data` contains the original research exports. `prepare_data.py` copies them unchanged and adds exact cluster membership and saved comparison results. Edit the shared shell in `dist/index.html`, then rerun the preparation script to update the other four entrypoints. Shared behavior and page content are in `dist/assets`.

See `RESEARCH_REVIEW.md` for the source review, interpretation details and earlier-script issues. The analysis scripts and model were not changed or rerun.

Two progressive WebMCP tools, `filter_heat_grid` and `inspect_heat_cell`, mirror the map's normal filtering and cell selection when the browser supports the API.

Mapping references: https://leafletjs.com/examples/quick-start/ and https://operations.osmfoundation.org/policies/tiles/
