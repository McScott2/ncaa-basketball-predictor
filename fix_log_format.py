"""
fix_log_format.py
One-time script to convert nba_predictions_log.json into the format
the dashboard expects, then backfill all available results.
"""
import requests
import json
import os
from datetime import datetime

LOG_FILE = 'nba_predictions_log.json'

# Known results from our tracking history
KNOWN_RESULTS = {
    "2026-02-22": [
        {"matchup": "Cleveland Cavaliers @ Oklahoma City Thunder", "ou_pick": "OVER", "ou_line": 224.0, "estimated": 228, "confidence": 65.0, "actual_away": 113, "actual_home": 121, "actual_total": 234, "result": "hit"},
        {"matchup": "Brooklyn Nets @ Atlanta Hawks", "ou_pick": "OVER", "ou_line": 218.0, "estimated": 224, "confidence": 58.0, "actual_away": 104, "actual_home": 115, "actual_total": 219, "result": "hit"},
        {"matchup": "Toronto Raptors @ Milwaukee Bucks", "ou_pick": "OVER", "ou_line": 220.0, "estimated": 226, "confidence": 70.0, "actual_away": 122, "actual_home": 94, "actual_total": 216, "result": "miss"},
        {"matchup": "Denver Nuggets @ Golden State Warriors", "ou_pick": "OVER", "ou_line": 226.0, "estimated": 231, "confidence": 63.0, "actual_away": 117, "actual_home": 128, "actual_total": 245, "result": "hit"},
        {"matchup": "Dallas Mavericks @ Indiana Pacers", "ou_pick": "OVER", "ou_line": 220.0, "estimated": 225, "confidence": 68.0, "actual_away": 134, "actual_home": 130, "actual_total": 264, "result": "hit"},
        {"matchup": "Charlotte Hornets @ Washington Wizards", "ou_pick": "OVER", "ou_line": 225.0, "estimated": 226, "confidence": 55.0, "actual_away": 129, "actual_home": 112, "actual_total": 241, "result": "hit"},
        {"matchup": "Boston Celtics @ Los Angeles Lakers", "ou_pick": "UNDER", "ou_line": 225.0, "estimated": 218, "confidence": 78.0, "actual_away": 111, "actual_home": 89, "actual_total": 200, "result": "hit"},
        {"matchup": "Philadelphia 76ers @ Minnesota Timberwolves", "ou_pick": "OVER", "ou_line": 228.0, "estimated": 243, "confidence": 72.0, "actual_away": 135, "actual_home": 108, "actual_total": 243, "result": "hit"},
        {"matchup": "New York Knicks @ Chicago Bulls", "ou_pick": "UNDER", "ou_line": 215.0, "estimated": 208, "confidence": 62.0, "actual_away": 105, "actual_home": 99, "actual_total": 204, "result": "hit"},
        {"matchup": "Portland Trail Blazers @ Phoenix Suns", "ou_pick": "UNDER", "ou_line": 210.0, "estimated": 198, "confidence": 58.0, "actual_away": 92, "actual_home": 77, "actual_total": 169, "result": "hit"},
        {"matchup": "Orlando Magic @ LA Clippers", "ou_pick": "UNDER", "ou_line": 225.0, "estimated": 214, "confidence": 55.0, "actual_away": 111, "actual_home": 109, "actual_total": 220, "result": "hit"},
    ],
    "2026-02-24": [
        {"matchup": "Cleveland Cavaliers @ Oklahoma City Thunder", "ou_pick": "OVER", "ou_line": 225.7, "estimated": 229, "confidence": 62.7, "actual_away": 113, "actual_home": 121, "actual_total": 234, "result": "hit"},
        {"matchup": "Toronto Raptors @ San Antonio Spurs", "ou_pick": "OVER", "ou_line": 227.4, "estimated": 233, "confidence": 62.2, "actual_away": 110, "actual_home": 107, "actual_total": 217, "result": "miss"},
        {"matchup": "Memphis Grizzlies @ Golden State Warriors", "ou_pick": "OVER", "ou_line": 224.9, "estimated": 226, "confidence": 67.0, "actual_away": 112, "actual_home": 133, "actual_total": 245, "result": "hit"},
        {"matchup": "Sacramento Kings @ Houston Rockets", "ou_pick": "UNDER", "ou_line": 226.3, "estimated": 204, "confidence": 90.9, "actual_away": 97, "actual_home": 128, "actual_total": 225, "result": "hit", "god": True},
        {"matchup": "Cleveland Cavaliers @ Milwaukee Bucks", "ou_pick": "OVER", "ou_line": 224.5, "estimated": 226, "confidence": 83.3, "actual_away": 116, "actual_home": 118, "actual_total": 234, "result": "hit"},
        {"matchup": "Boston Celtics @ Denver Nuggets", "ou_pick": "OVER", "ou_line": 228.2, "estimated": 233, "confidence": 54.4, "actual_away": 84, "actual_home": 103, "actual_total": 187, "result": "miss"},
    ],
    "2026-02-25": [
        {"matchup": "Philadelphia 76ers @ Indiana Pacers", "ou_pick": "OVER", "ou_line": 109.5, "estimated": 236, "confidence": 79.3, "actual_away": 135, "actual_home": 114, "actual_total": 249, "result": "hit"},
        {"matchup": "Washington Wizards @ Atlanta Hawks", "ou_pick": "OVER", "ou_line": 225.5, "estimated": 234, "confidence": 89.5, "actual_away": 98, "actual_home": 119, "actual_total": 217, "result": "miss", "god": True},
        {"matchup": "Dallas Mavericks @ Brooklyn Nets", "ou_pick": "UNDER", "ou_line": 239.5, "estimated": 223, "confidence": 62.4, "actual_away": 123, "actual_home": 114, "actual_total": 237, "result": "hit"},
        {"matchup": "Oklahoma City Thunder @ Toronto Raptors", "ou_pick": "OVER", "ou_line": 106.5, "estimated": 233, "confidence": 76.0, "actual_away": 116, "actual_home": 107, "actual_total": 223, "result": "hit"},
        {"matchup": "New York Knicks @ Cleveland Cavaliers", "ou_pick": "OVER", "ou_line": 219.5, "estimated": 224, "confidence": 65.9, "actual_away": 94, "actual_home": 109, "actual_total": 203, "result": "miss"},
        {"matchup": "Charlotte Hornets @ Chicago Bulls", "ou_pick": "UNDER", "ou_line": 246.5, "estimated": 227, "confidence": 77.5, "actual_away": 131, "actual_home": 99, "actual_total": 230, "result": "hit"},
        {"matchup": "Miami Heat @ Milwaukee Bucks", "ou_pick": "OVER", "ou_line": 213.5, "estimated": 225, "confidence": 58.2, "actual_away": 117, "actual_home": 128, "actual_total": 245, "result": "hit"},
        {"matchup": "Golden State Warriors @ New Orleans Pelicans", "ou_pick": "UNDER", "ou_line": 240.5, "estimated": 226, "confidence": 52.5, "actual_away": 109, "actual_home": 113, "actual_total": 222, "result": "hit"},
        {"matchup": "Boston Celtics @ Phoenix Suns", "ou_pick": "OVER", "ou_line": 97.5, "estimated": 228, "confidence": 54.4, "actual_away": 97, "actual_home": 81, "actual_total": 178, "result": "miss"},
        {"matchup": "Minnesota Timberwolves @ Portland Trail Blazers", "ou_pick": "UNDER", "ou_line": 249.5, "estimated": 220, "confidence": 83.2, "actual_away": 124, "actual_home": 121, "actual_total": 245, "result": "hit"},
        {"matchup": "Orlando Magic @ Los Angeles Lakers", "ou_pick": "UNDER", "ou_line": 243.5, "estimated": 222, "confidence": 76.5, "actual_away": 110, "actual_home": 109, "actual_total": 219, "result": "hit"},
    ],
    "2026-02-26": [
        {"matchup": "Charlotte Hornets @ Indiana Pacers", "ou_pick": "OVER", "ou_line": 229.5, "estimated": 230, "confidence": 79.3, "actual_away": 133, "actual_home": 109, "actual_total": 242, "result": "hit"},
        {"matchup": "Miami Heat @ Philadelphia 76ers", "ou_pick": "UNDER", "ou_line": 239.5, "estimated": 226, "confidence": 62.4, "actual_away": 117, "actual_home": 124, "actual_total": 241, "result": "miss"},
        {"matchup": "Washington Wizards @ Atlanta Hawks", "ou_pick": "UNDER", "ou_line": 237.5, "estimated": 219, "confidence": 89.5, "actual_away": 96, "actual_home": 126, "actual_total": 222, "result": "hit", "god": True},
        {"matchup": "San Antonio Spurs @ Brooklyn Nets", "ou_pick": "OVER", "ou_line": 224.5, "estimated": 232, "confidence": 95.0, "actual_away": 126, "actual_home": 110, "actual_total": 236, "result": "hit", "god": True},
        {"matchup": "Houston Rockets @ Orlando Magic", "ou_pick": "OVER", "ou_line": 215.5, "estimated": 221, "confidence": 60.5, "actual_away": 113, "actual_home": 108, "actual_total": 221, "result": "hit"},
        {"matchup": "Portland Trail Blazers @ Chicago Bulls", "ou_pick": "UNDER", "ou_line": 234.5, "estimated": 218, "confidence": 77.5, "actual_away": 121, "actual_home": 112, "actual_total": 233, "result": "hit"},
        {"matchup": "Sacramento Kings @ Dallas Mavericks", "ou_pick": "UNDER", "ou_line": 236.5, "estimated": 215, "confidence": 76.0, "actual_away": 130, "actual_home": 121, "actual_total": 251, "result": "miss"},
        {"matchup": "Los Angeles Lakers @ Phoenix Suns", "ou_pick": "OVER", "ou_line": 220.5, "estimated": 224, "confidence": 54.5, "actual_away": 110, "actual_home": 113, "actual_total": 223, "result": "hit"},
        {"matchup": "New Orleans Pelicans @ Utah Jazz", "ou_pick": "UNDER", "ou_line": 242.5, "estimated": 215, "confidence": 52.0, "actual_away": 129, "actual_home": 118, "actual_total": 247, "result": "miss"},
        {"matchup": "Minnesota Timberwolves @ LA Clippers", "ou_pick": "UNDER", "ou_line": 225.5, "estimated": 210, "confidence": 59.7, "actual_away": 94, "actual_home": 88, "actual_total": 182, "result": "hit"},
    ],
    "2026-02-27": [
        {"matchup": "Cleveland Cavaliers @ Detroit Pistons", "ou_pick": "OVER", "ou_line": 227.5, "estimated": 229, "confidence": 53.9, "actual_away": 119, "actual_home": 122, "actual_total": 241, "result": "hit"},
        {"matchup": "Brooklyn Nets @ Boston Celtics", "ou_pick": "OVER", "ou_line": 209.5, "estimated": 227, "confidence": 95.0, "actual_away": 111, "actual_home": 148, "actual_total": 259, "result": "hit", "god": True},
        {"matchup": "New York Knicks @ Milwaukee Bucks", "ou_pick": "OVER", "ou_line": 218.5, "estimated": 224, "confidence": 65.9, "actual_away": 127, "actual_home": 98, "actual_total": 225, "result": "hit"},
        {"matchup": "Memphis Grizzlies @ Dallas Mavericks", "ou_pick": "UNDER", "ou_line": 238.5, "estimated": 217, "confidence": 71.3, "actual_away": 124, "actual_home": 105, "actual_total": 229, "result": "hit"},
        {"matchup": "Denver Nuggets @ Oklahoma City Thunder", "ou_pick": "OVER", "ou_line": 233.5, "estimated": 234, "confidence": 76.0, "actual_away": 121, "actual_home": 127, "actual_total": 248, "result": "hit"},
    ],
}

def rebuild_log():
    today = datetime.now().strftime('%Y-%m-%d')

    # Load existing log if present
    existing = {}
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                raw = json.load(f)
            entries = raw if isinstance(raw, list) else raw.get('entries', [])
            for entry in entries:
                d = entry.get('date')
                if d:
                    existing[d] = entry
        except:
            pass

    # Merge known results with existing log
    all_dates = set(list(KNOWN_RESULTS.keys()) + list(existing.keys()))
    new_log = []

    for date in sorted(all_dates, reverse=True):
        if date in KNOWN_RESULTS:
            # Use our verified data
            preds = KNOWN_RESULTS[date]
            for p in preds:
                if 'god' not in p:
                    p['god'] = False
                if 'result' not in p:
                    p['result'] = 'pending'
            new_log.append({'date': date, 'predictions': preds})
        elif date in existing:
            # Keep existing entry — mark all results as pending if no result field
            entry = existing[date]
            preds = entry.get('predictions', [])
            for p in preds:
                if 'result' not in p or p['result'] is None:
                    p['result'] = 'pending'
                if 'god' not in p:
                    p['god'] = p.get('confidence', 0) >= 70
            new_log.append({'date': date, 'predictions': preds})

    with open(LOG_FILE, 'w') as f:
        json.dump(new_log, f, indent=2)

    total_picks = sum(len(e['predictions']) for e in new_log)
    total_hits = sum(1 for e in new_log for p in e['predictions'] if p.get('result') == 'hit')
    print(f"\n✅ Log rebuilt with {len(new_log)} days, {total_picks} predictions")
    print(f"📊 Overall accuracy: {total_hits}/{total_picks} = {round(total_hits/total_picks*100) if total_picks else 0}%")
    print(f"\n📤 Now push to GitHub:")
    print(f"   git add {LOG_FILE} && git commit -m 'Backfill results history' && git push")

if __name__ == '__main__':
    rebuild_log()
