#!/usr/bin/env python3
"""
NCAA BASKETBALL ORACLE — Fixed Version
- Pulls ALL games via groups=50 (all D1)
- Dynamic O/U line per game
- Saves predictions to JSON daily
- Auto compares yesterday's predictions
- Same proven Four Factors model (10/13 day 1)
"""

import requests
import numpy as np
import json
import os
from datetime import datetime, timedelta

def get_team_stats(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/statistics"
    try:
        return requests.get(url, timeout=5).json()
    except:
        return {}

def parse_season_stats(data):
    result = {
        'PTS': 70,
        'FGM': 25, 'FGA': 60,
        '3PM': 7,  '3PA': 20,
        'FTA': 14, 'FTM': 11,
        'ORB': 7,  'DRB': 25,
        'TRB': 32, 'AST': 14,
        'TO': 12,  'STL': 6, 'BLK': 3,
        'FG_PCT': 0.45, 'FT_PCT': 0.72,
    }
    try:
        cats = data.get('results', {}).get('stats', {}).get('categories', [])
        for cat in cats:
            for stat in cat.get('stats', []):
                name = stat.get('name', '')
                val  = float(stat.get('value', 0))
                mapping = {
                    'avgPoints':                        'PTS',
                    'avgFieldGoalsMade':                'FGM',
                    'avgFieldGoalsAttempted':           'FGA',
                    'avgThreePointFieldGoalsMade':      '3PM',
                    'avgThreePointFieldGoalsAttempted': '3PA',
                    'avgFreeThrowsMade':                'FTM',
                    'avgFreeThrowsAttempted':           'FTA',
                    'avgOffensiveRebounds':             'ORB',
                    'avgDefensiveRebounds':             'DRB',
                    'avgRebounds':                      'TRB',
                    'avgAssists':                       'AST',
                    'avgTurnovers':                     'TO',
                    'avgSteals':                        'STL',
                    'avgBlocks':                        'BLK',
                    'fieldGoalPct':                     'FG_PCT',
                    'freeThrowPct':                     'FT_PCT',
                }
                if name in mapping and val > 0:
                    result[mapping[name]] = val
    except:
        pass

    # ── DERIVE DEFENSIVE STRENGTH FROM AVAILABLE STATS ──
    # ESPN doesn't provide avgPointsAllowed — derive it from defensive stats
    # Higher DRB, STL, BLK = better defense = lower points allowed
    # Higher opponent TO (our STL) = fewer opponent possessions
    # Base NCAA average allowed = 70 pts
    drb_factor  = (result['DRB'] - 25) * 0.3    # above avg DRB = better defense
    stl_factor  = (result['STL'] - 6)  * 0.8    # steals = turnovers forced
    blk_factor  = (result['BLK'] - 3)  * 0.5    # blocks = shots deterred
    to_factor   = (result['TO']  - 12) * 0.4    # our turnovers = opponent easy pts
    result['DEF_STR'] = 70 - drb_factor - stl_factor - blk_factor + to_factor

    return result

def predict(home, away):
    # Four Factors — proven model
    home_efg = (home['FGM'] + 0.5*home['3PM']) / max(home['FGA'], 1)
    away_efg = (away['FGM'] + 0.5*away['3PM']) / max(away['FGA'], 1)
    home_tov = home['TO'] / max(home['FGA'] + 0.44*home['FTA'] + home['TO'], 1)
    away_tov = away['TO'] / max(away['FGA'] + 0.44*away['FTA'] + away['TO'], 1)
    home_reb = home['ORB'] / max(home['ORB'] + away['DRB'], 1)
    away_reb = away['ORB'] / max(away['ORB'] + home['DRB'], 1)
    home_ftr = home['FTM'] / max(home['FGA'], 1)
    away_ftr = away['FTM'] / max(away['FGA'], 1)
    pts_edge = (home['PTS'] - away['PTS']) / max(away['PTS'], 1)

    score = (
        (home_efg - away_efg) * 0.40 +
        (away_tov - home_tov) * 0.25 +
        (home_reb - away_reb) * 0.20 +
        (home_ftr - away_ftr) * 0.15 +
        pts_edge * 0.10 +
        0.03
    )
    wp = 1 / (1 + np.exp(-score * 15))

    # ── SCORE ESTIMATES using derived defensive strength ──
    # DEF_STR already computed in parse_season_stats from DRB, STL, BLK, TO
    h_est = home['PTS'] * 0.55 + (140 - away['DEF_STR']) * 0.45
    a_est = away['PTS'] * 0.55 + (140 - home['DEF_STR']) * 0.45
    total = h_est + a_est

    # ── DYNAMIC O/U LINE ──
    ou_line = round((home['PTS'] + away['PTS'] + home['DEF_STR'] + away['DEF_STR']) / 2, 1)

    return wp, total, h_est, a_est, ou_line

def get_all_games():
    """Pull all D1 games — not just ESPN featured games"""
    all_events = []
    seen = set()
    urls = [
        "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?limit=200&groups=50",
        "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?limit=200&groups=100",
    ]
    for url in urls:
        try:
            events = requests.get(url, timeout=10).json().get('events', [])
            for ev in events:
                eid = ev.get('id')
                if eid and eid not in seen:
                    seen.add(eid)
                    all_events.append(ev)
        except:
            continue
    if not all_events:
        try:
            all_events = requests.get(
                "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard",
                timeout=10).json().get('events', [])
        except:
            pass
    return all_events

def save_predictions(predictions):
    log_file = 'ncaa_predictions_log.json'
    log = []
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log = json.load(f)
    date_str = datetime.now().strftime('%Y-%m-%d')
    log = [e for e in log if e['date'] != date_str]
    log.append({'date': date_str, 'predictions': predictions,
                'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M')})
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o) if isinstance(o, np.floating) else int(o) if isinstance(o, np.integer) else str(o))
    print(f"\n  💾 {len(predictions)} predictions saved to {log_file}")

def auto_compare():
    log_file = 'ncaa_predictions_log.json'
    if not os.path.exists(log_file):
        return
    with open(log_file, 'r') as f:
        log = json.load(f)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yentry    = next((e for e in log if e['date'] == yesterday), None)
    if not yentry:
        return

    print("\n" + "="*65)
    print(f"  🔍  AUTO COMPARE — {yesterday} vs ACTUAL")
    print("="*65)

    ystr = yesterday.replace('-', '')
    try:
        events = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?limit=200&groups=50&dates={ystr}",
            timeout=10).json().get('events', [])
    except:
        print("  ⚠️  Could not fetch yesterday's results")
        return

    hits = 0; misses = 0

    for pred in yentry['predictions']:
        parts = pred['matchup'].split(' at ')
        if len(parts) != 2: continue
        away_n, home_n = parts[0], parts[1]
        away_last = away_n.split()[-1].lower()
        home_last = home_n.split()[-1].lower()

        result = None
        for ev in events:
            comp = ev['competitions'][0]
            h = comp['competitors'][0]['team']['displayName'].lower()
            a = comp['competitors'][1]['team']['displayName'].lower()
            if (away_last in a or away_last in h) and (home_last in h or home_last in a):
                h_score = int(comp['competitors'][0].get('score') or 0)
                a_score = int(comp['competitors'][1].get('score') or 0)
                status  = ev['status']['type']['description']
                result  = {
                    'total': h_score+a_score,
                    'h_score': h_score, 'a_score': a_score,
                    'status': status,
                    'home': comp['competitors'][0]['team']['displayName'],
                    'away': comp['competitors'][1]['team']['displayName']
                }
                break

        if not result or result['status'] not in ['Final', 'Final/OT']:
            continue

        hit  = (pred['ou']=='OVER'  and result['total'] > pred['ou_line']) or \
               (pred['ou']=='UNDER' and result['total'] < pred['ou_line'])
        icon = "✅" if hit else "❌"
        if hit: hits += 1
        else:   misses += 1

        print(f"  {icon} {result['away'].split()[-1]:<14} @ {result['home'].split()[-1]:<16} {result['a_score']}-{result['h_score']} (Total: {result['total']})")
        print(f"     Pred: {pred['ou']} {pred['ou_line']:<8} | Pick: {pred['pick'].split()[-1]:<18} | {pred['conf']*100:.1f}%")

    total = hits + misses
    if total > 0:
        pct = hits/total*100
        print(f"\n  📊  {yesterday}: {hits}/{total} = {pct:.1f}%")
        print(f"  {'🔥 STRONG!' if pct>=70 else '✅ DECENT' if pct>=55 else '⚠️  NEEDS TUNING'}")
        with open(log_file, 'r') as f: log = json.load(f)
        for e in log:
            if e['date'] == yesterday:
                e['result'] = {'hits': hits, 'total': total, 'pct': round(pct,1)}
        with open(log_file, 'w') as f: json.dump(log, f, indent=2)
        print(f"  💾 Result saved")
    print("="*65)

def main():
    print("\n" + "="*65)
    print("🏀  NCAA BASKETBALL — GOD MODE PREDICTIONS")
    print(f"📅  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}")
    print("="*65)

    print("\n  Fetching all NCAA games...", end='', flush=True)
    events    = get_all_games()
    scheduled = [e for e in events if e.get('status',{}).get('type',{}).get('state')=='pre']
    print(f" ✓ ({len(scheduled)} games found)")

    if not scheduled:
        print("\n  ⚠️  No scheduled games found.")
        auto_compare()
        return

    predictions = []
    god_picks   = []

    for event in scheduled:
        try:
            comp      = event['competitions'][0]
            home_c    = comp['competitors'][0]
            away_c    = comp['competitors'][1]
            home_name = home_c['team']['displayName']
            away_name = away_c['team']['displayName']
            status    = event['status']['type']['description']

            try:
                t      = datetime.strptime(event['date'],'%Y-%m-%dT%H:%MZ') + timedelta(hours=1)
                tipoff = t.strftime('%I:%M %p WAT')
            except:
                tipoff = "TBD"

            home_data = parse_season_stats(get_team_stats(home_c['team']['id']))
            away_data = parse_season_stats(get_team_stats(away_c['team']['id']))

            wp, total, h_est, a_est, ou_line = predict(home_data, away_data)
            fav    = home_name if wp > 0.5 else away_name
            conf   = wp if wp > 0.5 else 1 - wp
            ou     = 'OVER' if total > ou_line else 'UNDER'
            fh_line = round(ou_line * 0.475, 1)
            fh_ou   = 'OVER' if total*0.475 > fh_line else 'UNDER'

            print(f"\n📍 {away_name} at {home_name}  [{status}]")
            print(f"   ⏰ Tip-off:     {tipoff}")
            print(f"   🏆 Pick:        {fav}  ({conf:.1%} confidence)")
            print(f"   📊 Full Game:   Est. {total:.0f} pts  |  {ou} {ou_line}")
            print(f"   🎯 First Half:  Est. {total*0.475:.0f} pts  |  {fh_ou} {fh_line}")
            print(f"   🏠 {home_name}: Est. {h_est:.0f} pts")
            print(f"   ✈️  {away_name}: Est. {a_est:.0f} pts")
            if conf >= 0.70:
                print(f"   🔥 GOD PICK!")

            entry = {
                'matchup': f"{away_name} at {home_name}",
                'pick': fav, 'conf': conf,
                'ou': ou, 'ou_line': ou_line,
                'total': round(total,1),
                'fh_ou': fh_ou, 'fh_line': fh_line,
                'tipoff': tipoff, 'god': conf >= 0.70
            }
            predictions.append(entry)
            if conf >= 0.70:
                god_picks.append(entry)

        except:
            continue

    if predictions:
        overs = [p for p in predictions if p['ou']=='OVER']
        avg_c = sum(p['conf'] for p in predictions)/len(predictions)
        print("\n" + "="*65)
        print("  📊  SUMMARY")
        print("="*65)
        print(f"  Total games    : {len(predictions)}")
        print(f"  Avg confidence : {avg_c*100:.1f}%")
        print(f"  Overs / Unders : {len(overs)} / {len(predictions)-len(overs)}")
        print(f"  God picks ≥70% : {len(god_picks)}")
        if god_picks:
            print(f"\n  🔥 GOD PICKS:")
            for g in god_picks:
                print(f"     ✅ {g['pick']}")
                print(f"        {g['ou']} {g['ou_line']}  |  {g['conf']*100:.1f}%  |  {g['tipoff']}")
        print("\n  ⚠️  Max 5 picks. 100 naira stake.")
        print("="*65)
        save_predictions(predictions)

    auto_compare()

if __name__ == '__main__':
    main()