#!/usr/bin/env python3
"""
Export predictions log to dashboard/predictions.json
Run after nba_predictor.py to update the live dashboard
"""
import json, os
from datetime import datetime

NBA_LOG  = 'nba_predictions_log.json'
NCAA_LOG = 'ncaa_predictions_log.json'
OUT_DIR  = 'dashboard'
OUT_FILE = f'{OUT_DIR}/predictions.json'

os.makedirs(OUT_DIR, exist_ok=True)

def load_log(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

nba_log  = load_log(NBA_LOG)
ncaa_log = load_log(NCAA_LOG)

today = datetime.now().strftime('%Y-%m-%d')

# Today's predictions
nba_today  = next((e for e in nba_log  if e['date'] == today), None)
ncaa_today = next((e for e in ncaa_log if e['date'] == today), None)

# Full history with results
nba_history = [
    {'date': e['date'], 'result': e.get('result', {}), 'total': len(e.get('predictions', []))}
    for e in nba_log
]

# Overall stats
total_hits  = sum(e.get('result', {}).get('hits', 0)  for e in nba_log if 'result' in e)
total_picks = sum(e.get('result', {}).get('total', 0) for e in nba_log if 'result' in e)
best_day    = max((e for e in nba_log if 'result' in e), key=lambda e: e['result'].get('pct', 0), default=None)

output = {
    'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'stats': {
        'total_hits':   total_hits,
        'total_picks':  total_picks,
        'accuracy':     round(total_hits/total_picks*100, 1) if total_picks > 0 else 0,
        'best_day':     best_day['date'] if best_day else None,
        'best_pct':     best_day['result']['pct'] if best_day else None,
        'days_tracked': len([e for e in nba_log if 'result' in e]),
    },
    'nba_today':   nba_today,
    'ncaa_today':  ncaa_today,
    'nba_history': nba_history,
}

with open(OUT_FILE, 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"✅ Dashboard data exported to {OUT_FILE}")
print(f"   NBA accuracy: {output['stats']['accuracy']}% ({total_hits}/{total_picks})")
print(f"   Today's NBA games: {len(nba_today['predictions']) if nba_today else 0}")
print(f"   Today's NCAA games: {len(ncaa_today['predictions']) if ncaa_today else 0}")
