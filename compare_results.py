#!/usr/bin/env python3
"""
NBA ORACLE — Prediction vs Actual Results Comparison
Feb 22 2026
"""

results = [
    # (away, home, predicted_ou, predicted_line, predicted_pick, pick_conf, actual_away, actual_home)
    ("Cleveland Cavaliers",       "Oklahoma City Thunder",    "UNDER", 232.6, "Oklahoma City Thunder", 60.5, 113, 121),
    ("Brooklyn Nets",             "Atlanta Hawks",            "OVER",  224.9, "Atlanta Hawks",         79.9, 104, 115),
    ("Toronto Raptors",           "Milwaukee Bucks",          "OVER",  226.0, "Milwaukee Bucks",       57.8, 122,  94),
    ("Denver Nuggets",            "Golden State Warriors",    "UNDER", 231.2, "Denver Nuggets",        50.6, 117, 128),
    ("Dallas Mavericks",          "Indiana Pacers",           "OVER",  225.5, "Indiana Pacers",        54.6, 134, 130),
    ("Charlotte Hornets",         "Washington Wizards",       "UNDER", 226.9, "Washington Wizards",    53.9, 129, 112),
    ("Boston Celtics",            "Los Angeles Lakers",       "UNDER", 228.8, "Los Angeles Lakers",    62.8, 111,  89),
    ("Philadelphia 76ers",        "Minnesota Timberwolves",   "UNDER", 230.8, "Minnesota Timberwolves",68.6, 135, 108),
    ("New York Knicks",           "Chicago Bulls",            "UNDER", 230.1, "Chicago Bulls",         57.8, 105,  99),
    ("Portland Trail Blazers",    "Phoenix Suns",             "UNDER", 227.7, "Phoenix Suns",          54.7,  92,  77),
    ("Orlando Magic",             "LA Clippers",              "UNDER", 226.7, "LA Clippers",           54.2, 111, 109),
]

print()
print("=" * 70)
print("  🏀  NBA ORACLE — PREDICTION vs ACTUAL RESULTS")
print("  📅  February 22, 2026")
print("=" * 70)
print()

ou_correct = 0
ou_wrong   = 0
pick_correct = 0
pick_wrong   = 0
total_games  = len(results)

ou_wins   = []
ou_losses = []
pick_wins = []
pick_losses = []

for away, home, pred_ou, ou_line, pred_pick, conf, actual_away, actual_home in results:
    actual_total  = actual_away + actual_home
    actual_ou     = "OVER" if actual_total > ou_line else "UNDER"
    actual_winner = home if actual_home > actual_away else away

    ou_hit   = pred_ou == actual_ou
    pick_hit = pred_pick == actual_winner

    ou_icon   = "✅" if ou_hit   else "❌"
    pick_icon = "✅" if pick_hit else "❌"

    if ou_hit:   ou_correct   += 1; ou_wins.append(f"{away.split()[-1]} @ {home.split()[-1]}")
    else:        ou_wrong     += 1; ou_losses.append(f"{away.split()[-1]} @ {home.split()[-1]} (pred {pred_ou} {ou_line}, actual {actual_total})")
    if pick_hit: pick_correct += 1; pick_wins.append(pred_pick.split()[-1])
    else:        pick_wrong   += 1; pick_losses.append(f"Pred: {pred_pick.split()[-1]} | Actual: {actual_winner.split()[-1]}")

    print(f"  {away.split()[-1]:<12} @ {home.split()[-1]:<18}  Score: {actual_away}-{actual_home} (Total: {actual_total})")
    print(f"    O/U  {ou_icon}  Pred: {pred_ou} {ou_line:<6} | Actual: {actual_ou} {actual_total}")
    print(f"    PICK {pick_icon}  Pred: {pred_pick.split()[-1]:<20} | Actual: {actual_winner.split()[-1]}")
    print()

# ── SUMMARY ──
print("=" * 70)
print("  📊  RESULTS SUMMARY")
print("=" * 70)
print()
print(f"  Over/Under accuracy : {ou_correct}/{total_games} = {ou_correct/total_games*100:.1f}%")
print(f"  Pick accuracy       : {pick_correct}/{total_games} = {pick_correct/total_games*100:.1f}%")
print()

print(f"  ✅ O/U CORRECT ({ou_correct}):")
for w in ou_wins:
    print(f"     • {w}")
print()
print(f"  ❌ O/U WRONG ({ou_wrong}):")
for l in ou_losses:
    print(f"     • {l}")
print()
print(f"  ✅ PICKS CORRECT ({pick_correct}):")
for w in pick_wins:
    print(f"     • {w}")
print()
print(f"  ❌ PICKS WRONG ({pick_wrong}):")
for l in pick_losses:
    print(f"     • {l}")
print()

# ── ANALYSIS ──
print("=" * 70)
print("  🔍  ENGINE ANALYSIS")
print("=" * 70)
print()

ou_pct   = ou_correct / total_games * 100
pick_pct = pick_correct / total_games * 100

if ou_pct >= 70:
    print(f"  O/U Model: 🔥 STRONG ({ou_pct:.1f}%) — Engine is reading totals well")
elif ou_pct >= 60:
    print(f"  O/U Model: ✅ SOLID ({ou_pct:.1f}%) — Promising, needs tuning")
else:
    print(f"  O/U Model: ⚠️  NEEDS WORK ({ou_pct:.1f}%) — O/U lines need calibration")

if pick_pct >= 70:
    print(f"  Pick Model: 🔥 STRONG ({pick_pct:.1f}%) — Win predictions solid")
elif pick_pct >= 60:
    print(f"  Pick Model: ✅ SOLID ({pick_pct:.1f}%) — Good foundation")
else:
    print(f"  Pick Model: ⚠️  NEEDS WORK ({pick_pct:.1f}%) — Win model needs tuning")

print()
print("  KEY FINDINGS:")

# Check if overs were missed
big_overs = [(away, home, a+h, line) for away, home, pred_ou, line, _, _, a, h in results
             if (a+h) > line and pred_ou == 'UNDER']
big_unders = [(away, home, a+h, line) for away, home, pred_ou, line, _, _, a, h in results
              if (a+h) < line and pred_ou == 'OVER']

if big_overs:
    print(f"  • Engine missed {len(big_overs)} OVERs — predicted UNDER but game went high:")
    for away, home, total, line in big_overs:
        print(f"    → {away.split()[-1]} @ {home.split()[-1]}: {total} pts (line was {line})")

if big_unders:
    print(f"  • Engine missed {len(big_unders)} UNDERs — predicted OVER but game stayed low:")
    for away, home, total, line in big_unders:
        print(f"    → {away.split()[-1]} @ {home.split()[-1]}: {total} pts (line was {line})")

print()
print("  TOMORROW'S TUNING:")
print("  • Games with actual total 20+ pts from our line = model needs pace adjustment")
print("  • Will recalibrate O/U lines based on today's data")
print()
print("=" * 70)
print()
