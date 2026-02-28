#!/usr/bin/env python3
"""
Backfill historical results into nba_predictions_log.json
Calculates hits/total/pct from existing prediction data
"""
import json

log_file = 'nba_predictions_log.json'

with open(log_file) as f:
    log = json.load(f)

for entry in log:
    preds = entry.get('predictions', [])
    
    # Skip today's pending predictions
    if any(p.get('result') == 'pending' for p in preds):
        continue
    
    # Count hits and total from result field
    hits  = sum(1 for p in preds if p.get('result') == 'hit')
    total = sum(1 for p in preds if p.get('result') in ['hit', 'miss'])
    
    if total > 0:
        pct = round(hits / total * 100, 1)
        entry['result'] = {'hits': hits, 'total': total, 'pct': pct}
        print(f"  {entry['date']}: {hits}/{total} = {pct}%")
    else:
        print(f"  {entry['date']}: no results found")

with open(log_file, 'w') as f:
    json.dump(log, f, indent=2)

print()
print("✅ Historical results backfilled!")
print("Now run: python3 export_predictions.py")
