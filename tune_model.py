#!/usr/bin/env python3
"""
NBA ORACLE — Self-Tuning Engine
Runs automatically after nba_predictor.py to gradually evolve model weights.

How it works:
  1. Reads last night's results from nba_predictions_log.json
  2. Analyses WHY each prediction hit or missed
  3. Makes small weight adjustments (max 2% per night)
  4. Saves updated weights to model_weights.json
  5. nba_predictor.py loads these weights on next run

Optimizes for: O/U accuracy + Win pick accuracy equally
Learning rate: Gradual (small nudges, never overcorrects)
"""

import json
import os
from datetime import datetime, timedelta

WEIGHTS_FILE = "model_weights.json"
LOG_FILE     = "nba_predictions_log.json"
TUNE_LOG     = "tune_log.json"

# ── DEFAULT WEIGHTS ───────────────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    'pythagorean':  0.30,   # win model: pythagorean expectation
    'efficiency':   0.30,   # win model: ortg/drtg matchup
    'four_factors': 0.20,   # win model: eFG%, TOV%, ORB%, FTR
    'form':         0.15,   # win model: recent L10 form
    'home_adv':     0.045,  # win model: home court advantage
    'total_bias':   0.0,    # o/u model: positive = push estimates up, negative = push down
    'pace_weight':  1.0,    # o/u model: pace multiplier sensitivity
    'def_penalty':  0.98,   # o/u model: elite defensive matchup penalty
    'b2b_penalty':  0.97,   # o/u model: back-to-back fatigue penalty
    'strong_ou_threshold': 12.0,  # minimum edge (pts) to flag as Strong O/U
}

# Learning rate — max change per weight per night
LEARN_RATE = 0.02

def load_weights():
    if os.path.exists(WEIGHTS_FILE):
        with open(WEIGHTS_FILE) as f:
            saved = json.load(f)
        # Merge with defaults in case new keys were added
        weights = {**DEFAULT_WEIGHTS, **saved.get('weights', {})}
        print(f"  📦 Loaded weights (version {saved.get('version', 1)})")
    else:
        weights = DEFAULT_WEIGHTS.copy()
        print("  📦 No weights file found — using defaults")
    return weights

def save_weights(weights, version, notes):
    data = {
        'version':    version,
        'updated':    datetime.now().strftime('%Y-%m-%d %H:%M'),
        'weights':    weights,
        'notes':      notes,
    }
    with open(WEIGHTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  💾 Weights saved (version {version})")

def load_tune_log():
    if os.path.exists(TUNE_LOG):
        with open(TUNE_LOG) as f:
            return json.load(f)
    return []

def save_tune_log(log):
    with open(TUNE_LOG, 'w') as f:
        json.dump(log, f, indent=2)

def load_results(days=7):
    """Load last N days of completed results from log."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE) as f:
        log = json.load(f)
    completed = [e for e in log if 'result' in e]
    completed.sort(key=lambda x: x['date'])
    return completed[-days:]

def analyse_misses(results):
    """
    For each miss, figure out what signal led us astray.
    Returns a dict of signals and whether they trended toward over/under/win/loss.
    """
    analysis = {
        'ou_hits':        0,
        'ou_misses':      0,
        'win_hits':       0,
        'win_misses':     0,
        'missed_over':    0,   # predicted UNDER, went OVER
        'missed_under':   0,   # predicted OVER, went UNDER
        'total_error':    0.0, # avg (predicted_total - actual_total)
        'total_error_n':  0,
        'god_hits':       0,
        'god_misses':     0,
        'strong_ou_hits': 0,
        'strong_ou_misses': 0,
    }

    for day in results:
        for p in day.get('predictions', []):
            res     = p.get('result')
            win_res = p.get('win_result')
            god     = p.get('god', False)
            strong  = p.get('strong_ou', False)
            total   = p.get('total')          # model's estimated total
            actual  = p.get('actual_total')   # real total

            if res == 'hit':
                analysis['ou_hits'] += 1
                if god:    analysis['god_hits'] += 1
                if strong: analysis['strong_ou_hits'] += 1
            elif res == 'miss':
                analysis['ou_misses'] += 1
                ou = p.get('ou', '')
                if ou == 'UNDER': analysis['missed_over']  += 1  # went OVER
                if ou == 'OVER':  analysis['missed_under'] += 1  # went UNDER
                if god:    analysis['god_misses'] += 1
                if strong: analysis['strong_ou_misses'] += 1

            if win_res == 'hit':   analysis['win_hits']   += 1
            elif win_res == 'miss': analysis['win_misses'] += 1

            if total and actual:
                analysis['total_error']   += (total - actual)
                analysis['total_error_n'] += 1

    if analysis['total_error_n'] > 0:
        analysis['avg_total_error'] = analysis['total_error'] / analysis['total_error_n']
    else:
        analysis['avg_total_error'] = 0.0

    return analysis

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def tune(weights, analysis, learn_rate=LEARN_RATE):
    """
    Gradually adjust weights based on what's working and what isn't.
    Max change per weight per night = learn_rate (2%).
    """
    new_weights = weights.copy()
    notes = []

    ou_total  = analysis['ou_hits']  + analysis['ou_misses']
    win_total = analysis['win_hits'] + analysis['win_misses']
    ou_acc    = analysis['ou_hits']  / ou_total  if ou_total  > 0 else 0.5
    win_acc   = analysis['win_hits'] / win_total if win_total > 0 else 0.5

    print(f"\n  📊 Analysis (last 7 days):")
    print(f"     O/U  accuracy : {analysis['ou_hits']}/{ou_total} = {ou_acc*100:.1f}%")
    print(f"     WIN  accuracy : {analysis['win_hits']}/{win_total} = {win_acc*100:.1f}%")
    print(f"     Avg total error: {analysis['avg_total_error']:+.1f} pts "
          f"({'model too LOW' if analysis['avg_total_error'] < 0 else 'model too HIGH'})")
    print(f"     Missed OVERs  : {analysis['missed_over']} | Missed UNDERs: {analysis['missed_under']}")

    # ── TUNE total_bias ───────────────────────────────────────────────────
    # If model estimates are consistently too low → push up (positive bias)
    # If consistently too high → push down (negative bias)
    avg_err = analysis['avg_total_error']
    if abs(avg_err) > 3.0:  # only adjust if error is meaningful
        # Each point of avg error → 0.3pt bias adjustment, capped at learn_rate
        bias_adj = clamp(-avg_err * 0.3, -learn_rate * 5, learn_rate * 5)
        old_bias = new_weights['total_bias']
        new_weights['total_bias'] = clamp(old_bias + bias_adj, -8.0, 8.0)
        if abs(new_weights['total_bias'] - old_bias) > 0.01:
            notes.append(f"total_bias: {old_bias:+.2f} → {new_weights['total_bias']:+.2f} "
                         f"(avg error was {avg_err:+.1f}pts)")

    # ── TUNE strong_ou_threshold ──────────────────────────────────────────
    # If Strong O/U picks are hitting well → lower threshold (catch more)
    # If Strong O/U picks are missing → raise threshold (be more selective)
    sou_total = analysis['strong_ou_hits'] + analysis['strong_ou_misses']
    if sou_total >= 3:
        sou_acc = analysis['strong_ou_hits'] / sou_total
        old_thr = new_weights['strong_ou_threshold']
        if sou_acc >= 0.75:
            # Hitting well — lower threshold slightly to catch more games
            new_weights['strong_ou_threshold'] = clamp(old_thr - 0.5, 8.0, 20.0)
            notes.append(f"strong_ou_threshold: {old_thr} → {new_weights['strong_ou_threshold']} "
                         f"(Strong O/U hitting {sou_acc*100:.0f}%)")
        elif sou_acc < 0.50:
            # Missing too much — raise threshold to be more selective
            new_weights['strong_ou_threshold'] = clamp(old_thr + 0.5, 8.0, 20.0)
            notes.append(f"strong_ou_threshold: {old_thr} → {new_weights['strong_ou_threshold']} "
                         f"(Strong O/U only {sou_acc*100:.0f}%)")

    # ── TUNE win model weights ────────────────────────────────────────────
    # If win accuracy is poor, reduce the weight of the worst-performing factor
    # and increase the best-performing one slightly
    if win_total >= 5:
        if win_acc < 0.55:
            # Model is struggling on win picks — boost pythagorean (most reliable)
            old = new_weights['pythagorean']
            new_weights['pythagorean'] = clamp(old + learn_rate * 0.5, 0.15, 0.50)
            # Reduce form slightly (most volatile factor)
            old_f = new_weights['form']
            new_weights['form'] = clamp(old_f - learn_rate * 0.5, 0.05, 0.30)
            notes.append(f"pythagorean: {old:.3f} → {new_weights['pythagorean']:.3f} "
                         f"(win acc low at {win_acc*100:.0f}%)")
            notes.append(f"form: {old_f:.3f} → {new_weights['form']:.3f}")
        elif win_acc >= 0.75:
            # Doing well — boost efficiency matchup (most sophisticated signal)
            old = new_weights['efficiency']
            new_weights['efficiency'] = clamp(old + learn_rate * 0.3, 0.15, 0.50)
            notes.append(f"efficiency: {old:.3f} → {new_weights['efficiency']:.3f} "
                         f"(win acc strong at {win_acc*100:.0f}%)")

        # Re-normalise win weights to sum to ~0.95 (leaving 0.05 for home_adv)
        win_keys = ['pythagorean', 'efficiency', 'four_factors', 'form']
        win_sum  = sum(new_weights[k] for k in win_keys)
        if abs(win_sum - 0.95) > 0.01:
            factor = 0.95 / win_sum
            for k in win_keys:
                new_weights[k] = round(new_weights[k] * factor, 4)

    # ── TUNE home_adv ─────────────────────────────────────────────────────
    # If home teams are consistently over/underperforming picks
    # (simple heuristic — refine later with more data)
    if win_total >= 10:
        # Keep home_adv in a reasonable range
        new_weights['home_adv'] = clamp(new_weights['home_adv'], 0.02, 0.08)

    return new_weights, notes

def print_weight_diff(old, new):
    print("\n  📐 Weight Changes:")
    changed = False
    for k in old:
        if k in new and abs(old[k] - new[k]) > 0.0001:
            changed = True
            arrow = "↑" if new[k] > old[k] else "↓"
            print(f"     {k:<25} {old[k]:.4f} → {new[k]:.4f}  {arrow}")
    if not changed:
        print("     No changes this cycle — model performing well!")

def main():
    print()
    print("═" * 60)
    print("  🧠  NBA ORACLE — SELF-TUNING ENGINE")
    print(f"  📅  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("═" * 60)

    # Load current weights
    weights = load_weights()

    # Load last 7 days of results
    results = load_results(days=7)
    if not results:
        print("\n  ⚠️  No completed results yet — need at least 1 day of data.")
        print("  Run again tomorrow after games complete.\n")
        return

    completed_days = len(results)
    total_games    = sum(len(e.get('predictions',[])) for e in results)
    print(f"\n  📊 Analysing {completed_days} days / {total_games} games...")

    # Analyse what's working and what isn't
    analysis = analyse_misses(results)

    # Compute new weights
    old_weights = weights.copy()
    new_weights, notes = tune(weights, analysis)

    # Show the diff
    print_weight_diff(old_weights, new_weights)

    if notes:
        print("\n  📝 Reasons:")
        for n in notes:
            print(f"     • {n}")

    # Save new weights
    tune_log = load_tune_log()
    version  = len(tune_log) + 1
    save_weights(new_weights, version, notes)

    # Append to tune log for tracking evolution over time
    tune_log.append({
        'date':     datetime.now().strftime('%Y-%m-%d'),
        'version':  version,
        'analysis': {
            'ou_acc':  round(analysis['ou_hits'] / max(analysis['ou_hits']+analysis['ou_misses'],1) * 100, 1),
            'win_acc': round(analysis['win_hits'] / max(analysis['win_hits']+analysis['win_misses'],1) * 100, 1),
            'avg_total_error': round(analysis['avg_total_error'], 2),
        },
        'changes':  notes,
        'weights':  new_weights,
    })
    save_tune_log(tune_log)

    print(f"\n  ✅ Done. Weights v{version} saved.")
    print("  Run nba_predictor.py to use the updated weights.\n")
    print("═" * 60)

if __name__ == '__main__':
    main()
