"""Offline integrity checks for the published research snapshot."""
import csv
import json
import math
import re
import subprocess
from pathlib import Path

site = Path(__file__).resolve().parent
dist = site / 'dist'
grid = json.loads((dist / 'data/grid_data.json').read_text(encoding='utf-8'))
compact = json.loads((dist / 'data/grid_data.min.json').read_text(encoding='utf-8'))
assert grid == compact, 'Compact data changed research values'
ids = {r['Grid_ID'] for r in grid}
assert len(grid) == len(ids) == 1320
indicators = json.loads((dist / 'data/cell_indicators.json').read_text())
assert set(indicators) == ids
weights = {'Heat_Intensity_Score':30, 'Hot_Frequency_Score':25,
           'Very_Hot_Frequency_Score':10, 'Low_Tree_Score':15,
           'Built_Score':10, 'Water_Distance_Score':5, 'Low_Albedo_Score':5}
with (site.parent / 'src/bengaluru_hybrid_heat_grid.csv').open(encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        values = indicators[row['Grid_ID']]
        assert all(v is not None and math.isfinite(v) for v in values.values())
        assert abs(sum(values[k]*w for k,w in weights.items()) - float(row['Hybrid_Heat_Score'])) < 1e-8
for source in (site / 'data').glob('*.json'):
    assert source.read_bytes() == (dist / 'data' / source.name).read_bytes()
for route in ['index', 'map', 'hotspots', 'methodology', 'about']:
    html = (dist / (route+'.html')).read_text(encoding='utf-8')
    for ref in re.findall(r'(?:href|src)="([^"?#]+)', html):
        if not re.match(r'\w+:|//', ref):
            assert (dist / ref).exists(), ref
for name in ['app.js', 'content.js']:
    subprocess.run(['node', '--check', str(dist / 'assets' / name)], check=True)
print('Validated five routes, research data, 1,320 cell joins and score totals.')
