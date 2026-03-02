#!/usr/bin/env python3
"""
fetch_nba_stats.py — balldontlie.io (no blocking, free)
"""
import requests, json, os
from datetime import datetime

OUT_FILE = 'nba_team_stats.json'
API_KEY  = os.environ.get('BALLDONTLIE_KEY', '')
BASE     = 'https://api.balldontlie.io/v1'
HEADERS  = {'Authorization': API_KEY} if API_KEY else {}

NBA_AVG = {
    'ppg':113.5,'opp_ppg':113.5,'pace':98.5,
    'ortg':114.0,'drtg':114.0,'net_rtg':0.0,
    'efg_pct':0.535,'tov_pct':12.8,'orb_pct':25.0,'ft_rate':0.21,
    'fgm':41.5,'fga':88.0,'fg3m':13.5,'fg3a':37.0,
    'ftm':17.0,'fta':22.0,'orb':10.0,'drb':33.0,
    'ast':26.0,'tov':13.0,'stl':7.5,'blk':4.5,
}

def safe_get(url, params=None, hdrs=None):
    try:
        r = requests.get(url, headers=hdrs or HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f" ⚠️  {e}")
        return None

def main():
    print("\n" + "="*60)
    print("  NBA STATS FETCHER — balldontlie.io")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*60 + "\n")

    # 1. Teams
    print("  Fetching team list...", end='', flush=True)
    data = safe_get(f"{BASE}/teams", params={'per_page':100})
    teams = {}
    if data:
        for t in data.get('data',[]):
            tid = str(t['id'])
            teams[tid] = {'id':tid,'name':t['full_name'],'abbr':t.get('abbreviation',''),**NBA_AVG}
    print(f" ✓ ({len(teams)} teams)")

    # 2. Season averages
    print("  Fetching season averages...", end='', flush=True)
    data = safe_get(f"{BASE}/season_averages", params={'season':2024,'per_page':100})
    count = 0
    if data:
        for row in data.get('data',[]):
            tname = row.get('team',{}).get('full_name','')
            tid   = next((k for k,v in teams.items() if v['name']==tname), None)
            if not tid: continue
            fgm=row.get('fgm',NBA_AVG['fgm']); fga=row.get('fga',NBA_AVG['fga']); fg3m=row.get('fg3m',NBA_AVG['fg3m'])
            teams[tid].update({
                'ppg':row.get('pts',NBA_AVG['ppg']),'orb':row.get('oreb',NBA_AVG['orb']),
                'drb':row.get('dreb',NBA_AVG['drb']),'ast':row.get('ast',NBA_AVG['ast']),
                'tov':row.get('turnover',NBA_AVG['tov']),'stl':row.get('stl',NBA_AVG['stl']),
                'blk':row.get('blk',NBA_AVG['blk']),'fgm':fgm,'fga':fga,'fg3m':fg3m,
                'fg3a':row.get('fg3a',NBA_AVG['fg3a']),'ftm':row.get('ftm',NBA_AVG['ftm']),
                'fta':row.get('fta',NBA_AVG['fta']),'fg_pct':row.get('fg_pct',0.47),
                'fg3_pct':row.get('fg3_pct',0.36),'ft_pct':row.get('ft_pct',0.78),
                'efg_pct':(fgm+0.5*fg3m)/max(fga,1),
            })
            count += 1
    print(f" ✓ ({count} teams updated)")

    # 3. opp_ppg from ESPN standings
    print("  Fetching opp_ppg from ESPN...", end='', flush=True)
    data = safe_get("https://site.api.espn.com/apis/site/v2/sports/basketball/nba/standings",
                    hdrs={'User-Agent':'Mozilla/5.0'})
    count = 0
    if data:
        for conf in data.get('children',[]):
            for entry in conf.get('standings',{}).get('entries',[]):
                tname = entry.get('team',{}).get('displayName','')
                for s in entry.get('stats',[]):
                    if s.get('name')=='avgPointsAgainst':
                        val = float(s.get('value',0))
                        if val > 0:
                            last = tname.split()[-1].lower()
                            tid  = next((k for k,v in teams.items() if last in v['name'].lower()),None)
                            if tid: teams[tid]['opp_ppg']=val; count+=1
    print(f" ✓ ({count} teams with opp_ppg)")

    # 4. Derive advanced metrics
    print("  Computing ortg/drtg/pace...", end='', flush=True)
    for tid, t in teams.items():
        ppg=t.get('ppg',113.5); opp=t.get('opp_ppg',113.5)
        fga=t.get('fga',88); fta=t.get('fta',22); tov=t.get('tov',13)
        orb=t.get('orb',10); drb=t.get('drb',33); stl=t.get('stl',7.5); blk=t.get('blk',4.5)
        poss=max(fga-orb+tov+0.44*fta,70)
        ortg=(ppg/poss)*100; drtg=(opp/poss)*100-(drb-33)*0.15-(stl-7.5)*0.40-(blk-4.5)*0.25
        pace=98.5+(fga-88)*0.15-(tov-13)*0.10
        teams[tid].update({
            'ortg':round(ortg,1),'drtg':round(drtg,1),'pace':round(pace,1),
            'net_rtg':round(ortg-drtg,1),'tov_pct':round(tov/max(fga+0.44*fta+tov,1)*100,1),
            'orb_pct':round(orb/max(orb+drb,1)*100,1),'ft_rate':round(fta/max(fga,1),3),
            'form_score':0.0,'ppg_l10':ppg,'opp_ppg_l10':opp,'wins_l10':5,'losses_l10':5,
        })
    print(" ✓")

    name_to_id = {t['name'].lower():tid for tid,t in teams.items()}
    abbr_to_id = {}
    for tid,t in teams.items():
        abbr_to_id[t.get('abbr','').lower()]=tid
        abbr_to_id[t['name'].split()[-1].lower()]=tid

    output = {'fetched_at':datetime.now().strftime('%Y-%m-%d %H:%M'),
              'season':'2024-25','teams':teams,'name_to_id':name_to_id,'abbr_to_id':abbr_to_id}
    with open(OUT_FILE,'w') as f: json.dump(output,f,indent=2)
    print(f"\n  ✅ {len(teams)} teams saved to {OUT_FILE}")

    # Sanity check
    print("\n  Sample stats:")
    for kw in ['Thunder','Lakers','Celtics']:
        t = next((v for v in teams.values() if kw in v['name']),None)
        if t:
            print(f"    {kw:12} ppg={t.get('ppg',0):.1f}  opp={t.get('opp_ppg',0):.1f}  "
                  f"ortg={t.get('ortg',0):.1f}  drtg={t.get('drtg',0):.1f}  "
                  f"pace={t.get('pace',0):.1f}  net={t.get('net_rtg',0):.1f}")

if __name__ == '__main__':
    main()
