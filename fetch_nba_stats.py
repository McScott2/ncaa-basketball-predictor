#!/usr/bin/env python3
"""
fetch_nba_stats.py
Pulls full NBA team stats from stats.nba.com and saves to nba_team_stats.json
Run this BEFORE nba_predictor.py in GitHub Actions.

Stats pulled:
  Base  — ppg, opp_ppg, fgm, fga, fg3m, fg3a, ftm, fta, orb, drb, ast, tov, stl, blk
  Advanced — pace, ortg, drtg, net_rtg, efg_pct, tov_pct, orb_pct, ft_rate, ts_pct
"""

import requests
import json
import os
from datetime import datetime

OUT_FILE = 'nba_team_stats.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  'Chrome/120.0.0.0 Safari/537.36',
    'Referer':    'https://www.nba.com/',
    'Origin':     'https://www.nba.com',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token':  'true',
    'Accept':             'application/json, text/plain, */*',
    'Accept-Language':    'en-US,en;q=0.9',
    'Connection':         'keep-alive',
}

BASE_URL = 'https://stats.nba.com/stats/leaguedashteamstats'
SEASON   = '2024-25'

def fetch(measure_type):
    params = {
        'MeasureType':   measure_type,
        'PerMode':       'PerGame',
        'Season':        SEASON,
        'SeasonType':    'Regular Season',
        'LeagueID':      '00',
        'LastNGames':    '0',
        'Month':         '0',
        'OpponentTeamID':'0',
        'PaceAdjust':    'N',
        'PlusMinus':     'N',
        'Rank':          'N',
        'Conference':    '',
        'Division':      '',
        'GameScope':     '',
        'GameSegment':   '',
        'Location':      '',
        'Outcome':       '',
        'PORound':       '0',
        'Period':        '0',
        'PlayerExperience': '',
        'PlayerPosition':   '',
        'ShotClockRange':   '',
        'StarterBench':     '',
        'TeamID':        '0',
        'TwoWay':        '0',
        'VsConference':  '',
        'VsDivision':    '',
        'DateFrom':      '',
        'DateTo':        '',
    }
    print(f"  Fetching {measure_type} stats...", end='', flush=True)
    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    headers = data['resultSets'][0]['headers']
    rows    = data['resultSets'][0]['rowSet']
    print(f" ✓ ({len(rows)} teams)")
    return headers, rows

def fetch_recent_form(team_id, n=10):
    """Fetch last N games for a team"""
    params = {
        'MeasureType':    'Base',
        'PerMode':        'PerGame',
        'Season':         SEASON,
        'SeasonType':     'Regular Season',
        'LeagueID':       '00',
        'LastNGames':     str(n),
        'Month':          '0',
        'OpponentTeamID': '0',
        'PaceAdjust':     'N',
        'PlusMinus':      'N',
        'Rank':           'N',
        'TeamID':         str(team_id),
        'DateFrom': '', 'DateTo': '',
        'Conference': '', 'Division': '', 'GameScope': '',
        'GameSegment': '', 'Location': '', 'Outcome': '',
        'PORound': '0', 'Period': '0', 'PlayerExperience': '',
        'PlayerPosition': '', 'ShotClockRange': '', 'StarterBench': '',
        'TwoWay': '0', 'VsConference': '', 'VsDivision': '',
    }
    try:
        r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        hdrs = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        if not rows: return None
        row = rows[0]
        d   = dict(zip(hdrs, row))
        return {
            'ppg_l10':     d.get('PTS', 0),
            'opp_ppg_l10': d.get('OPP_PTS', d.get('PTS', 0)),
            'wins_l10':    d.get('W', 5),
            'losses_l10':  d.get('L', 5),
        }
    except:
        return None

def main():
    print()
    print("=" * 60)
    print("  NBA STATS FETCHER")
    print(f"  Season: {SEASON}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()

    # --- BASE STATS ---
    base_hdrs, base_rows = fetch('Base')
    # --- ADVANCED STATS ---
    adv_hdrs, adv_rows = fetch('Advanced')
    # --- OPPONENT STATS (points allowed) ---
    opp_hdrs, opp_rows = fetch('Opponent')

    # Build team lookup: TEAM_ID -> dict of all stats
    teams = {}

    for row in base_rows:
        d = dict(zip(base_hdrs, row))
        tid  = str(d['TEAM_ID'])
        name = d['TEAM_NAME']
        teams[tid] = {
            'id':      tid,
            'name':    name,
            # Offense
            'ppg':     d.get('PTS', 110),
            'fgm':     d.get('FGM', 40),
            'fga':     d.get('FGA', 88),
            'fg3m':    d.get('FG3M', 12),
            'fg3a':    d.get('FG3A', 34),
            'ftm':     d.get('FTM', 18),
            'fta':     d.get('FTA', 23),
            'orb':     d.get('OREB', 10),
            'drb':     d.get('DREB', 33),
            'ast':     d.get('AST', 25),
            'tov':     d.get('TOV', 13),
            'stl':     d.get('STL', 7),
            'blk':     d.get('BLK', 5),
            'fg_pct':  d.get('FG_PCT', 0.47),
            'fg3_pct': d.get('FG3_PCT', 0.36),
            'ft_pct':  d.get('FT_PCT', 0.78),
            'wins':    d.get('W', 30),
            'losses':  d.get('L', 30),
        }

    for row in adv_rows:
        d   = dict(zip(adv_hdrs, row))
        tid = str(d['TEAM_ID'])
        if tid in teams:
            teams[tid].update({
                'pace':    d.get('PACE', 98.5),
                'ortg':    d.get('OFF_RATING', 112),
                'drtg':    d.get('DEF_RATING', 112),
                'net_rtg': d.get('NET_RATING', 0),
                'efg_pct': d.get('EFG_PCT', 0.53),
                'tov_pct': d.get('TM_TOV_PCT', 13),
                'orb_pct': d.get('OREB_PCT', 25),
                'ft_rate': d.get('FTA_RATE', 0.22),
                'ts_pct':  d.get('TS_PCT', 0.57),
                'pie':     d.get('PIE', 0.5),
            })

    for row in opp_rows:
        d   = dict(zip(opp_hdrs, row))
        tid = str(d['TEAM_ID'])
        if tid in teams:
            teams[tid].update({
                'opp_ppg':    d.get('OPP_PTS', 110),
                'opp_fgm':    d.get('OPP_FGM', 40),
                'opp_fga':    d.get('OPP_FGA', 88),
                'opp_fg3m':   d.get('OPP_FG3M', 12),
                'opp_fg3a':   d.get('OPP_FG3A', 34),
                'opp_efg_pct':d.get('OPP_EFG_PCT', 0.53),
                'opp_tov_pct':d.get('OPP_TOV_PCT', 13),
            })

    # Fetch recent form for each team (last 10 games)
    print()
    print("  Fetching L10 form for each team...")
    import time
    for i, (tid, t) in enumerate(teams.items()):
        form = fetch_recent_form(tid)
        if form:
            teams[tid].update(form)
        else:
            teams[tid].update({
                'ppg_l10': t['ppg'], 'opp_ppg_l10': t.get('opp_ppg', 110),
                'wins_l10': 5, 'losses_l10': 5,
            })
        if i % 5 == 0:
            time.sleep(0.5)  # be polite to the API

    # Also build a name->id lookup for ESPN game matching
    name_to_id = {t['name'].lower(): tid for tid, t in teams.items()}
    # Add common abbreviations
    abbr_map = {}
    for tid, t in teams.items():
        parts = t['name'].split()
        abbr_map[parts[-1].lower()] = tid  # last word e.g. "Lakers"

    output = {
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'season':     SEASON,
        'teams':      teams,
        'name_to_id': name_to_id,
        'abbr_to_id': abbr_map,
    }

    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n  ✅ {len(teams)} teams saved to {OUT_FILE}")
    print(f"  Stats: ppg, opp_ppg, pace, ortg, drtg, net_rtg, efg_pct, tov_pct, orb_pct, L10 form")

    # Quick sanity check
    print("\n  Sample — OKC Thunder:")
    okc = next((t for t in teams.values() if 'Thunder' in t['name']), None)
    if okc:
        print(f"    ppg={okc.get('ppg'):.1f}  opp_ppg={okc.get('opp_ppg',0):.1f}  "
              f"pace={okc.get('pace',0):.1f}  ortg={okc.get('ortg',0):.1f}  "
              f"drtg={okc.get('drtg',0):.1f}")

if __name__ == '__main__':
    main()
