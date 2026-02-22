#!/usr/bin/env python3
"""
NBA ORACLE — God Mode Prediction Engine
Same proven structure as NCAA engine (10/13 hit rate)
Upgraded with NBA-specific factors:
  - Pythagorean Win Expectation (NBA exponent 13.91)
  - Pace-adjusted offensive/defensive ratings
  - Back-to-back fatigue detection
  - Home court advantage (proven NBA value)
  - Four Factors model
  - Recent form (last 10 games)
  - Vegas odds comparison (optional)
"""

import requests
import json
from datetime import datetime, timedelta
import math
import sys

# ── CONFIG ──────────────────────────────────────────────────────────────
ODDS_API_KEY = ""  # Optional: paste your key from the-odds-api.com
NBA_LEAGUE   = "basketball_nba"
SHOW_BOTH_DAYS = True  # Show today + tomorrow fixtures

# ── HELPERS ─────────────────────────────────────────────────────────────
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def pythagorean_wp(ppg, opp_ppg, exp=13.91):
    """NBA Pythagorean Win Expectation — proven formula used by front offices"""
    if opp_ppg == 0:
        return 0.5
    return (ppg ** exp) / (ppg ** exp + opp_ppg ** exp)

def safe_get(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return None

# ── ESPN API ─────────────────────────────────────────────────────────────
def get_scoreboard(date_str=None):
    """Get NBA scoreboard — today or specific date (YYYYMMDD)"""
    if date_str:
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_str}"
    else:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    return safe_get(url)

def get_team_stats(team_id):
    """Get full season stats for a team"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics"
    data = safe_get(url)
    stats = {
        'ppg': 110.0, 'opp_ppg': 110.0,
        'fgm': 40.0, 'fga': 88.0,
        'fg3m': 12.0, 'fg3a': 34.0,
        'ftm': 18.0, 'fta': 23.0,
        'orb': 10.0, 'drb': 33.0,
        'ast': 25.0, 'tov': 13.0,
        'stl': 7.0,  'blk': 5.0,
        'ortg': 112.0, 'drtg': 112.0,
        'pace': 98.0
    }
    if not data:
        return stats
    try:
        mapping = {
            'avgPoints': 'ppg',
            'avgFieldGoalsMade': 'fgm',
            'avgFieldGoalsAttempted': 'fga',
            'avgThreePointFieldGoalsMade': 'fg3m',
            'avgThreePointFieldGoalsAttempted': 'fg3a',
            'avgFreeThrowsMade': 'ftm',
            'avgFreeThrowsAttempted': 'fta',
            'avgOffensiveRebounds': 'orb',
            'avgDefensiveRebounds': 'drb',
            'avgAssists': 'ast',
            'avgTurnovers': 'tov',
            'avgSteals': 'stl',
            'avgBlocks': 'blk',
            'avgPointsAllowed': 'opp_ppg',
            'offensiveRating': 'ortg',
            'defensiveRating': 'drtg',
            'pace': 'pace',
        }
        categories = data.get('results', {}).get('stats', {}).get('categories', [])
        for cat in categories:
            for s in cat.get('stats', []):
                key = mapping.get(s.get('name'))
                if key:
                    val = float(s.get('value', 0) or 0)
                    if val > 0:
                        stats[key] = val
    except:
        pass
    return stats

def get_recent_form(team_id, num_games=10):
    """Get last N games form — wins, avg pts scored/allowed, streak"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
    data = safe_get(url)
    result = {
        'wins': 5, 'losses': 5,
        'avg_pts': 110.0, 'avg_opp': 110.0,
        'form_score': 0.0,
        'streak': 0, 'streak_type': 'W'
    }
    if not data:
        return result
    try:
        events = data.get('events', [])
        completed = [e for e in events
                     if e.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('completed')]
        recent = completed[-num_games:]
        wins = 0; pts = 0; opp = 0; count = 0
        streak = 0; streak_type = None
        for ev in recent:
            comp = ev['competitions'][0]
            me   = next((c for c in comp['competitors'] if c['team']['id'] == str(team_id)), None)
            them = next((c for c in comp['competitors'] if c['team']['id'] != str(team_id)), None)
            if me and them:
                tp = float(me.get('score') or 0)
                op = float(them.get('score') or 0)
                win = me.get('winner', False)
                if win: wins += 1
                pts += tp; opp += op; count += 1
                if streak_type is None:
                    streak_type = 'W' if win else 'L'
                if (win and streak_type == 'W') or (not win and streak_type == 'L'):
                    streak += 1
                else:
                    break
        if count > 0:
            result['wins']       = wins
            result['losses']     = count - wins
            result['avg_pts']    = pts / count
            result['avg_opp']    = opp / count
            result['form_score'] = (wins / count - 0.5) * 2   # -1 to +1
            result['streak']     = streak
            result['streak_type']= streak_type or 'W'
    except:
        pass
    return result

def get_team_record(team_id):
    """Get current season W-L record"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
    data = safe_get(url)
    try:
        return data['team']['record']['items'][0]['summary']
    except:
        return '?-?'

def detect_b2b(all_events, team_id):
    """Check if team played yesterday (back-to-back)"""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    for ev in all_events:
        date = ev.get('date', '')[:10]
        if date != yesterday:
            continue
        comp = ev.get('competitions', [{}])[0]
        for c in comp.get('competitors', []):
            if c.get('team', {}).get('id') == str(team_id):
                status = comp.get('status', {}).get('type', {}).get('completed', False)
                if status:
                    return True
    return False

# ── VEGAS ODDS ────────────────────────────────────────────────────────────
def get_vegas_odds():
    if not ODDS_API_KEY:
        return {}
    url = (f"https://api.the-odds-api.com/v4/sports/{NBA_LEAGUE}/odds/"
           f"?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,totals&oddsFormat=american")
    data = safe_get(url)
    odds_map = {}
    if not isinstance(data, list):
        return {}
    for game in data:
        home = game.get('home_team', '')
        away = game.get('away_team', '')
        key  = tuple(sorted([home.lower(), away.lower()]))
        h2h  = None; total = None
        for book in game.get('bookmakers', []):
            for mkt in book.get('markets', []):
                if mkt['key'] == 'h2h' and not h2h:
                    ho = next((o for o in mkt['outcomes'] if o['name'] == home), None)
                    ao = next((o for o in mkt['outcomes'] if o['name'] == away), None)
                    if ho and ao:
                        def impl(price):
                            return abs(price)/(abs(price)+100) if price < 0 else 100/(price+100)
                        hp = impl(ho['price']); ap = impl(ao['price'])
                        tot = hp + ap
                        h2h = {
                            'home_implied': hp/tot, 'away_implied': ap/tot,
                            'home_odds': ho['price'], 'away_odds': ao['price']
                        }
                if mkt['key'] == 'totals' and not total:
                    ov = next((o for o in mkt['outcomes'] if o['name'] == 'Over'), None)
                    if ov:
                        total = {'line': ov['point'], 'over_odds': ov['price']}
            if h2h and total:
                break
        odds_map[key] = {'h2h': h2h, 'total': total, 'home': home, 'away': away}
    return odds_map

def find_vegas(home_name, away_name, odds_map):
    key = tuple(sorted([home_name.lower(), away_name.lower()]))
    if key in odds_map:
        return odds_map[key]
    # fuzzy match
    home_last = home_name.split()[-1].lower()
    away_last  = away_name.split()[-1].lower()
    for k, v in odds_map.items():
        if any(home_last in t or away_last in t for t in k):
            return v
    return None

# ── PREDICTION ENGINE ─────────────────────────────────────────────────────
def predict_game(home_stats, away_stats, home_form, away_form, home_b2b, away_b2b, vegas=None):
    """
    Multi-factor NBA prediction model:
    1. Pythagorean Win Expectation (30%)
    2. Adjusted Efficiency Matchup (30%)
    3. Win % (20%)
    4. Recent Form L10 (15%)
    5. Home Court Advantage (constant)
    6. B2B Fatigue (adjustment)
    7. Vegas comparison (signal only)
    """
    signals = []

    # ── 1. PYTHAGOREAN EXPECTATION ──
    h_pyth = pythagorean_wp(home_stats['ppg'], home_stats['opp_ppg'])
    a_pyth = pythagorean_wp(away_stats['ppg'], away_stats['opp_ppg'])
    pyth_edge = h_pyth - a_pyth

    # ── 2. ADJUSTED EFFICIENCY (Ortg vs opponent Drtg) ──
    h_off_vs_a_def = (home_stats['ortg'] - away_stats['drtg']) / 20
    a_off_vs_h_def = (away_stats['ortg'] - home_stats['drtg']) / 20
    eff_edge = h_off_vs_a_def - a_off_vs_h_def

    # ── 3. FOUR FACTORS ──
    # eFG%
    h_efg = (home_stats['fgm'] + 0.5 * home_stats['fg3m']) / max(home_stats['fga'], 1)
    a_efg = (away_stats['fgm'] + 0.5 * away_stats['fg3m']) / max(away_stats['fga'], 1)
    # TOV rate
    h_tov_rate = home_stats['tov'] / max(home_stats['fga'] + 0.44 * home_stats['fta'] + home_stats['tov'], 1)
    a_tov_rate = away_stats['tov'] / max(away_stats['fga'] + 0.44 * away_stats['fta'] + away_stats['tov'], 1)
    # ORB%
    h_orb_pct = home_stats['orb'] / max(home_stats['orb'] + away_stats['drb'], 1)
    a_orb_pct = away_stats['orb'] / max(away_stats['orb'] + home_stats['drb'], 1)
    # FTR
    h_ftr = home_stats['ftm'] / max(home_stats['fga'], 1)
    a_ftr = away_stats['ftm'] / max(away_stats['fga'], 1)

    four_factors = (
        (h_efg - a_efg) * 0.40 +
        (a_tov_rate - h_tov_rate) * 0.25 +
        (h_orb_pct - a_orb_pct) * 0.20 +
        (h_ftr - a_ftr) * 0.15
    )

    # ── 4. RECENT FORM (L10) ──
    form_edge = (home_form['form_score'] - away_form['form_score'])

    # ── 5. HOME COURT ── (~3.2 pts = ~4.5% win prob in NBA)
    home_adv = 0.045

    # ── 6. BACK-TO-BACK FATIGUE ──
    b2b_adj = 0
    if home_b2b:
        b2b_adj -= 0.04
        signals.append("🔴 Home on B2B — fatigue penalty")
    if away_b2b:
        b2b_adj += 0.04
        signals.append("✅ Away on B2B — opponent fatigued")

    # ── COMPOSITE WIN PROBABILITY ──
    score = (
        pyth_edge   * 0.30 +
        eff_edge    * 0.30 +
        four_factors* 0.20 +
        form_edge   * 0.15 +
        home_adv +
        b2b_adj
    )
    wp = max(0.05, min(0.95, sigmoid(score * 10)))

    # ── PACE-ADJUSTED TOTAL ESTIMATE ──
    avg_pace = (home_stats['pace'] + away_stats['pace']) / 2
    h_score_est = ((home_stats['ortg'] + (100 - away_stats['drtg'])) / 2) * (avg_pace / 100)
    a_score_est = ((away_stats['ortg'] + (100 - home_stats['drtg'])) / 2) * (avg_pace / 100)
    # Blend with recent form scoring
    h_score_est = h_score_est * 0.6 + home_form['avg_pts'] * 0.4
    a_score_est = a_score_est * 0.6 + away_form['avg_pts'] * 0.4
    # B2B scoring penalty
    if home_b2b: h_score_est *= 0.98
    if away_b2b: a_score_est *= 0.98
    est_total = h_score_est + a_score_est

    # ── SIGNALS ──
    if h_pyth > a_pyth + 0.08:
        signals.append(f"📊 Home Pyth advantage +{(h_pyth-a_pyth):.2f}")
    elif a_pyth > h_pyth + 0.08:
        signals.append(f"📊 Away Pyth advantage +{(a_pyth-h_pyth):.2f}")

    if home_stats['ortg'] > away_stats['drtg'] + 5:
        signals.append(f"⚔️  Home offense dominates ({home_stats['ortg']:.1f} vs {away_stats['drtg']:.1f})")
    if away_stats['ortg'] > home_stats['drtg'] + 5:
        signals.append(f"⚔️  Away offense dominates ({away_stats['ortg']:.1f} vs {home_stats['drtg']:.1f})")

    if home_form['wins'] >= 8:
        signals.append(f"🔥 Home HOT: {home_form['wins']}-{home_form['losses']} L10")
    if away_form['wins'] >= 8:
        signals.append(f"🔥 Away HOT: {away_form['wins']}-{away_form['losses']} L10")
    if home_form['wins'] <= 2:
        signals.append(f"❄️  Home COLD: {home_form['wins']}-{home_form['losses']} L10")
    if away_form['wins'] <= 2:
        signals.append(f"❄️  Away COLD: {away_form['wins']}-{away_form['losses']} L10")

    if home_form['streak'] >= 4:
        signals.append(f"🏆 Home {home_form['streak']}-game {home_form['streak_type']} streak")
    if away_form['streak'] >= 4:
        signals.append(f"🏆 Away {away_form['streak']}-game {away_form['streak_type']} streak")

    if h_efg > a_efg + 0.03:
        signals.append(f"🎯 Home eFG% edge ({h_efg:.3f} vs {a_efg:.3f})")
    if a_efg > h_efg + 0.03:
        signals.append(f"🎯 Away eFG% edge ({a_efg:.3f} vs {h_efg:.3f})")

    if est_total > 240:
        signals.append("💨 High-pace shootout expected")
    elif est_total < 215:
        signals.append("🛡️  Defensive grind expected")

    # ── VEGAS COMPARISON ──
    value_bet = None
    if vegas and vegas.get('h2h'):
        vegas_wp = vegas['h2h']['home_implied']
        edge = wp - vegas_wp
        if abs(edge) >= 0.05:
            side = "HOME" if edge > 0 else "AWAY"
            pct  = abs(edge) * 100
            signals.append(f"💰 VALUE BET: {side} edge {pct:.1f}% vs Vegas line!")
            value_bet = {'side': side, 'edge': edge, 'our_wp': wp, 'vegas_wp': vegas_wp}

    return {
        'wp': wp,
        'est_total': est_total,
        'h_score': h_score_est,
        'a_score': a_score_est,
        'h_pyth': h_pyth,
        'a_pyth': a_pyth,
        'signals': signals,
        'value_bet': value_bet,
        'four_factors': four_factors,
        'eff_edge': eff_edge
    }

# ── DISPLAY ───────────────────────────────────────────────────────────────
def print_separator(char='═', width=70):
    print(char * width)

def confidence_bar(conf, width=20):
    filled = int(conf * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {conf*100:.1f}%"

def print_game(game_data, idx):
    home = game_data['home_name']
    away = game_data['away_name']
    p    = game_data['prediction']
    home_b2b = game_data['home_b2b']
    away_b2b = game_data['away_b2b']
    tipoff   = game_data['tipoff']
    h_rec    = game_data['home_rec']
    a_rec    = game_data['away_rec']
    vegas    = game_data.get('vegas')

    wp   = p['wp']
    conf = wp if wp > 0.5 else 1 - wp
    pick = home if wp > 0.5 else away

    ou_line = 224.5
    ou_label = "OVER" if p['est_total'] > ou_line else "UNDER"
    fh_est   = p['est_total'] * 0.475
    fh_line  = 107.0
    fh_label = "OVER" if fh_est > fh_line else "UNDER"

    is_god    = conf >= 0.70
    is_value  = bool(p['value_bet'])

    god_tag   = " 🔥 GOD PICK" if is_god else ""
    val_tag   = " 💰 VALUE BET" if is_value else ""
    b2b_tag   = f" 😴{'HOME' if home_b2b else ''}{'/' if home_b2b and away_b2b else ''}{'AWAY' if away_b2b else ''} B2B" if (home_b2b or away_b2b) else ""

    print_separator()
    print(f"  GAME {idx}{god_tag}{val_tag}{b2b_tag}")
    print(f"  {away} ({a_rec}) @ {home} ({h_rec})")
    print(f"  Tip-off: {tipoff}")
    print_separator('─')

    # Win probability bar
    home_pct = int(wp * 100)
    away_pct = 100 - home_pct
    bar_h = '█' * int(wp * 30)
    bar_a = '░' * (30 - int(wp * 30))
    print(f"  WIN PROB  {away[:15]:<15} {bar_a}{bar_h} {home[:15]}")
    print(f"            {away_pct}%{' '*27}{home_pct}%")
    print()

    # Pick
    conf_color = "🟢" if conf >= 0.70 else "🟡" if conf >= 0.60 else "🔵"
    print(f"  🏆 PICK:       {pick}")
    print(f"  {conf_color} CONFIDENCE:  {confidence_bar(conf)}")
    print()

    # Scores
    print(f"  📊 FULL GAME:  Est. {p['est_total']:.0f} pts  |  {ou_label} {ou_line}")
    print(f"  🎯 1ST HALF:   Est. {fh_est:.0f} pts  |  {fh_label} {fh_line}")
    print(f"  🏠 {home[:20]:<20} Est. {p['h_score']:.0f} pts")
    print(f"  ✈️  {away[:20]:<20} Est. {p['a_score']:.0f} pts")
    print()

    # Pythagorean
    print(f"  📈 PYTHAGOREAN: Home {p['h_pyth']:.3f} | Away {p['a_pyth']:.3f}")

    # Vegas
    if vegas and vegas.get('h2h'):
        h2h = vegas['h2h']
        tot = vegas.get('total')
        h_odds = f"+{h2h['home_odds']}" if h2h['home_odds'] > 0 else str(h2h['home_odds'])
        a_odds = f"+{h2h['away_odds']}" if h2h['away_odds'] > 0 else str(h2h['away_odds'])
        print(f"  💠 VEGAS ML:   {home[:15]} {h_odds} | {away[:15]} {a_odds}")
        if tot:
            print(f"  💠 VEGAS O/U:  {tot['line']} (we say {p['est_total']:.0f})")

    # Signals
    if p['signals']:
        print()
        print("  🔍 KEY SIGNALS:")
        for sig in p['signals'][:5]:
            print(f"     • {sig}")

    print()

def print_summary(results):
    print_separator('═')
    print("  📊 SESSION SUMMARY")
    print_separator('─')

    god_picks   = [(r['pick'], r['conf']) for r in results if r['conf'] >= 0.70]
    value_bets  = [r for r in results if r['is_value']]
    overs       = [r for r in results if r['ou'] == 'OVER']
    avg_conf    = sum(r['conf'] for r in results) / len(results) if results else 0
    avg_total   = sum(r['total'] for r in results) / len(results) if results else 0

    print(f"  Total games analyzed : {len(results)}")
    print(f"  Average confidence   : {avg_conf*100:.1f}%")
    print(f"  God picks (≥70%)     : {len(god_picks)}")
    print(f"  Value bets vs Vegas  : {len(value_bets)}")
    print(f"  Overs / Unders       : {len(overs)} / {len(results)-len(overs)}")
    print(f"  Avg total estimate   : {avg_total:.0f} pts")
    print()

    if god_picks:
        print("  🔥 GOD PICKS (build your slip from these):")
        for pick, conf in god_picks:
            print(f"     ✅ {pick} — {conf*100:.1f}% confidence")
        print()

    if value_bets:
        print("  💰 VALUE BETS VS VEGAS:")
        for r in value_bets:
            vb = r['value_bet']
            print(f"     💰 {vb['side']} edge {abs(vb['edge'])*100:.1f}% in {r['matchup']}")
        print()

    print("  ⚠️  BETTING ADVICE:")
    print("     • Use GOD PICKS only for your slip")
    print("     • Max 5-6 game parlays, not 13+")
    print("     • 100 naira stake until we confirm consistency")
    print("     • Never bet more than you can afford to lose")
    print_separator('═')

# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    print()
    print_separator('═')
    print("  🏀  NBA ORACLE — GOD MODE PREDICTION ENGINE")
    print(f"  📅  {datetime.now().strftime('%A, %B %d %Y  %H:%M')}")
    print_separator('═')
    print()

    # Load Vegas odds
    print("  Loading Vegas odds...", end='', flush=True)
    vegas_map = get_vegas_odds()
    if vegas_map:
        print(f" ✓ {len(vegas_map)} games loaded")
    else:
        print(" (no API key — skipping)")

    # Get today's games
    print("  Fetching today's NBA schedule...", end='', flush=True)
    today_data = get_scoreboard()
    today_events = today_data.get('events', []) if today_data else []

    # Get tomorrow's games
    tomorrow_str = (datetime.utcnow() + timedelta(days=1)).strftime('%Y%m%d')
    print(f" ✓")
    print("  Fetching tomorrow's NBA schedule...", end='', flush=True)
    tomorrow_data = get_scoreboard(tomorrow_str)
    tomorrow_events = tomorrow_data.get('events', []) if tomorrow_data else []
    print(f" ✓")

    # All events for B2B detection
    all_events = today_events + tomorrow_events

    # Filter scheduled only
    today_scheduled    = [e for e in today_events    if e.get('status', {}).get('type', {}).get('state') == 'pre']
    tomorrow_scheduled = [e for e in tomorrow_events if e.get('status', {}).get('type', {}).get('state') == 'pre']

    all_scheduled = [('TODAY', e) for e in today_scheduled] + \
                    [('TOMORROW', e) for e in tomorrow_scheduled]

    if not all_scheduled:
        print()
        print("  ⚠️  No scheduled games found right now.")
        print("  NBA games tip off between 12:00–09:00 Nigeria time.")
        print("  Try running this again closer to game time.")
        print()
        return

    total = len(all_scheduled)
    print(f"  Found {len(today_scheduled)} today + {len(tomorrow_scheduled)} tomorrow = {total} total games")
    print()

    results = []
    game_idx = 1
    current_day = None

    for day_label, event in all_scheduled:

        # Day header
        if day_label != current_day:
            current_day = day_label
            date_str = "TODAY" if day_label == 'TODAY' else f"TOMORROW ({(datetime.utcnow()+timedelta(days=1)).strftime('%b %d')})"
            print()
            print(f"  {'━'*60}")
            print(f"  📅  {date_str} — {len(today_scheduled) if day_label=='TODAY' else len(tomorrow_scheduled)} GAMES")
            print(f"  {'━'*60}")
            print()

        try:
            comp = event['competitions'][0]
            home_c = comp['competitors'][0]
            away_c = comp['competitors'][1]
            home_id   = home_c['team']['id']
            away_id   = away_c['team']['id']
            home_name = home_c['team']['displayName']
            away_name = away_c['team']['displayName']

            # Tipoff time (convert to Nigeria WAT = UTC+1)
            tipoff_str = "TBD"
            try:
                tipoff_utc = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ')
                tipoff_nga = tipoff_utc + timedelta(hours=1)
                tipoff_str = tipoff_nga.strftime('%I:%M %p WAT (Nigeria)')
            except:
                pass

            print(f"  ⏳ Analyzing: {away_name} @ {home_name}...", flush=True)

            home_stats = get_team_stats(home_id)
            away_stats = get_team_stats(away_id)
            home_form  = get_recent_form(home_id)
            away_form  = get_recent_form(away_id)
            home_rec   = get_team_record(home_id)
            away_rec   = get_team_record(away_id)
            home_b2b   = detect_b2b(all_events, home_id)
            away_b2b   = detect_b2b(all_events, away_id)
            vegas      = find_vegas(home_name, away_name, vegas_map)

            prediction = predict_game(
                home_stats, away_stats,
                home_form, away_form,
                home_b2b, away_b2b,
                vegas
            )

            game_data = {
                'home_name': home_name,
                'away_name': away_name,
                'home_rec': home_rec,
                'away_rec': away_rec,
                'tipoff': tipoff_str,
                'home_b2b': home_b2b,
                'away_b2b': away_b2b,
                'prediction': prediction,
                'vegas': vegas,
            }

            print_game(game_data, game_idx)

            wp   = prediction['wp']
            conf = wp if wp > 0.5 else 1 - wp
            pick = home_name if wp > 0.5 else away_name
            ou   = "OVER" if prediction['est_total'] > 224.5 else "UNDER"

            results.append({
                'pick': pick,
                'conf': conf,
                'total': prediction['est_total'],
                'ou': ou,
                'matchup': f"{away_name} @ {home_name}",
                'is_value': bool(prediction['value_bet']),
                'value_bet': prediction['value_bet'],
            })

            game_idx += 1

        except Exception as e:
            print(f"  ⚠️  Error processing game: {e}")
            continue

    # Final summary
    if results:
        print()
        print_summary(results)
    print()

if __name__ == '__main__':
    main()
