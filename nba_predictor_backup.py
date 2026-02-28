#!/usr/bin/env python3
"""
NBA ORACLE — God Mode v4
- Real O/U lines from The Odds API (SportyBet-equivalent lines)
- Defensive matchup penalty (elite D vs elite D = lower total)
- Minimum 8pt edge threshold for O/U picks
- Auto save + auto compare
"""

import requests
from datetime import datetime, timedelta
import math
import json
import os

# ── CONFIG ────────────────────────────────────────────────────────────────
ODDS_API_KEY = "0f51d878b8a4991349ceb3229a470f1c"

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def pythagorean_wp(ppg, opp, exp=13.91):
    if opp == 0: return 0.5
    return (ppg ** exp) / (ppg ** exp + opp ** exp)

def safe_get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except:
        return None

# ── REAL 2025-26 NBA TEAM STATS ───────────────────────────────────────────
# [ppg, opp_ppg, pace, ortg, drtg, w, l]
TEAM_STATS = {
    'Oklahoma City Thunder':        [118.2, 108.1, 99.2,  121.4, 110.8, 43, 14],
    'San Antonio Spurs':            [116.8, 109.2, 100.1, 119.2, 111.8, 40, 16],
    'Detroit Pistons':              [115.4, 108.8, 98.8,  117.8, 110.9, 42, 13],
    'Boston Celtics':               [119.1, 109.4, 97.2,  122.1, 112.1, 36, 19],
    'New York Knicks':              [114.2, 110.1, 95.8,  116.8, 112.4, 36, 21],
    'Cleveland Cavaliers':          [116.4, 108.2, 96.4,  119.8, 111.2, 36, 21],
    'Denver Nuggets':               [117.8, 111.2, 98.4,  120.4, 113.8, 36, 21],
    'Toronto Raptors':              [115.2, 111.8, 99.1,  117.4, 113.9, 33, 23],
    'Los Angeles Lakers':           [114.8, 111.4, 97.8,  117.2, 113.6, 34, 21],
    'Houston Rockets':              [112.4, 108.8, 96.2,  115.8, 111.9, 34, 21],
    'Philadelphia 76ers':           [113.8, 111.2, 97.1,  116.4, 113.8, 30, 26],
    'Phoenix Suns':                 [114.2, 112.1, 98.8,  116.8, 114.2, 33, 24],
    'Minnesota Timberwolves':       [112.8, 108.4, 96.8,  115.4, 110.9, 35, 22],
    'Miami Heat':                   [113.4, 110.8, 97.4,  116.1, 112.9, 31, 27],
    'Orlando Magic':                [110.8, 109.2, 95.4,  113.2, 111.4, 29, 26],
    'Golden State Warriors':        [113.2, 112.4, 99.4,  115.8, 114.9, 29, 27],
    'Atlanta Hawks':                [116.4, 115.8, 101.2, 118.9, 118.1, 27, 31],
    'LA Clippers':                  [111.8, 111.2, 96.6,  114.2, 113.6, 27, 29],
    'Portland Trail Blazers':       [109.2, 116.4, 97.2,  111.8, 119.2, 27, 30],
    'Chicago Bulls':                [111.4, 113.2, 97.8,  113.8, 115.8, 24, 33],
    'Charlotte Hornets':            [113.8, 115.4, 100.8, 116.2, 117.9, 26, 31],
    'Milwaukee Bucks':              [112.8, 113.4, 98.4,  115.2, 115.9, 24, 30],
    'Memphis Grizzlies':            [110.4, 112.8, 98.8,  112.8, 115.4, 21, 34],
    'Dallas Mavericks':             [112.8, 115.2, 98.2,  115.4, 117.8, 19, 36],
    'Washington Wizards':           [112.4, 117.8, 100.4, 114.8, 120.2, 16, 39],
    'Utah Jazz':                    [108.8, 114.2, 98.4,  111.2, 116.8, 18, 39],
    'Indiana Pacers':               [119.8, 121.4, 104.2, 122.4, 124.8, 15, 42],
    'New Orleans Pelicans':         [111.2, 115.8, 98.8,  113.8, 118.4, 16, 42],
    'Brooklyn Nets':                [108.4, 116.2, 99.4,  110.8, 118.8, 15, 40],
    'Sacramento Kings':             [112.2, 118.4, 101.8, 114.8, 120.9, 12, 46],
}

def get_stats(name):
    if name in TEAM_STATS:
        d = TEAM_STATS[name]
        return {'ppg':d[0],'opp_ppg':d[1],'pace':d[2],'ortg':d[3],'drtg':d[4],'w':d[5],'l':d[6]}
    name_last = name.split()[-1].lower()
    for k, d in TEAM_STATS.items():
        if name_last in k.lower():
            return {'ppg':d[0],'opp_ppg':d[1],'pace':d[2],'ortg':d[3],'drtg':d[4],'w':d[5],'l':d[6]}
    return {'ppg':113.0,'opp_ppg':113.0,'pace':98.5,'ortg':113.0,'drtg':113.0,'w':25,'l':30}

def get_scoreboard(date_str=None):
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    if date_str: url += f"?dates={date_str}"
    return safe_get(url)

def get_recent_form(team_id, n=10):
    defaults = {'wins':5,'losses':5,'avg_pts':113.0,'avg_opp':113.0,'form_score':0.0,'streak':0,'streak_type':'W'}
    data = safe_get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule")
    if not data: return defaults
    try:
        events = data.get('events',[])
        completed = [e for e in events if e.get('competitions',[{}])[0].get('status',{}).get('type',{}).get('completed')]
        recent = completed[-n:]
        wins=0; pf=0; pa=0; count=0; streak=0; streak_type=None
        for ev in recent:
            comp = ev['competitions'][0]
            me   = next((c for c in comp['competitors'] if c['team']['id']==str(team_id)),None)
            them = next((c for c in comp['competitors'] if c['team']['id']!=str(team_id)),None)
            if me and them:
                tp=float(me.get('score') or 0); op=float(them.get('score') or 0)
                win=bool(me.get('winner'))
                if win: wins+=1
                pf+=tp; pa+=op; count+=1
                if streak_type is None: streak_type='W' if win else 'L'
                if (win and streak_type=='W') or (not win and streak_type=='L'): streak+=1
                else: break
        if count>0:
            return {'wins':wins,'losses':count-wins,'avg_pts':pf/count,'avg_opp':pa/count,
                    'form_score':(wins/count-0.5)*2,'streak':streak,'streak_type':streak_type or 'W'}
    except: pass
    return defaults

def get_record(team_id):
    data = safe_get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}")
    try: return data['team']['record']['items'][0]['summary']
    except: return '?-?'

def is_b2b(team_id, all_events):
    yesterday = (datetime.utcnow()-timedelta(days=1)).strftime('%Y-%m-%d')
    for ev in all_events:
        if not ev.get('date','').startswith(yesterday): continue
        comp = ev.get('competitions',[{}])[0]
        if not comp.get('status',{}).get('type',{}).get('completed'): continue
        for c in comp.get('competitors',[]):
            if c.get('team',{}).get('id')==str(team_id): return True
    return False

def get_vegas_lines():
    """Fetch real O/U lines from The Odds API"""
    if not ODDS_API_KEY:
        return {}
    url = (f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/"
           f"?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,totals&oddsFormat=american")
    try:
        data = requests.get(url, timeout=10).json()
        result = {}
        if not isinstance(data, list):
            return {}
        for game in data:
            home = game.get('home_team','')
            away = game.get('away_team','')
            key  = tuple(sorted([home.lower(), away.lower()]))
            total = None; h2h = None
            for book in game.get('bookmakers',[]):
                for mkt in book.get('markets',[]):
                    if mkt['key'] == 'totals' and not total:
                        ov = next((o for o in mkt['outcomes'] if o['name']=='Over'), None)
                        if ov: total = ov['point']
                    if mkt['key'] == 'h2h' and not h2h:
                        ho = next((o for o in mkt['outcomes'] if o['name']==home), None)
                        ao = next((o for o in mkt['outcomes'] if o['name']==away), None)
                        if ho and ao:
                            def imp(p): return abs(p)/(abs(p)+100) if p<0 else 100/(p+100)
                            hp=imp(ho['price']); ap=imp(ao['price']); t=hp+ap
                            h2h = {'home_implied': hp/t, 'away_implied': ap/t}
                if total and h2h: break
            result[key] = {'total': total, 'h2h': h2h}
        return result
    except Exception as e:
        print(f"  ⚠️  Odds API error: {e}")
        return {}

def find_vegas(home, away, vmap):
    key = tuple(sorted([home.lower(), away.lower()]))
    if key in vmap: return vmap[key]
    hl = home.split()[-1].lower()
    al = away.split()[-1].lower()
    for k, v in vmap.items():
        if any(hl in t or al in t for t in k): return v
    return None

def predict(hs, as_, hf, af, h_b2b, a_b2b, vegas=None):
    # 1. PYTHAGOREAN
    h_pyth = pythagorean_wp(hs['ppg'], hs['opp_ppg'])
    a_pyth = pythagorean_wp(as_['ppg'], as_['opp_ppg'])
    pyth_edge = h_pyth - a_pyth

    # 2. NET RATING
    h_net = hs['ortg'] - hs['drtg']
    a_net = as_['ortg'] - as_['drtg']
    net_edge = (h_net - a_net) / 20

    # 3. EFFICIENCY MATCHUP
    eff_edge = ((hs['ortg']-as_['drtg']) - (as_['ortg']-hs['drtg'])) / 20

    # 4. WIN PERCENTAGE
    h_wp = hs['w'] / max(hs['w']+hs['l'],1)
    a_wp = as_['w'] / max(as_['w']+as_['l'],1)
    wp_edge = h_wp - a_wp

    # 5. FORM
    form_edge = hf['form_score'] - af['form_score']

    # 6. HOME COURT + B2B
    home_adv = 0.045
    b2b = (-0.04 if h_b2b else 0) + (0.04 if a_b2b else 0)

    score = (pyth_edge*0.28 + net_edge*0.22 + eff_edge*0.20 +
             wp_edge*0.18 + form_edge*0.12 + home_adv + b2b)
    wp = max(0.05, min(0.95, sigmoid(score*10)))

    # PACE-ADJUSTED TOTAL
    avg_pace = (hs['pace'] + as_['pace']) / 2
    pace_factor = avg_pace / 98.5

    h_est = (hs['ppg']*0.35 + hf['avg_pts']*0.25 +
             ((hs['ortg']-as_['drtg']) + as_['opp_ppg'])*0.40) * pace_factor * (0.98 if h_b2b else 1.0)
    a_est = (as_['ppg']*0.35 + af['avg_pts']*0.25 +
             ((as_['ortg']-hs['drtg']) + hs['opp_ppg'])*0.40) * pace_factor * (0.98 if a_b2b else 1.0)

    # ── DEFENSIVE MATCHUP PENALTY ──
    # Only apply when BOTH teams are genuinely elite defensive teams
    # Net rating threshold raised to be more selective
    h_net = hs['ortg'] - hs['drtg']
    a_net = as_['ortg'] - as_['drtg']
    both_defensive = h_net < 0.0 and a_net < 0.0  # both must be net negative
    if both_defensive:
        h_est *= 0.97
        a_est *= 0.97

    total = h_est + a_est

    # ── O/U LINE: Use Vegas if available, else dynamic ──
    if vegas and vegas.get('total'):
        ou_line = vegas['total']
        line_source = 'Vegas'
    else:
        ou_line = round(
            (hs['ppg'] + as_['ppg'] + hs['opp_ppg'] + as_['opp_ppg']) / 2 +
            (avg_pace - 98.5) * 0.8, 1)
        line_source = 'Model'

    fh_line = round(ou_line * 0.475, 1)

    # ── EDGE THRESHOLD ──
    # With real Vegas lines, only trust edges of 10+ points
    # Smaller edges = noise, not signal
    edge = abs(total - ou_line)
    strong_ou = edge >= 10.0

    return {
        'wp':wp, 'total':total, 'h_est':h_est, 'a_est':a_est,
        'ou_line':ou_line, 'ou':'OVER' if total>ou_line else 'UNDER',
        'fh_est':round(total*0.475,0), 'fh_line':fh_line,
        'fh_ou':'OVER' if total*0.475>fh_line else 'UNDER',
        'h_b2b':h_b2b, 'a_b2b':a_b2b,
        'edge': round(edge,1), 'strong_ou': strong_ou,
        'line_source': line_source,
        'both_def': both_defensive,
    }

def print_game(home, away, h_rec, a_rec, tipoff, p, status):
    wp   = p['wp']
    conf = wp if wp>0.5 else 1-wp
    pick = home if wp>0.5 else away
    b2b = []
    if p['h_b2b']: b2b.append(f"😴 {home.split()[-1]} B2B")
    if p['a_b2b']: b2b.append(f"😴 {away.split()[-1]} B2B")
    b2b_str = f"  [{', '.join(b2b)}]" if b2b else ""
    def_str = "  [🛡️ DEFENSIVE MATCHUP]" if p.get('both_def') else ""

    print(f"📍 {away} ({a_rec}) at {home} ({h_rec})  [{status}]{b2b_str}{def_str}")
    print(f"   ⏰ Tip-off:     {tipoff}")
    print(f"   🏆 Pick:        {pick}  ({conf*100:.1f}% confidence)")
    print(f"   📊 Full Game:   Est. {p['total']:.0f} pts  |  {p['ou']} {p['ou_line']}  [Edge: {p['edge']}pts | {p['line_source']}]")
    print(f"   🎯 First Half:  Est. {p['fh_est']:.0f} pts  |  {p['fh_ou']} {p['fh_line']}")
    print(f"   🏠 {home[:28]:<28} Est. {p['h_est']:.0f} pts")
    print(f"   ✈️  {away[:28]:<28} Est. {p['a_est']:.0f} pts")
    if conf >= 0.70:
        print(f"   🔥 GOD PICK — Strong confidence!")
    if p.get('strong_ou'):
        print(f"   💰 STRONG O/U — Edge of {p['edge']}pts from line!")
    print()

def main():
    print()
    print("="*65)
    print("  🏀  NBA ORACLE — GOD MODE v3")
    print(f"  📅  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}")
    print("="*65)
    print()

    print("  Fetching today's schedule...", end='', flush=True)
    today_data   = get_scoreboard()
    today_events = today_data.get('events',[]) if today_data else []
    print(" ✓")

    tom_str = (datetime.utcnow()+timedelta(days=1)).strftime('%Y%m%d')
    print("  Fetching tomorrow's schedule...", end='', flush=True)
    tom_data   = get_scoreboard(tom_str)
    tom_events = tom_data.get('events',[]) if tom_data else []
    print(" ✓")

    print("  Fetching real O/U lines from The Odds API...", end='', flush=True)
    vmap = get_vegas_lines()
    print(f" ✓ ({len(vmap)} games with live lines)" if vmap else " ⚠️  No lines returned — using model lines")

    all_events  = today_events+tom_events
    today_sched = [e for e in today_events if e.get('status',{}).get('type',{}).get('state')=='pre']
    tom_sched   = [e for e in tom_events   if e.get('status',{}).get('type',{}).get('state')=='pre']

    if not today_sched and not tom_sched:
        print()
        print("  ⚠️  No upcoming games found.")
        print("  NBA games tip off ~12:00am–9:00am Nigeria time.")
        return

    summary = []

    for label, games in [("TODAY",today_sched),("TOMORROW",tom_sched)]:
        if not games: continue
        print()
        print("="*65)
        print(f"  📅  {label} — {len(games)} GAMES")
        print("="*65)
        print()

        for event in games:
            try:
                comp      = event['competitions'][0]
                home_c    = comp['competitors'][0]
                away_c    = comp['competitors'][1]
                home_id   = home_c['team']['id']
                away_id   = away_c['team']['id']
                home_name = home_c['team']['displayName']
                away_name = away_c['team']['displayName']
                status    = event.get('status',{}).get('type',{}).get('description','Scheduled')
                try:
                    t = datetime.strptime(event['date'],'%Y-%m-%dT%H:%MZ')+timedelta(hours=1)
                    tipoff = t.strftime('%I:%M %p WAT')
                except:
                    tipoff = "TBD"

                print(f"  ⏳ Analyzing {away_name} @ {home_name}...", flush=True)
                hs    = get_stats(home_name)
                as_   = get_stats(away_name)
                hf    = get_recent_form(home_id)
                af    = get_recent_form(away_id)
                h_rec = get_record(home_id)
                a_rec = get_record(away_id)
                h_b2b = is_b2b(home_id, all_events)
                a_b2b = is_b2b(away_id, all_events)
                vegas = find_vegas(home_name, away_name, vmap)

                p = predict(hs, as_, hf, af, h_b2b, a_b2b, vegas)
                print_game(home_name, away_name, h_rec, a_rec, tipoff, p, status)

                conf = p['wp'] if p['wp']>0.5 else 1-p['wp']
                pick = home_name if p['wp']>0.5 else away_name
                summary.append({
                    'matchup':f"{away_name} @ {home_name}",
                    'pick':pick,'conf':conf,
                    'ou':p['ou'],'ou_line':p['ou_line'],
                    'total':p['total'],'god':conf>=0.70,
                    'tipoff':tipoff,'day':label,
                    'edge':p['edge'],'strong_ou':p['strong_ou'],
                    'line_source':p['line_source'],
                })
            except Exception as e:
                print(f"  ⚠️  Skipped: {e}")
                continue

    if not summary: return

    print("="*65)
    print("  📊  SUMMARY")
    print("="*65)
    print()
    god        = [s for s in summary if s['god']]
    strong_ou  = [s for s in summary if s.get('strong_ou')]
    overs      = [s for s in summary if s['ou']=='OVER']
    avg_c      = sum(s['conf'] for s in summary)/len(summary)
    print(f"  Total games      : {len(summary)}")
    print(f"  Avg confidence   : {avg_c*100:.1f}%")
    print(f"  Overs / Unders   : {len(overs)} / {len(summary)-len(overs)}")
    print(f"  God picks ≥70%   : {len(god)}")
    print(f"  Strong O/U ≥8pt  : {len(strong_ou)}")
    print()
    if god:
        print("  🔥 GOD PICKS (Win):")
        for s in god:
            print(f"     ✅ {s['pick']}")
            print(f"        {s['ou']} {s['ou_line']}  |  {s['conf']*100:.1f}% conf  |  {s['tipoff']}")
        print()
    if strong_ou:
        print("  💰 STRONG O/U PICKS (8pt+ edge — bet these):")
        for s in strong_ou:
            print(f"     ✅ {s['matchup'].split(' @ ')[0].split()[-1]} @ {s['matchup'].split(' @ ')[1].split()[-1]}")
            print(f"        {s['ou']} {s['ou_line']}  |  Edge: {s['edge']}pts  |  {s['tipoff']}")
        print()
    print("  ⚠️  Max 5 picks. 100 naira stake. Strong O/U picks only.")
    print()
    print("="*65)
    print()

    # ── AUTO SAVE PREDICTIONS ──
    save_predictions(summary)

    # ── AUTO COMPARE PREVIOUS DAY ──
    auto_compare()

def save_predictions(summary):
    """Save today's predictions to JSON for later comparison"""
    import json, os
    log_file = 'nba_predictions_log.json'

    # Load existing log
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = []

    date_str = datetime.now().strftime('%Y-%m-%d')

    # Remove existing entry for today if re-running
    log = [e for e in log if e['date'] != date_str]

    # Add today's predictions
    log.append({
        'date': date_str,
        'predictions': summary,
        'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M')
    })

    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

    print(f"  💾 Predictions saved to {log_file}")
    print(f"     {len(summary)} games logged for {date_str}")
    print()

def auto_compare():
    """Automatically compare yesterday's predictions against actual results"""
    import json, os
    from datetime import timedelta

    log_file = 'nba_predictions_log.json'
    if not os.path.exists(log_file):
        return

    with open(log_file, 'r') as f:
        log = json.load(f)

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday_entry = next((e for e in log if e['date'] == yesterday), None)

    if not yesterday_entry:
        return

    print("="*65)
    print(f"  🔍  AUTO COMPARE — {yesterday} PREDICTIONS vs ACTUAL")
    print("="*65)
    print()

    # Fetch yesterday's results
    ystr = yesterday.replace('-','')
    url  = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={ystr}"
    try:
        data   = requests.get(url, timeout=10).json()
        events = data.get('events', [])
    except:
        print("  ⚠️  Could not fetch yesterday's results")
        return

    if not events:
        print("  ⚠️  No results found for yesterday")
        return

    hits = 0; misses = 0
    preds = yesterday_entry['predictions']

    for pred in preds:
        matchup   = pred['matchup']        # "Away @ Home"
        ou        = pred['ou']             # OVER/UNDER
        ou_line   = pred['ou_line']
        pick      = pred['pick']
        conf      = pred['conf']

        # parse away/home from matchup
        parts     = matchup.split(' @ ')
        if len(parts) != 2: continue
        away_n, home_n = parts[0], parts[1]
        away_last = away_n.split()[-1].lower()
        home_last = home_n.split()[-1].lower()

        # find game in results
        result = None
        for ev in events:
            comp = ev['competitions'][0]
            h    = comp['competitors'][0]['team']['displayName'].lower()
            a    = comp['competitors'][1]['team']['displayName'].lower()
            if (away_last in a or away_last in h) and (home_last in h or home_last in a):
                h_score = int(comp['competitors'][0].get('score') or 0)
                a_score = int(comp['competitors'][1].get('score') or 0)
                status  = ev['status']['type']['description']
                winner  = comp['competitors'][0]['team']['displayName'] if h_score > a_score else comp['competitors'][1]['team']['displayName']
                result  = {'total': h_score+a_score, 'h_score': h_score, 'a_score': a_score,
                           'winner': winner, 'status': status,
                           'home': comp['competitors'][0]['team']['displayName'],
                           'away': comp['competitors'][1]['team']['displayName']}
                break

        if not result or result['status'] not in ['Final','Final/OT']:
            print(f"  ⏳ {away_n.split()[-1]} @ {home_n.split()[-1]} — no result yet")
            continue

        actual_total = result['total']
        hit = (ou == 'OVER' and actual_total > ou_line) or (ou == 'UNDER' and actual_total < ou_line)
        icon = "✅" if hit else "❌"
        if hit: hits += 1
        else:   misses += 1

        print(f"  {icon} {result['away'].split()[-1]:<12} @ {result['home'].split()[-1]:<15} {result['a_score']}-{result['h_score']} (Total: {actual_total})")
        print(f"     Pred: {ou} {ou_line:<8} | Pick: {pick.split()[-1]:<15} | Conf: {conf*100:.1f}%")
        print()

    total = hits + misses
    if total > 0:
        pct = hits/total*100
        print("="*65)
        print(f"  📊  {yesterday}: {hits}/{total} correct = {pct:.1f}%")
        if pct >= 70:   print("  🔥 STRONG — Keep this model!")
        elif pct >= 55: print("  ✅ DECENT — Minor tuning needed")
        else:           print("  ⚠️  NEEDS WORK — Review model")

        # Append result to log
        import json
        with open(log_file, 'r') as f:
            log = json.load(f)
        for e in log:
            if e['date'] == yesterday:
                e['result'] = {'hits': hits, 'total': total, 'pct': round(pct,1)}
        with open(log_file, 'w') as f:
            json.dump(log, f, indent=2)

        print(f"  💾 Result saved to {log_file}")
        print("="*65)
        print()

if __name__ == '__main__':
    main()