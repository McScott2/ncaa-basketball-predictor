import json, os
from datetime import datetime

log_file = 'nba_predictions_log.json'
out_file = 'dashboard/predictions.json'

os.makedirs('dashboard', exist_ok=True)

if os.path.exists(log_file):
    with open(log_file) as f:
        log = json.load(f)
    
    # Get today's predictions
    today = datetime.now().strftime('%Y-%m-%d')
    today_entry = next((e for e in log if e['date'] == today), None)
    
    # Get full history
    history = [{'date': e['date'], 'result': e.get('result', {})} for e in log if 'result' in e]
    
    output = {
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'today': today_entry,
        'history': history
    }
    
    with open(out_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Exported to {out_file}")
else:
    print("⚠️ No predictions log found — run nba_predictor.py first")
