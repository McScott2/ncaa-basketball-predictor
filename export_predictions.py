#!/usr/bin/env python3
"""
Export predictions to dashboard/predictions.json
Run after nba_predictor.py to update the live dashboard.
"""
import json, os
from datetime import datetime

NBA_LOG  = 'nba_predictions_log.json'
OUT_DIR  = 'dashboard'
OUT_FILE = f'{OUT_DIR}/predictions.json'

os.makedirs(OUT_DIR, exist_ok=True)

def load_log(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

nba_log = load_log(NBA_LOG)
today   = datetime.now().strftime('%Y-%m-%d')

# Today's predictions (only TODAY games, not TOMORROW)
nba_today = next((e for e in nba_log if e['date'] == today), None)
if nba_today:
    today_preds = [p for p in nba_today.get('predictions',[]) if p.get('day','TODAY') == 'TODAY']
    nba_today = {**nba_today, 'predictions': today_preds}

# History with results
nba_history = []
for e in nba_log:
    entry = {
        'date':        e['date'],
        'predictions': e.get('predictions',[]),
        'total':       len(e.get('predictions',[])),
    }
    if 'result' in e:
        entry['result'] = e['result']
    nba_history.append(entry)

# Sort history oldest first
nba_history.sort(key=lambda x: x['date'])

# Stats
results_days  = [e for e in nba_log if 'result' in e]
total_hits    = sum(e['result'].get('hits',0)  for e in results_days)
total_picks   = sum(e['result'].get('total',0) for e in results_days)
best_day      = max(results_days, key=lambda e: e['result'].get('pct',0), default=None)

output = {
    'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'stats': {
        'total_hits':   total_hits,
        'total_picks':  total_picks,
        'accuracy':     round(total_hits/total_picks*100, 1) if total_picks > 0 else 0,
        'best_day':     best_day['date'] if best_day else None,
        'best_pct':     best_day['result']['pct'] if best_day else None,
        'days_tracked': len(results_days),
    },
    'nba_today':   nba_today,
    'nba_history': nba_history,
}

with open(OUT_FILE, 'w') as f:
    json.dump(output, f, indent=2, default=str)

print(f"✅ Dashboard exported to {OUT_FILE}")
print(f"   Accuracy: {output['stats']['accuracy']}% ({total_hits}/{total_picks})")
print(f"   Today's games: {len(nba_today['predictions']) if nba_today else 0}")
print(f"   History days: {len(nba_history)}")
