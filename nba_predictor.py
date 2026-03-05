#!/usr/bin/env python3
"""
NBA ORACLE v6 — God Mode Prediction Engine
Fixes over v5:
  - Removed systematic UNDER bias (defensive penalty was too aggressive)
  - Calibrated team score estimates against real NBA avg (~226 pts/game)
  - Win pick accuracy now tracked separately from O/U accuracy
  - Terminal output now matches JSON (consistent rounding)
  - Defensive matchup penalty is now symmetric (affects both sides equally)
  - O/U edge threshold raised to 12pt for stronger signal
"""

import requests
import json
import os
import math
from datetime import datetime, timedelta

# ── CONFIG ────────────────────────────────────────────────────────────────
ODDS_API_KEY  = "0f51d878b8a4991349ceb3229a470f1c"
NBA_LEAGUE    = "basketball_nba"
LOG_FILE      = "nba_predictions_log.json"
STATS_CACHE   = "nba_team_stats.json"

# Real NBA 2024-25 average total: ~226 pts/game
NBA_AVG_TOTAL = 226.0
NBA_AVG_PACE  = 98.5

# ── LOAD SELF-TUNED WEIGHTS ───────────────────────────────────────────────
WEIGHTS_FILE = "model_weights.json"
DEFAULT_WEIGHTS = {
    'pythagorean':  0.30,
    'efficiency':   0.30,
    'four_factors': 0.20,
    'form':         0.15,
    'home_adv':     0.045,
    'total_bias':   0.0,
    'pace_weight':  1.0,
    'def_penalty':  0.98,
    'b2b_penalty':  0.97,
    'strong_ou_threshold': 12.0,
}

def load_weights():
    if os.path.exists(WEIGHTS_FILE):
        with open(WEIGHTS_FILE) as f:
            saved = json.load(f)
        w = {**DEFAULT_WEIGHTS, **saved.get('weights', {})}
        print(f"  🧠 Loaded tuned weights (version {saved.get('version', 1)})")
        return w
    return DEFAULT_WEIGHTS.copy()

W = load_weights()

# ── LOAD CACHED STATS ─────────────────────────────────────────────────────
_stats_cache = None
def load_stats_cache():
    global _stats_cache
    if _stats_cache: return _stats_cache
    if os.path.exists(STATS_CACHE):
        with open(STATS_CACHE) as f:
            _stats_cache = json.load(f)
        print(f"  📦 Loaded stats cache: {len(_stats_cache['teams'])} teams ({_stats_cache['fetched_at']})")
    return _stats_cache

def get_cached_team(team_name):
    cache = load_stats_cache()
    if not cache: return None
    name_lower = team_name.lower()
    teams = cache['teams']
    if name_lower in cache['name_to_id']:
        key = cache['name_to_id'][name_lower]
        return teams.get(key)
    last = name_lower.split()[-1]
    if last in cache['abbr_to_id']:
        key = cache['abbr_to_id'][last]
        return teams.get(key)
    for key, t in teams.items():
        tname = t.get('name','').lower()
        if last in tname or tname.split()[-1] in name_lower:
            return t
    return None

# ── MATH ──────────────────────────────────────────────────────────────────
def sigmoid(x):
    return 1 / (1 + math.exp(-max(-500, min(500, x))))

def pythagorean_wp(ppg, opp_ppg, exp=13.91):
    if opp_ppg == 0: return 0.5
    return (ppg ** exp) / (ppg ** exp + opp_ppg ** exp)

def safe_get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except:
        return None

# ── ESPN API ──────────────────────────────────────────────────────────────
def get_scoreboard(date_str=None):
    from datetime import timezone
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
    return safe_get(url)

def get_team_stats(team_id, team_name=None):
    if team_name:
        cached = get_cached_team(team_name)
        if cached:
            return cached
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    data = safe_get(url)
    # Defaults calibrated to real NBA 2024-25 averages
    stats = {
        'ppg':113.0,'opp_ppg':113.0,
        'fgm':40.0,'fga':88.0,
        'fg3m':12.0,'fg3a':34.0,
        'ftm':18.0,'fta':23.0,
        'orb':10.0,'drb':33.0,
        'ast':25.0,'tov':13.0,
        'stl':7.0,'blk':5.0,
        'ortg':113.0,'drtg':113.0,'pace':98.5,
        'efg_pct':0.535,'net_rtg':0.0,
    }
    if not data: return stats
    try:
        mapping = {
            'avgPoints':'ppg',
            'avgFieldGoalsMade':'fgm','avgFieldGoalsAttempted':'fga',
            'avgThreePointFieldGoalsMade':'fg3m','avgThreePointFieldGoalsAttempted':'fg3a',
            'avgFreeThrowsMade':'ftm','avgFreeThrowsAttempted':'fta',
            'avgOffensiveRebounds':'orb','avgDefensiveRebounds':'drb',
            'avgAssists':'ast','avgTurnovers':'tov',
            'avgSteals':'stl','avgBlocks':'blk',
        }
        for cat in data.get('results',{}).get('stats',{}).get('categories',[]):
            for s in cat.get('stats',[]):
                key = mapping.get(s.get('name'))
                if key:
                    val = float(s.get('value',0) or 0)
                    if val > 0: stats[key] = val
    except: pass
    return stats

def get_recent_form(team_id, num=10):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    data = safe_get(url)
    result = {'wins':5,'losses':5,'avg_pts':113.0,'avg_opp':113.0,
              'form_score':0.0,'streak':0,'streak_type':'W'}
    if not data: return result
    try:
        events    = data.get('events',[])
        completed = [e for e in events
                     if e.get('competitions',[{}])[0].get('status',{}).get('type',{}).get('completed')]
        recent = completed[-num:]
        wins=0; pts=0; opp=0; count=0
        streak=0; stype=None
        for ev in recent:
            comp = ev['competitions'][0]
            me   = next((c for c in comp['competitors'] if c['team']['id']==str(team_id)), None)
            them = next((c for c in comp['competitors'] if c['team']['id']!=str(team_id)), None)
            if me and them:
                tp = float(me.get('score') or 0)
                op = float(them.get('score') or 0)
                win = me.get('winner', False)
                if win: wins += 1
                pts += tp; opp += op; count += 1
                if stype is None:
                    stype = 'W' if win else 'L'
                if (win and stype=='W') or (not win and stype=='L'):
                    streak += 1
                else: break
        if count > 0:
            result.update({
                'wins':wins,'losses':count-wins,
                'avg_pts':pts/count,'avg_opp':opp/count,
                'form_score':(wins/count-0.5)*2,
                'streak':streak,'streak_type':stype or 'W'
            })
    except: pass
    return result

def get_team_record(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
    data = safe_get(url)
    try: return data['team']['record']['items'][0]['summary']
    except: return '?-?'

def detect_b2b(all_events, team_id):
    from datetime import timezone as _tz2
    yesterday = (datetime.now(_tz2.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    for ev in all_events:
        if ev.get('date','')[:10] != yesterday: continue
        comp = ev.get('competitions',[{}])[0]
        for c in comp.get('competitors',[]):
            if c.get('team',{}).get('id') == str(team_id):
                if comp.get('status',{}).get('type',{}).get('completed', False):
                    return True
    return False

# ── VEGAS ODDS ────────────────────────────────────────────────────────────
def get_vegas_lines():
    if not ODDS_API_KEY: return {}
    url = (f"https://api.the-odds-api.com/v4/sports/{NBA_LEAGUE}/odds/"
           f"?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,totals&oddsFormat=american")
    try:
        data = requests.get(url, timeout=10).json()
        result = {}
        if not isinstance(data, list): return {}
        for game in data:
            home = game.get('home_team','')
            away = game.get('away_team','')
            key  = tuple(sorted([home.lower(), away.lower()]))
            total=None; h2h=None
            for book in game.get('bookmakers',[]):
                for mkt in book.get('markets',[]):
                    if mkt['key']=='totals' and not total:
                        ov = next((o for o in mkt['outcomes'] if o['name']=='Over'), None)
                        if ov: total = ov['point']
                    if mkt['key']=='h2h' and not h2h:
                        ho = next((o for o in mkt['outcomes'] if o['name']==home), None)
                        ao = next((o for o in mkt['outcomes'] if o['name']==away), None)
                        if ho and ao:
                            def imp(p): return abs(p)/(abs(p)+100) if p<0 else 100/(p+100)
                            hp=imp(ho['price']); ap=imp(ao['price']); t=hp+ap
                            h2h={'home_implied':hp/t,'away_implied':ap/t,
                                 'home_odds':ho['price'],'away_odds':ao['price']}
                if total and h2h: break
            result[key] = {'total':total,'h2h':h2h}
        return result
    except Exception as e:
        print(f"  ⚠️  Odds API: {e}")
        return {}

def find_vegas(home, away, vmap):
    key = tuple(sorted([home.lower(), away.lower()]))
    if key in vmap: return vmap[key]
    hl = home.split()[-1].lower()
    al = away.split()[-1].lower()
    for k, v in vmap.items():
        if any(hl in t or al in t for t in k): return v
    return None

# ── PREDICTION ENGINE ─────────────────────────────────────────────────────
def predict(hs, as_, hf, af, h_b2b, a_b2b, vegas=None):
    """
    5-factor composite model:
    1. Pythagorean Win Expectation (30%)
    2. Adjusted Efficiency Matchup (30%)
    3. Four Factors (20%)
    4. Recent Form L10 (15%)
    5. Home Court + B2B adjustments (5%)

    FIX v6: Total estimation calibrated to NBA avg ~226 pts.
    Defensive penalty is now mild and symmetric — no UNDER bias.
    """
    # 1. PYTHAGOREAN
    h_pyth = pythagorean_wp(hs['ppg'], hs['opp_ppg'])
    a_pyth = pythagorean_wp(as_['ppg'], as_['opp_ppg'])
    pyth_edge = h_pyth - a_pyth

    # 2. EFFICIENCY MATCHUP
    h_off_vs_a_def = (hs['ortg'] - as_['drtg']) / 20
    a_off_vs_h_def = (as_['ortg'] - hs['drtg']) / 20
    eff_edge = h_off_vs_a_def - a_off_vs_h_def

    # 3. FOUR FACTORS
    h_efg = (hs['fgm'] + 0.5*hs['fg3m']) / max(hs['fga'],1)
    a_efg = (as_['fgm'] + 0.5*as_['fg3m']) / max(as_['fga'],1)
    h_tov = hs['tov'] / max(hs['fga'] + 0.44*hs['fta'] + hs['tov'],1)
    a_tov = as_['tov'] / max(as_['fga'] + 0.44*as_['fta'] + as_['tov'],1)
    h_orb = hs['orb'] / max(hs['orb'] + as_['drb'],1)
    a_orb = as_['orb'] / max(as_['orb'] + hs['drb'],1)
    h_ftr = hs['ftm'] / max(hs['fga'],1)
    a_ftr = as_['ftm'] / max(as_['fga'],1)
    four_factors = (
        (h_efg - a_efg)*0.40 +
        (a_tov - h_tov)*0.25 +
        (h_orb - a_orb)*0.20 +
        (h_ftr - a_ftr)*0.15
    )

    # 4. RECENT FORM
    form_edge = hf['form_score'] - af['form_score']

    # 5. HOME COURT + B2B
    home_adv = 0.045
    b2b_adj  = (-0.04 if h_b2b else 0) + (0.04 if a_b2b else 0)

    score = (
        pyth_edge    * W['pythagorean'] +
        eff_edge     * W['efficiency'] +
        four_factors * W['four_factors'] +
        form_edge    * W['form'] +
        W['home_adv'] + b2b_adj
    )
    wp = max(0.05, min(0.95, sigmoid(score * 10)))

    # ── CALIBRATED TOTAL ESTIMATE ─────────────────────────────────────────
    # FIX v6: Blend team offense with opponent defense, pace-adjusted.
    # Anchored so league-average teams produce ~226 pts combined.
    avg_pace  = (hs['pace'] + as_['pace']) / 2
    pace_mult = avg_pace / NBA_AVG_PACE

    h_est = ((hs['ppg'] * 0.6) + (as_['opp_ppg'] * 0.4)) * pace_mult
    a_est = ((as_['ppg'] * 0.6) + (hs['opp_ppg'] * 0.4)) * pace_mult

    # B2B fatigue — uses self-tuned penalty
    if h_b2b: h_est *= W['b2b_penalty']
    if a_b2b: a_est *= W['b2b_penalty']

    # ── DEFENSIVE MATCHUP — uses self-tuned penalty ───────────────────────
    h_net = hs['ortg'] - hs['drtg']
    a_net = as_['ortg'] - as_['drtg']
    both_elite_def = h_net < -2.0 and a_net < -2.0

    if both_elite_def:
        h_est *= W['def_penalty']
        a_est *= W['def_penalty']

    # total_bias corrects systematic over/under estimation (self-tuned nightly)
    total = h_est + a_est + W['total_bias']

    # ── O/U LINE ──────────────────────────────────────────────────────────
    if vegas and vegas.get('total'):
        ou_line     = vegas['total']
        line_source = 'Vegas'
    else:
        ou_line = round(
            (hs['ppg'] + as_['ppg'] + hs['opp_ppg'] + as_['opp_ppg']) / 2 +
            (avg_pace - NBA_AVG_PACE) * 0.8, 1)
        line_source = 'Model'

    fh_line   = round(ou_line * 0.475, 1)
    edge      = round(abs(total - ou_line), 1)
    # FIX v6: Raised to 12pt — reduces noise, improves O/U signal quality
    strong_ou = edge >= W['strong_ou_threshold'] and line_source == "Vegas"

    # ── SIGNALS ───────────────────────────────────────────────────────────
    signals = []
    if h_b2b: signals.append("😴 Home team on B2B — fatigue penalty applied")
    if a_b2b: signals.append("😴 Away team on B2B — fatigue penalty applied")
    if both_elite_def: signals.append("🛡️  ELITE DEFENSIVE MATCHUP — both teams top D")
    if h_pyth > a_pyth + 0.08: signals.append(f"📊 Home Pythagorean edge +{h_pyth-a_pyth:.2f}")
    if a_pyth > h_pyth + 0.08: signals.append(f"📊 Away Pythagorean edge +{a_pyth-h_pyth:.2f}")
    if hs['ortg'] > as_['drtg'] + 5: signals.append(f"⚔️  Home offense dominates ({hs['ortg']:.1f} vs {as_['drtg']:.1f} drtg)")
    if as_['ortg'] > hs['drtg'] + 5: signals.append(f"⚔️  Away offense dominates ({as_['ortg']:.1f} vs {hs['drtg']:.1f} drtg)")
    if hf['wins'] >= 8: signals.append(f"🔥 Home HOT: {hf['wins']}-{hf['losses']} L10")
    if af['wins'] >= 8: signals.append(f"🔥 Away HOT: {af['wins']}-{af['losses']} L10")
    if hf['streak'] >= 4: signals.append(f"🏆 Home {hf['streak']}-game {hf['streak_type']} streak")
    if af['streak'] >= 4: signals.append(f"🏆 Away {af['streak']}-game {af['streak_type']} streak")
    if h_efg > a_efg + 0.03: signals.append(f"🎯 Home eFG% edge ({h_efg:.3f} vs {a_efg:.3f})")
    if a_efg > h_efg + 0.03: signals.append(f"🎯 Away eFG% edge ({a_efg:.3f} vs {h_efg:.3f})")
    if total > 240: signals.append("💨 High-pace shootout expected")
    elif total < 215: signals.append("🛡️  Grind expected — low scoring")

    value_flag = None
    if vegas and vegas.get('h2h'):
        v_wp   = vegas['h2h']['home_implied']
        v_edge = wp - v_wp
        if abs(v_edge) >= 0.05:
            side = "HOME" if v_edge > 0 else "AWAY"
            signals.append(f"💰 VALUE BET: {side} {abs(v_edge)*100:.1f}% edge vs Vegas!")
            value_flag = {'side':side,'edge':v_edge}

    return {
        'wp':wp,'total':total,'h_est':h_est,'a_est':a_est,
        'ou_line':ou_line,'ou':'OVER' if total>ou_line else 'UNDER',
        'fh_est':round(total*0.475,1),'fh_line':fh_line,
        'fh_ou':'OVER' if total*0.475>fh_line else 'UNDER',
        'edge':edge,'strong_ou':strong_ou,'line_source':line_source,
        'both_def':both_elite_def,'signals':signals,'value':value_flag,
        'h_pyth':h_pyth,'a_pyth':a_pyth,
    }

# ── DISPLAY ───────────────────────────────────────────────────────────────
def bar(conf, w=20):
    f = int(conf*w)
    return f"[{'█'*f}{'░'*(w-f)}] {conf*100:.1f}%"

def print_game(home, away, h_rec, a_rec, tipoff, p, idx):
    wp   = p['wp']
    conf = wp if wp>0.5 else 1-wp
    pick = home if wp>0.5 else away
    god  = conf >= 0.70

    print(f"{'═'*68}")
    tags = ""
    if god:            tags += "  🔥 GOD PICK"
    if p['strong_ou']: tags += "  💰 STRONG O/U"
    if p['both_def']:  tags += "  🛡️ DEF MATCHUP"
    print(f"  GAME {idx}{tags}")
    print(f"  {away} ({a_rec})  @  {home} ({h_rec})")
    print(f"  ⏰ {tipoff}")
    print(f"{'─'*68}")

    hp = int(wp*30); ap = 30-hp
    print(f"  WIN PROB  {'░'*ap}{'█'*hp}")
    print(f"            {away.split()[-1][:12]:<12} {int((1-wp)*100)}%"
          f"  ←→  {int(wp*100)}% {home.split()[-1][:12]}")
    print()
    print(f"  🏆 PICK:        {pick}")
    print(f"  📊 CONFIDENCE:  {bar(conf)}")
    print()
    # FIX v6: round() for terminal matches JSON storage (no floating point drift)
    print(f"  Full Game:   Est {round(p['total'])} pts  |  {p['ou']} {p['ou_line']}  "
          f"[Edge: {p['edge']}pt | {p['line_source']}]")
    print(f"  First Half:  Est {round(p['fh_est'])} pts  |  {p['fh_ou']} {p['fh_line']}")
    print(f"  🏠 {home[:28]:<28}  Est {round(p['h_est'])} pts")
    print(f"  ✈️  {away[:28]:<28}  Est {round(p['a_est'])} pts")
    print(f"  📈 Pythagorean:  Home {p['h_pyth']:.3f}  |  Away {p['a_pyth']:.3f}")

    if p['signals']:
        print()
        print("  🔍 SIGNALS:")
        for sig in p['signals'][:6]:
            print(f"     • {sig}")
    print()

def print_summary(summary):
    if not summary: return
    print(f"{'═'*68}")
    print("  📊  SUMMARY")
    print(f"{'═'*68}")
    god    = [s for s in summary if s['conf'] >= 0.70]
    strong = [s for s in summary if s['strong_ou']]
    overs  = [s for s in summary if s['ou']=='OVER']
    unders = [s for s in summary if s['ou']=='UNDER']
    avg_c  = sum(s['conf'] for s in summary)/len(summary)
    print(f"  Total games        : {len(summary)}")
    print(f"  Avg confidence     : {avg_c*100:.1f}%")
    print(f"  God picks (≥70%)   : {len(god)}")
    print(f"  Strong O/U (≥12pt) : {len(strong)}")
    print(f"  Overs / Unders     : {len(overs)} / {len(unders)}")
    print()
    if god:
        print("  🔥 GOD PICKS — WIN PICKS:")
        for s in god:
            print(f"     ✅ {s['pick']}")
            print(f"        {s['conf']*100:.1f}% conf  |  {s['tipoff']}")
        print()
    if strong:
        print("  💰 STRONG O/U PICKS (12pt+ edge):")
        for s in strong:
            parts = s['matchup'].split(' @ ')
            away_s = parts[0].split()[-1] if len(parts)>1 else s['matchup']
            home_s = parts[1].split()[-1] if len(parts)>1 else ''
            print(f"     ✅ {away_s} @ {home_s}")
            print(f"        {s['ou']} {s['ou_line']}  |  Edge: {s['edge']}pt  |  {s['tipoff']}")
        print()
    print("  ⚠️  Bet only God Picks + Strong O/U. Max 5 picks.")
    print("  ⚠️  Never stake more than you can afford to lose.")
    print(f"{'═'*68}")
    print()

# ── SAVE PREDICTIONS ──────────────────────────────────────────────────────
def save_predictions(summary):
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            log = json.load(f)

    date_str   = datetime.now().strftime('%Y-%m-%d')
    today_only = [p for p in summary if p.get('day','TODAY') == 'TODAY']

    if not today_only:
        print("  ⚠️  No TODAY games to save — skipping log")
        return

    # FIX v7: Never overwrite today's predictions if they already exist.
    # This locks in the O/U lines from the first run of the day,
    # preventing line drift when the bot runs a second time at 5PM.
    existing = next((e for e in log if e['date'] == date_str), None)
    if existing and existing.get('predictions'):
        print(f"  🔒 Predictions for {date_str} already locked — skipping overwrite")
        print(f"     (lines locked at {existing.get('saved_at','unknown')})")
        return

    log = [e for e in log if e['date'] != date_str]
    log.append({
        'date':        date_str,
        'predictions': today_only,
        'saved_at':    datetime.now().strftime('%Y-%m-%d %H:%M')
    })
    with open(LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)
    print(f"  💾 {len(today_only)} predictions saved to {LOG_FILE}")
    print(f"  🔒 Lines locked for {date_str} — will not be overwritten today")

# ── AUTO COMPARE ──────────────────────────────────────────────────────────
def auto_compare():
    if not os.path.exists(LOG_FILE): return
    with open(LOG_FILE) as f:
        log = json.load(f)

    yesterday = (datetime.now()-timedelta(days=1)).strftime('%Y-%m-%d')
    entry     = next((e for e in log if e['date']==yesterday), None)
    if not entry: return

    print(f"\n{'═'*68}")
    print(f"  🔍  AUTO COMPARE — {yesterday}")
    print(f"{'═'*68}")

    ystr = yesterday.replace('-','')
    url  = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={ystr}"
    try:
        events = requests.get(url, timeout=10).json().get('events',[])
    except:
        print("  ⚠️  Could not fetch yesterday's results")
        return

    # FIX v6: Track O/U and win picks separately
    ou_hits=0;  ou_total=0
    win_hits=0; win_total=0

    for pred in entry['predictions']:
        matchup  = pred['matchup']
        ou       = pred['ou']
        ou_line  = pred['ou_line']
        pick     = pred['pick']
        conf     = pred['conf']
        parts    = matchup.split(' @ ')
        if len(parts) != 2: continue
        away_last = parts[0].split()[-1].lower()
        home_last = parts[1].split()[-1].lower()

        result = None
        for ev in events:
            comp = ev['competitions'][0]
            h = comp['competitors'][0]['team']['displayName'].lower()
            a = comp['competitors'][1]['team']['displayName'].lower()
            if (away_last in a or away_last in h) and (home_last in h or home_last in a):
                hs  = int(comp['competitors'][0].get('score') or 0)
                as_ = int(comp['competitors'][1].get('score') or 0)
                status = ev['status']['type']['description']
                winner = comp['competitors'][0]['team']['displayName'] if hs > as_ \
                         else comp['competitors'][1]['team']['displayName']
                result = {'total':hs+as_,'h_score':hs,'a_score':as_,
                          'winner':winner,'status':status,
                          'home':comp['competitors'][0]['team']['displayName'],
                          'away':comp['competitors'][1]['team']['displayName']}
                break

        if not result or result['status'] not in ['Final','Final/OT']:
            print(f"  ⏳ {parts[0].split()[-1]} @ {parts[1].split()[-1]} — no result yet")
            continue

        ou_hit  = (ou=='OVER'  and result['total'] > ou_line) or \
                  (ou=='UNDER' and result['total'] < ou_line)
        # FIX v6: also check win pick
        win_hit = pick.split()[-1].lower() in result['winner'].lower()

        ou_icon  = "✅" if ou_hit  else "❌"
        win_icon = "✅" if win_hit else "❌"

        if ou_hit:  ou_hits  += 1
        if win_hit: win_hits += 1
        ou_total  += 1
        win_total += 1

        print(f"  {result['away'].split()[-1]:<12} @ {result['home'].split()[-1]:<14}"
              f" {result['a_score']}-{result['h_score']} (Total: {result['total']})")
        print(f"     O/U: {ou_icon} {ou} {ou_line:<6} | "
              f"WIN: {win_icon} Picked {pick.split()[-1]:<14} | "
              f"Actual: {result['winner'].split()[-1]}")
        print()

    if ou_total > 0:
        ou_pct  = ou_hits  / ou_total  * 100
        win_pct = win_hits / win_total * 100 if win_total > 0 else 0

        print(f"  📊  O/U  Accuracy : {ou_hits}/{ou_total} = {ou_pct:.1f}%")
        print(f"  📊  WIN  Accuracy : {win_hits}/{win_total} = {win_pct:.1f}%")
        combined = (ou_hits+win_hits) / (ou_total+win_total) * 100
        print(f"  📊  COMBINED      : {combined:.1f}%")

        if ou_pct >= 70:   print("  🔥 STRONG — Model is working!")
        elif ou_pct >= 55: print("  ✅ DECENT — Minor tuning needed")
        else:              print("  ⚠️  NEEDS REVIEW")

        with open(LOG_FILE) as f: log = json.load(f)
        for e in log:
            if e['date'] == yesterday:
                e['result'] = {
                    'hits':ou_hits,'total':ou_total,'pct':round(ou_pct,1),
                    'win_hits':win_hits,'win_total':win_total,'win_pct':round(win_pct,1)
                }
                for pred in e['predictions']:
                    parts = pred['matchup'].split(' @ ')
                    if len(parts) != 2: continue
                    away_last = parts[0].split()[-1].lower()
                    home_last = parts[1].split()[-1].lower()
                    for ev in events:
                        comp = ev['competitions'][0]
                        h = comp['competitors'][0]['team']['displayName'].lower()
                        a = comp['competitors'][1]['team']['displayName'].lower()
                        if (away_last in a or away_last in h) and (home_last in h or home_last in a):
                            hs  = int(comp['competitors'][0].get('score') or 0)
                            as_ = int(comp['competitors'][1].get('score') or 0)
                            status = ev['status']['type']['description']
                            if status in ['Final','Final/OT']:
                                pred['actual_total'] = hs+as_
                                pred['actual_home']  = hs
                                pred['actual_away']  = as_
                                winner = comp['competitors'][0]['team']['displayName'] if hs > as_ \
                                         else comp['competitors'][1]['team']['displayName']
                                ou_hit2  = (pred['ou']=='OVER'  and hs+as_ > pred['ou_line']) or \
                                           (pred['ou']=='UNDER' and hs+as_ < pred['ou_line'])
                                pred['result']     = 'hit' if ou_hit2 else 'miss'
                                pred['win_result'] = 'hit' if pred['pick'].split()[-1].lower() in winner.lower() else 'miss'
                            break
        with open(LOG_FILE,'w') as f: json.dump(log, f, indent=2)
        print(f"  💾 Results saved to {LOG_FILE}")
    print(f"{'═'*68}\n")

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print()
    print(f"{'═'*68}")
    print("  🏀  NBA ORACLE v6 — GOD MODE PREDICTION ENGINE")
    print(f"  📅  {datetime.now().strftime('%A, %B %d %Y  %H:%M WAT')}")
    print(f"{'═'*68}\n")

    print("  Loading Vegas O/U lines...", end='', flush=True)
    vmap = get_vegas_lines()
    if vmap: print(f" ✓ {len(vmap)} games with live lines")
    else:    print(" ⚠️  No lines — using model lines")

    print("  Fetching today's schedule...", end='', flush=True)
    today_data   = get_scoreboard()
    today_events = today_data.get('events',[]) if today_data else []
    print(" ✓")

    print("  Fetching tomorrow's schedule...", end='', flush=True)
    from datetime import timezone as _tz
    tom_str    = (datetime.now(_tz.utc)+timedelta(days=1)).strftime('%Y%m%d')
    tom_data   = get_scoreboard(tom_str)
    tom_events = tom_data.get('events',[]) if tom_data else []
    print(" ✓\n")

    all_events  = today_events + tom_events
    today_sched = [e for e in today_events if e.get('status',{}).get('type',{}).get('state')=='pre']
    tom_sched   = [e for e in tom_events   if e.get('status',{}).get('type',{}).get('state')=='pre']
    all_sched   = [('TODAY',e) for e in today_sched] + [('TOMORROW',e) for e in tom_sched]

    if not all_sched:
        print("  ⚠️  No scheduled games found.")
        print("  NBA games tip off between 12:00–09:00 Nigeria time.")
        auto_compare()
        return

    print(f"  Found {len(today_sched)} today + {len(tom_sched)} tomorrow = {len(all_sched)} total\n")

    summary = []
    idx     = 1
    cur_day = None

    for label, event in all_sched:
        if label != cur_day:
            cur_day = label
            if label == 'TODAY':
                day_str = f"TODAY — {datetime.now().strftime('%b %d')}"
                n_games = len(today_sched)
            else:
                day_str = f"TOMORROW — {(datetime.now()+timedelta(days=1)).strftime('%b %d')}"
                n_games = len(tom_sched)
            print(f"\n  {'━'*60}")
            print(f"  📅  {day_str}  ({n_games} games)")
            print(f"  {'━'*60}\n")

        try:
            comp      = event['competitions'][0]
            home_c    = comp['competitors'][0]
            away_c    = comp['competitors'][1]
            home_id   = home_c['team']['id']
            away_id   = away_c['team']['id']
            home_name = home_c['team']['displayName']
            away_name = away_c['team']['displayName']

            tipoff = "TBD"
            try:
                t = datetime.strptime(event['date'],'%Y-%m-%dT%H:%MZ') + timedelta(hours=1)
                tipoff = t.strftime('%I:%M %p WAT')
            except: pass

            print(f"  ⏳ Analyzing: {away_name} @ {home_name}...", flush=True)

            hs    = get_team_stats(home_id, home_name)
            as_   = get_team_stats(away_id, away_name)
            hf    = get_recent_form(home_id)
            af    = get_recent_form(away_id)
            h_rec = get_team_record(home_id)
            a_rec = get_team_record(away_id)
            h_b2b = detect_b2b(all_events, home_id)
            a_b2b = detect_b2b(all_events, away_id)
            vegas = find_vegas(home_name, away_name, vmap)

            p = predict(hs, as_, hf, af, h_b2b, a_b2b, vegas)

            print_game(home_name, away_name, h_rec, a_rec, tipoff, p, idx)

            wp   = p['wp']
            conf = wp if wp>0.5 else 1-wp
            pick = home_name if wp>0.5 else away_name

            summary.append({
                'matchup':    f"{away_name} @ {home_name}",
                'pick':       pick,
                'conf':       round(conf, 4),
                'ou':         p['ou'],
                'ou_line':    p['ou_line'],
                'total':      round(p['total'], 1),
                'fh_ou':      p['fh_ou'],
                'fh_line':    p['fh_line'],
                'god':        conf >= 0.70,
                'tipoff':     tipoff,
                'day':        label,
                'edge':       p['edge'],
                'strong_ou':  p['strong_ou'],
                'line_source':p['line_source'],
                'result':     'pending',
            })
            idx += 1

        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            continue

    if summary:
        print_summary(summary)
        save_predictions(summary)

    auto_compare()

if __name__ == '__main__':
    main()