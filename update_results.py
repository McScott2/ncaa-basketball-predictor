"""
update_results.py
Run this after nba_predictor.py to backfill actual scores into the predictions log.
The dashboard reads from this log to show hit/miss history.
"""
import requests
import json
import os
from datetime import datetime, timedelta

LOG_FILE = 'nba_predictions_log.json'

def fetch_results_for_date(date_str):
    """Fetch ESPN NBA results for a given date YYYY-MM-DD"""
    date_clean = date_str.replace('-', '')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_clean}"
    try:
        r = requests.get(url, timeout=10)
        events = r.json().get('events', [])
        results = {}
        for e in events:
            comp = e['competitions'][0]
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            status = e['status']['type']['state']
            if status != 'post':
                continue
            h_score = int(home.get('score', 0) or 0)
            a_score = int(away.get('score', 0) or 0)
            home_name = home['team']['displayName']
            away_name = away['team']['displayName']
            total = h_score + a_score
            # Store by both team names for fuzzy matching
            key = f"{away_name} @ {home_name}"
            results[key] = {
                'home_team': home_name,
                'away_team': away_name,
                'home_score': h_score,
                'away_score': a_score,
                'total': total,
                'home_won': h_score > a_score
            }
        return results
    except Exception as ex:
        print(f"  ⚠ Could not fetch results for {date_str}: {ex}")
        return {}

def team_name_match(pred_name, result_name):
    """Fuzzy match team names"""
    pred_words = set(pred_name.lower().split())
    result_words = set(result_name.lower().split())
    return len(pred_words & result_words) >= 1

def find_result(pred, results):
    """Match a prediction to its result"""
    matchup = pred.get('matchup', '')
    for key, res in results.items():
        # Try exact match first
        if matchup.lower() in key.lower() or key.lower() in matchup.lower():
            return res
        # Try fuzzy — check if any team name words match
        parts = matchup.split(' @ ')
        if len(parts) == 2:
            away_pred, home_pred = parts[0].strip(), parts[1].strip()
            if team_name_match(away_pred, res['away_team']) and team_name_match(home_pred, res['home_team']):
                return res
    return None

def determine_result(pred, actual):
    """Determine if prediction was hit or miss"""
    ou_pick = pred.get('ou_pick', '').upper()
    ou_line = pred.get('ou_line', 0)
    actual_total = actual['total']

    if ou_pick == 'OVER':
        return 'hit' if actual_total > ou_line else 'miss'
    elif ou_pick == 'UNDER':
        return 'hit' if actual_total < ou_line else 'miss'
    else:
        # Win pick
        pick = pred.get('pick', '')
        if team_name_match(pick, actual['home_team']):
            return 'hit' if actual['home_won'] else 'miss'
        elif team_name_match(pick, actual['away_team']):
            return 'hit' if not actual['home_won'] else 'miss'
    return 'pending'

def update_log():
    if not os.path.exists(LOG_FILE):
        print(f"⚠ {LOG_FILE} not found. Run nba_predictor.py first.")
        return

    with open(LOG_FILE, 'r') as f:
        log = json.load(f)

    if not isinstance(log, list):
        log = log.get('entries', [])

    updated = 0
    for entry in log:
        date = entry.get('date')
        predictions = entry.get('predictions', [])
        if not predictions:
            continue

        # Check if already has results
        has_pending = any(p.get('result') == 'pending' or not p.get('result') for p in predictions)
        if not has_pending:
            continue

        print(f"\n📅 Checking results for {date}...")
        results = fetch_results_for_date(date)

        if not results:
            print(f"  No final games found for {date} (may still be in progress or future)")
            continue

        print(f"  Found {len(results)} completed games")

        for pred in predictions:
            if pred.get('result') and pred.get('result') != 'pending':
                continue  # already resolved

            actual = find_result(pred, results)
            if actual:
                res = determine_result(pred, actual)
                pred['result'] = res
                pred['actual_total'] = actual['total']
                pred['actual_home'] = actual['home_score']
                pred['actual_away'] = actual['away_score']
                icon = '✅' if res == 'hit' else '❌'
                print(f"  {icon} {pred.get('matchup')} → {res.upper()} (actual: {actual['total']})")
                updated += 1
            else:
                print(f"  ⚠ No match found for: {pred.get('matchup')}")

    # Save updated log
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

    print(f"\n✅ Updated {updated} predictions in {LOG_FILE}")
    print("📤 Now run: git add nba_predictions_log.json && git commit -m 'Update results' && git push")

if __name__ == '__main__':
    update_log()
