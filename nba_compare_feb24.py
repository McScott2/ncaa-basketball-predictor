#!/usr/bin/env python3
"""
NBA Results Comparison — Feb 24 2026
Compares actual results against our slip picks
"""

import requests
from datetime import datetime

# ── YOUR SLIP PICKS (from SportyBet screenshot) ──
SLIP = [
    # (away, home, our_pick, pick_type, our_line, over_under)
    ("Philadelphia 76ers",  "Indiana Pacers",           "Indiana Pacers",   "team_total", 109.5, "OVER"),
    ("Washington Wizards",  "Atlanta Hawks",             "Atlanta Hawks",    "full_game",  225.5, "OVER"),
    ("Dallas Mavericks",    "Brooklyn Nets",             "Brooklyn Nets",    "full_game",  239.5, "UNDER"),
    ("Oklahoma City Thunder","Toronto Raptors",          "OKC Thunder",      "team_total", 106.5, "OVER"),
    ("New York Knicks",     "Cleveland Cavaliers",       "Cleveland Cavaliers","full_game",219.5, "OVER"),
    ("Charlotte Hornets",   "Chicago Bulls",             "Chicago Bulls",    "full_game",  246.5, "UNDER"),
    ("Miami Heat",          "Milwaukee Bucks",           "Miami Heat",       "full_game",  213.5, "OVER"),
    ("Golden State Warriors","New Orleans Pelicans",     "Golden State Warriors","full_game",240.5,"UNDER"),
    ("Boston Celtics",      "Phoenix Suns",              "Boston Celtics",   "team_total",  97.5, "OVER"),
    ("Minnesota Timberwolves","Portland Trail Blazers",  "Minnesota Timberwolves","full_game",249.5,"UNDER"),
    ("Orlando Magic",       "Los Angeles Lakers",        "Los Angeles Lakers","full_game", 243.5, "UNDER"),
]

def get_results():
    print("  Fetching results...", end='', flush=True)
    # Try yesterday's date
    from datetime import timedelta
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={yesterday}"
    data = requests.get(url, timeout=10).json()
    events = data.get('events', [])
    # also try today
    if not events:
        data = requests.get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard", timeout=10).json()
        events = data.get('events', [])
    print(f" ✓ ({len(events)} games found)")
    return events

def find_game(events, away, home):
    away_last = away.split()[-1].lower()
    home_last = home.split()[-1].lower()
    for ev in events:
        comp = ev['competitions'][0]
        h = comp['competitors'][0]['team']['displayName'].lower()
        a = comp['competitors'][1]['team']['displayName'].lower()
        if (away_last in a or away_last in h) and (home_last in h or home_last in a):
            h_score = int(comp['competitors'][0].get('score') or 0)
            a_score = int(comp['competitors'][1].get('score') or 0)
            status  = ev['status']['type']['description']
            # figure out which is actually home/away
            home_team = comp['competitors'][0]['team']['displayName']
            away_team = comp['competitors'][1]['team']['displayName']
            return {
                'home': home_team, 'away': away_team,
                'h_score': h_score, 'a_score': a_score,
                'total': h_score + a_score,
                'winner': home_team if h_score > a_score else away_team,
                'status': status
            }
    return None

def main():
    print()
    print("="*65)
    print("  🏀  NBA SLIP COMPARISON — FEB 24 2026")
    print("="*65)
    print()

    events = get_results()
    if not events:
        print("  ❌ No results found yet. Try again after games finish.")
        return

    hits = 0; misses = 0; pending = 0
    details = []

    for away, home, pick, pick_type, line, ou in SLIP:
        result = find_game(events, away, home)

        if not result:
            details.append({'match': f"{away.split()[-1]} @ {home.split()[-1]}", 'status': 'NOT FOUND', 'hit': None})
            pending += 1
            continue

        if result['status'] not in ['Final', 'Final/OT']:
            details.append({'match': f"{away.split()[-1]} @ {home.split()[-1]}", 'status': result['status'], 'hit': None})
            pending += 1
            continue

        # Check if pick hit
        hit = False
        if pick_type == "team_total":
            # Find the specific team's score
            pick_last = pick.split()[-1].lower()
            if pick_last in result['home'].lower():
                actual = result['h_score']
            else:
                actual = result['a_score']
            hit = (ou == "OVER" and actual > line) or (ou == "UNDER" and actual < line)
            actual_str = f"{pick.split()[-1]} scored {actual} (line {line})"
        else:
            actual = result['total']
            hit = (ou == "OVER" and actual > line) or (ou == "UNDER" and actual < line)
            actual_str = f"Total {actual} (line {line})"

        if hit: hits += 1
        else:   misses += 1

        details.append({
            'match': f"{result['away'].split()[-1]} @ {result['home'].split()[-1]}",
            'score': f"{result['a_score']}-{result['h_score']}",
            'pick': f"{ou} {line}",
            'actual': actual_str,
            'hit': hit,
            'status': result['status']
        })

    # Print results
    for d in details:
        if d['hit'] is None:
            print(f"  ⏳ {d['match']:<30} {d['status']}")
        else:
            icon = "✅" if d['hit'] else "❌"
            print(f"  {icon} {d['match']:<30} Score: {d['score']}")
            print(f"     Bet: {d['pick']:<20} | {d['actual']}")
        print()

    total = hits + misses
    print("="*65)
    print(f"  📊  RESULTS: {hits}/{total} correct ({hits/total*100:.1f}% hit rate)" if total > 0 else "  ⏳ No completed games yet")
    if pending:
        print(f"  ⏳  {pending} games still pending/not found")

    if total > 0:
        print()
        if hits/total >= 0.70:
            print("  🔥 STRONG NIGHT — Model is working!")
        elif hits/total >= 0.55:
            print("  ✅ DECENT NIGHT — Needs improvement")
        else:
            print("  ⚠️  ROUGH NIGHT — Back to tuning")

    print("="*65)
    print()

if __name__ == '__main__':
    main()
