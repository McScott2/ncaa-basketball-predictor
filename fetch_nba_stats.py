#!/usr/bin/env python3
"""
fetch_nba_stats.py
Scrapes NBA team stats from Basketball Reference (free, no API key needed)
Gets: ppg, opp_ppg, pace, ortg, drtg, efg%, tov%, orb%, ft_rate
"""
import requests, json, re
from datetime import datetime

OUT_FILE = 'nba_team_stats.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.basketball-reference.com/',
}

# Team name mapping Basketball-Reference -> ESPN display name
BREF_TO_ESPN = {
    'Atlanta Hawks':'Atlanta Hawks','Boston Celtics':'Boston Celtics',
    'Brooklyn Nets':'Brooklyn Nets','Charlotte Hornets':'Charlotte Hornets',
    'Chicago Bulls':'Chicago Bulls','Cleveland Cavaliers':'Cleveland Cavaliers',
    'Dallas Mavericks':'Dallas Mavericks','Denver Nuggets':'Denver Nuggets',
    'Detroit Pistons':'Detroit Pistons','Golden State Warriors':'Golden State Warriors',
    'Houston Rockets':'Houston Rockets','Indiana Pacers':'Indiana Pacers',
    'LA Clippers':'LA Clippers','Los Angeles Lakers':'Los Angeles Lakers',
    'Memphis Grizzlies':'Memphis Grizzlies','Miami Heat':'Miami Heat',
    'Milwaukee Bucks':'Milwaukee Bucks','Minnesota Timberwolves':'Minnesota Timberwolves',
    'New Orleans Pelicans':'New Orleans Pelicans','New York Knicks':'New York Knicks',
    'Oklahoma City Thunder':'Oklahoma City Thunder','Orlando Magic':'Orlando Magic',
    'Philadelphia 76ers':'Philadelphia 76ers','Phoenix Suns':'Phoenix Suns',
    'Portland Trail Blazers':'Portland Trail Blazers','Sacramento Kings':'Sacramento Kings',
    'San Antonio Spurs':'San Antonio Spurs','Toronto Raptors':'Toronto Raptors',
    'Utah Jazz':'Utah Jazz','Washington Wizards':'Washington Wizards',
}

NBA_AVG = {
    'ppg':113.5,'opp_ppg':113.5,'pace':98.5,
    'ortg':114.0,'drtg':114.0,'net_rtg':0.0,
    'efg_pct':0.535,'tov_pct':12.8,'orb_pct':25.0,'ft_rate':0.21,
    'fgm':41.5,'fga':88.0,'fg3m':13.5,'fg3a':37.0,
    'ftm':17.0,'fta':22.0,'orb':10.0,'drb':33.0,
    'ast':26.0,'tov':13.0,'stl':7.5,'blk':4.5,
    'fg_pct':0.47,'fg3_pct':0.36,'ft_pct':0.78,
}

def scrape_table(url, table_id):
    """Scrape a specific table from Basketball Reference"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
        # Find table
        start = html.find(f'id="{table_id}"')
        if start == -1:
            # Try commented out tables (bref hides some in comments)
            html = html.replace('<!--', '').replace('-->', '')
            start = html.find(f'id="{table_id}"')
        if start == -1:
            return None, None
        # Extract rows
        table_html = html[start:start+50000]
        # Parse headers
        header_matches = re.findall(r'<th[^>]*data-stat="([^"]+)"[^>]*>([^<]*)</th>', table_html[:2000])
        headers = [m[0] for m in header_matches if m[0] not in ('', 'DUMMY')]
        # Parse rows
        rows = []
        row_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
        for row_html in row_matches:
            if 'class="thead"' in row_html or 'class="over_header"' in row_html:
                continue
            cells = re.findall(r'<t[dh][^>]*data-stat="([^"]+)"[^>]*>(?:<[^>]+>)*([^<]*)(?:<[^>]+>)*</t[dh]>', row_html)
            if cells:
                row_dict = {k: v.strip() for k, v in cells}
                if row_dict.get('team_name_abbr') or row_dict.get('team'):
                    rows.append(row_dict)
        return headers, rows
    except Exception as e:
        print(f" ⚠️  {e}")
        return None, None

def safe_float(val, default=0.0):
    try:
        return float(val) if val and val != '' else default
    except:
        return default

def main():
    print("\n" + "="*60)
    print("  NBA STATS FETCHER — Basketball Reference")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60 + "\n")

    teams = {name: {'name': name, **NBA_AVG} for name in BREF_TO_ESPN.keys()}

    # 1. Per Game stats (ppg, fgm, fga, fg3m, orb, drb, ast, tov, stl, blk, fta, ftm)
    print("  Fetching per game stats...", end='', flush=True)
    _, rows = scrape_table('https://www.basketball-reference.com/leagues/NBA_2025.html', 'per_game-team')
    if rows:
        count = 0
        for row in rows:
            name = row.get('team_name_abbr', row.get('team',''))
            # Clean team name
            name = re.sub(r'\*$','',name).strip()
            if name not in teams: continue
            fgm=safe_float(row.get('fg',NBA_AVG['fgm']))
            fga=safe_float(row.get('fga',NBA_AVG['fga']))
            fg3m=safe_float(row.get('fg3',NBA_AVG['fg3m']))
            teams[name].update({
                'ppg':  safe_float(row.get('pts',  NBA_AVG['ppg'])),
                'fgm':  fgm, 'fga': fga, 'fg3m': fg3m,
                'fg3a': safe_float(row.get('fg3a', NBA_AVG['fg3a'])),
                'ftm':  safe_float(row.get('ft',   NBA_AVG['ftm'])),
                'fta':  safe_float(row.get('fta',  NBA_AVG['fta'])),
                'orb':  safe_float(row.get('orb',  NBA_AVG['orb'])),
                'drb':  safe_float(row.get('drb',  NBA_AVG['drb'])),
                'ast':  safe_float(row.get('ast',  NBA_AVG['ast'])),
                'tov':  safe_float(row.get('tov',  NBA_AVG['tov'])),
                'stl':  safe_float(row.get('stl',  NBA_AVG['stl'])),
                'blk':  safe_float(row.get('blk',  NBA_AVG['blk'])),
                'fg_pct':  safe_float(row.get('fg_pct',  0.47)),
                'fg3_pct': safe_float(row.get('fg3_pct', 0.36)),
                'ft_pct':  safe_float(row.get('ft_pct',  0.78)),
                'efg_pct': (fgm+0.5*fg3m)/max(fga,1),
            })
            count += 1
        print(f" ✓ ({count} teams)")
    else:
        print(" ⚠️  failed — using defaults")

    # 2. Opponent per game stats (opp_ppg)
    print("  Fetching opponent stats...", end='', flush=True)
    _, rows = scrape_table('https://www.basketball-reference.com/leagues/NBA_2025.html', 'per_game-opponent')
    if rows:
        count = 0
        for row in rows:
            name = re.sub(r'\*$','',row.get('team_name_abbr', row.get('team',''))).strip()
            if name not in teams: continue
            teams[name]['opp_ppg'] = safe_float(row.get('pts', NBA_AVG['opp_ppg']))
            count += 1
        print(f" ✓ ({count} teams)")
    else:
        print(" ⚠️  failed")

    # 3. Advanced stats (pace, ortg, drtg, efg%, tov%, orb%, ft_rate)
    print("  Fetching advanced stats...", end='', flush=True)
    _, rows = scrape_table('https://www.basketball-reference.com/leagues/NBA_2025.html', 'advanced-team')
    if rows:
        count = 0
        for row in rows:
            name = re.sub(r'\*$','',row.get('team_name_abbr', row.get('team',''))).strip()
            if name not in teams: continue
            pace  = safe_float(row.get('pace',  NBA_AVG['pace']))
            ortg  = safe_float(row.get('off_rtg', NBA_AVG['ortg']))
            drtg  = safe_float(row.get('def_rtg', NBA_AVG['drtg']))
            teams[name].update({
                'pace':    pace,
                'ortg':    ortg,
                'drtg':    drtg,
                'net_rtg': round(ortg - drtg, 1),
                'efg_pct': safe_float(row.get('efg_pct', teams[name]['efg_pct'])),
                'tov_pct': safe_float(row.get('tov_pct', NBA_AVG['tov_pct'])),
                'orb_pct': safe_float(row.get('orb_pct', NBA_AVG['orb_pct'])),
                'ft_rate': safe_float(row.get('ft_rate', NBA_AVG['ft_rate'])),
            })
            count += 1
        print(f" ✓ ({count} teams)")
    else:
        print(" ⚠️  failed — deriving from box score")
        # Derive from box score
        for name, t in teams.items():
            fga=t['fga']; fta=t['fta']; tov=t['tov']; orb=t['orb']; drb=t['drb']
            stl=t['stl']; blk=t['blk']
            poss=max(fga-orb+tov+0.44*fta, 70)
            ortg=(t['ppg']/poss)*100
            drtg=(t['opp_ppg']/poss)*100-(drb-33)*0.15-(stl-7.5)*0.40-(blk-4.5)*0.25
            pace=98.5+(fga-88)*0.15-(tov-13)*0.10
            teams[name].update({
                'ortg':round(ortg,1),'drtg':round(drtg,1),
                'pace':round(pace,1),'net_rtg':round(ortg-drtg,1),
            })

    # 4. Add form defaults
    for name, t in teams.items():
        t.update({'form_score':0.0,'ppg_l10':t['ppg'],
                  'opp_ppg_l10':t['opp_ppg'],'wins_l10':5,'losses_l10':5})

    # Build lookups
    name_to_id = {n.lower(): n for n in teams}
    abbr_to_id = {}
    for name in teams:
        abbr_to_id[name.split()[-1].lower()] = name

    # Use team name as ID for simplicity
    output = {
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'season':     '2024-25',
        'teams':      teams,
        'name_to_id': name_to_id,
        'abbr_to_id': abbr_to_id,
    }

    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n  ✅ {len(teams)} teams saved to {OUT_FILE}")
    print("\n  Sample stats:")
    for kw in ['Thunder','Lakers','Celtics']:
        t = next((v for v in teams.values() if kw in v['name']), None)
        if t:
            print(f"    {kw:12} ppg={t.get('ppg',0):.1f}  opp={t.get('opp_ppg',0):.1f}  "
                  f"ortg={t.get('ortg',0):.1f}  drtg={t.get('drtg',0):.1f}  "
                  f"pace={t.get('pace',0):.1f}  net={t.get('net_rtg',0):.1f}")

if __name__ == '__main__':
    main()
