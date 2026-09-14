"""Copy final exports into the website; never rerun or change the analysis."""
import csv
import json
from pathlib import Path
import shutil

website = Path(__file__).resolve().parent
project = website.parent
target = website / 'dist' / 'data'
target.mkdir(parents=True, exist_ok=True)
for source in (website / 'data').glob('*.json'):
    json.loads(source.read_text(encoding='utf-8'))
    shutil.copy2(source, target / source.name)

# Compact transport copy retains every original value.
(target / 'grid_data.min.json').write_text(json.dumps(json.loads(
    (target / 'grid_data.json').read_text(encoding='utf-8')),
    separators=(',', ':'), ensure_ascii=False), encoding='utf-8')

def read_csv(name):
    with (project / 'src' / name).open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))

# This join preserves script 44's actual cluster membership. Locality labels
# alone cannot identify the extent of a connected cluster.
membership = {r['Grid_ID']: int(r['Cluster_ID']) for r in read_csv('bengaluru_hotspot_cluster_cells.csv')}
(target / 'cluster_membership.json').write_text(json.dumps(membership), encoding='utf-8')
metrics = {
    'models': read_csv('v3_v4_v5_model_comparison.csv'),
    'dates': read_csv('v3_v4_v5_date_comparison.csv'),
    'features': read_csv('v5_feature_importance.csv'),
}
(target / 'model_metrics.json').write_text(json.dumps(metrics), encoding='utf-8')
print('Prepared six original exports, exact cluster membership, and saved model metrics.')

# Keep supplementary indicators separate from the unchanged public exports.
indicator_fields = ['Final_L_NDVI', 'Final_S2_NDVI', 'Median_NDBI',
    'Median_NDWI', 'Final_Albedo', 'Final_Distance_To_Water', 'Elevation',
    'Heat_Intensity_Score', 'Hot_Frequency_Score', 'Very_Hot_Frequency_Score',
    'Low_Tree_Score', 'Built_Score', 'Water_Distance_Score', 'Low_Albedo_Score']
indicators = {r['Grid_ID']: {k: float(r[k]) if r[k] else None
    for k in indicator_fields} for r in read_csv('bengaluru_hybrid_heat_grid.csv')}
(target / 'cell_indicators.json').write_text(
    json.dumps(indicators, allow_nan=False, separators=(',', ':')), encoding='utf-8')

shell = (website / 'dist' / 'index.html').read_text(encoding='utf-8')
for name, title, headline in [
    ('map', 'Explore map', 'Explore the heat grid.'),
    ('hotspots', 'Hotspot clusters', 'The places to prioritize.'),
    ('methodology', 'Methodology', 'Understand the evidence.'),
    ('about', 'About the project', 'Understanding Bengaluru’s heat.'),
]:
    html = shell.replace('Bengaluru Heat Atlas · Cooling priorities', f'Bengaluru Heat Atlas · {title}')
    html = html.replace('Cooling priorities, mapped.', headline)
    (website / 'dist' / f'{name}.html').write_text(html, encoding='utf-8')
print('Prepared all five page entrypoints.')
