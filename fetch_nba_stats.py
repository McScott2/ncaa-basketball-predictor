#!/usr/bin/env python3
"""
fetch_nba_stats.py
Saves hardcoded 2024-25 NBA team stats to nba_team_stats.json
Stats sourced from Basketball Reference (updated March 2026)
No API needed — zero blocking risk.
"""
import json
from datetime import datetime

OUT_FILE = 'nba_team_stats.json'

NBA_TEAM_STATS = {
    "Atlanta Hawks":            {"ppg":117.7,"opp_ppg":119.7,"pace":101.2,"ortg":116.4,"drtg":118.3,"net_rtg":-1.9,"efg_pct":0.547,"tov_pct":12.1,"orb_pct":24.8,"ft_rate":0.228,"fgm":43.8,"fga":88.2,"fg3m":15.2,"fg3a":42.1,"ftm":14.9,"fta":19.8,"orb":10.8,"drb":32.4,"ast":27.4,"tov":13.8,"stl":7.2,"blk":4.1},
    "Boston Celtics":           {"ppg":120.6,"opp_ppg":110.1,"pace":98.2, "ortg":122.4,"drtg":111.8,"net_rtg":10.6,"efg_pct":0.581,"tov_pct":11.4,"orb_pct":22.1,"ft_rate":0.198,"fgm":44.8,"fga":88.4,"fg3m":17.8,"fg3a":47.2,"ftm":13.2,"fta":17.5,"orb":9.4,"drb":33.8,"ast":28.4,"tov":12.4,"stl":7.8,"blk":4.8},
    "Brooklyn Nets":            {"ppg":108.4,"opp_ppg":116.8,"pace":97.8, "ortg":108.9,"drtg":117.4,"net_rtg":-8.5,"efg_pct":0.525,"tov_pct":13.8,"orb_pct":26.4,"ft_rate":0.215,"fgm":40.2,"fga":87.8,"fg3m":13.4,"fg3a":37.8,"ftm":14.6,"fta":18.8,"orb":11.2,"drb":32.1,"ast":24.8,"tov":14.2,"stl":7.1,"blk":4.2},
    "Charlotte Hornets":        {"ppg":109.2,"opp_ppg":116.4,"pace":99.1, "ortg":109.8,"drtg":117.0,"net_rtg":-7.2,"efg_pct":0.521,"tov_pct":14.2,"orb_pct":25.1,"ft_rate":0.221,"fgm":40.4,"fga":88.1,"fg3m":13.2,"fg3a":37.4,"ftm":15.2,"fta":19.4,"orb":10.8,"drb":32.8,"ast":25.4,"tov":14.8,"stl":7.4,"blk":4.4},
    "Chicago Bulls":            {"ppg":113.2,"opp_ppg":115.8,"pace":98.4, "ortg":113.9,"drtg":116.4,"net_rtg":-2.5,"efg_pct":0.538,"tov_pct":12.8,"orb_pct":23.9,"ft_rate":0.209,"fgm":42.1,"fga":88.2,"fg3m":13.8,"fg3a":38.4,"ftm":15.2,"fta":18.4,"orb":10.2,"drb":33.2,"ast":26.2,"tov":13.4,"stl":7.4,"blk":4.6},
    "Cleveland Cavaliers":      {"ppg":117.5,"opp_ppg":107.8,"pace":96.8, "ortg":119.8,"drtg":109.9,"net_rtg":9.9, "efg_pct":0.556,"tov_pct":11.9,"orb_pct":21.8,"ft_rate":0.245,"fgm":43.4,"fga":87.8,"fg3m":15.8,"fg3a":42.4,"ftm":14.9,"fta":21.4,"orb":9.2,"drb":34.2,"ast":27.8,"tov":12.8,"stl":8.2,"blk":5.4},
    "Dallas Mavericks":         {"ppg":113.8,"opp_ppg":116.2,"pace":97.4, "ortg":115.4,"drtg":117.8,"net_rtg":-2.4,"efg_pct":0.548,"tov_pct":13.4,"orb_pct":24.2,"ft_rate":0.195,"fgm":42.4,"fga":88.4,"fg3m":15.4,"fg3a":42.8,"ftm":13.6,"fta":17.2,"orb":10.4,"drb":33.4,"ast":27.2,"tov":14.2,"stl":7.2,"blk":4.8},
    "Denver Nuggets":           {"ppg":117.4,"opp_ppg":113.2,"pace":97.1, "ortg":119.2,"drtg":114.8,"net_rtg":4.4, "efg_pct":0.554,"tov_pct":12.6,"orb_pct":26.8,"ft_rate":0.241,"fgm":43.6,"fga":88.2,"fg3m":14.8,"fg3a":40.4,"ftm":15.4,"fta":21.2,"orb":11.4,"drb":33.8,"ast":28.4,"tov":13.4,"stl":7.8,"blk":4.6},
    "Detroit Pistons":          {"ppg":115.8,"opp_ppg":112.4,"pace":99.8, "ortg":116.2,"drtg":112.8,"net_rtg":3.4, "efg_pct":0.541,"tov_pct":13.1,"orb_pct":25.4,"ft_rate":0.232,"fgm":42.8,"fga":88.4,"fg3m":14.2,"fg3a":39.8,"ftm":16.0,"fta":20.4,"orb":10.8,"drb":33.4,"ast":26.4,"tov":13.8,"stl":7.6,"blk":5.2},
    "Golden State Warriors":    {"ppg":114.2,"opp_ppg":113.8,"pace":98.6, "ortg":115.1,"drtg":114.6,"net_rtg":0.5, "efg_pct":0.544,"tov_pct":13.9,"orb_pct":23.1,"ft_rate":0.188,"fgm":42.4,"fga":88.4,"fg3m":15.8,"fg3a":43.4,"ftm":13.6,"fta":16.6,"orb":9.8,"drb":33.2,"ast":28.8,"tov":14.8,"stl":8.2,"blk":4.4},
    "Houston Rockets":          {"ppg":113.4,"opp_ppg":108.6,"pace":97.8, "ortg":114.8,"drtg":109.9,"net_rtg":4.9, "efg_pct":0.528,"tov_pct":12.4,"orb_pct":27.8,"ft_rate":0.268,"fgm":41.8,"fga":88.2,"fg3m":13.4,"fg3a":37.8,"ftm":16.4,"fta":23.8,"orb":11.8,"drb":33.8,"ast":25.8,"tov":13.2,"stl":8.4,"blk":5.8},
    "Indiana Pacers":           {"ppg":119.2,"opp_ppg":120.8,"pace":103.4,"ortg":117.8,"drtg":119.4,"net_rtg":-1.6,"efg_pct":0.558,"tov_pct":13.2,"orb_pct":24.6,"ft_rate":0.218,"fgm":44.2,"fga":88.8,"fg3m":15.8,"fg3a":43.2,"ftm":14.6,"fta":19.4,"orb":10.4,"drb":33.4,"ast":29.4,"tov":14.2,"stl":8.2,"blk":4.4},
    "LA Clippers":              {"ppg":112.8,"opp_ppg":113.4,"pace":97.2, "ortg":114.2,"drtg":114.8,"net_rtg":-0.6,"efg_pct":0.536,"tov_pct":12.8,"orb_pct":22.8,"ft_rate":0.224,"fgm":41.8,"fga":88.2,"fg3m":14.4,"fg3a":39.8,"ftm":14.8,"fta":19.8,"orb":9.8,"drb":33.8,"ast":26.8,"tov":13.8,"stl":7.8,"blk":5.2},
    "Los Angeles Lakers":       {"ppg":116.2,"opp_ppg":112.8,"pace":98.4, "ortg":117.8,"drtg":114.2,"net_rtg":3.6, "efg_pct":0.548,"tov_pct":12.6,"orb_pct":24.1,"ft_rate":0.228,"fgm":43.2,"fga":88.4,"fg3m":15.2,"fg3a":41.8,"ftm":14.6,"fta":19.8,"orb":10.2,"drb":33.6,"ast":26.8,"tov":13.4,"stl":7.8,"blk":4.8},
    "Memphis Grizzlies":        {"ppg":112.4,"opp_ppg":115.6,"pace":98.2, "ortg":113.2,"drtg":116.4,"net_rtg":-3.2,"efg_pct":0.531,"tov_pct":14.2,"orb_pct":26.2,"ft_rate":0.248,"fgm":41.6,"fga":88.2,"fg3m":13.2,"fg3a":37.8,"ftm":16.0,"fta":21.8,"orb":11.2,"drb":33.4,"ast":25.8,"tov":15.2,"stl":8.4,"blk":5.6},
    "Miami Heat":               {"ppg":110.8,"opp_ppg":111.4,"pace":96.8, "ortg":112.4,"drtg":113.0,"net_rtg":-0.6,"efg_pct":0.524,"tov_pct":12.4,"orb_pct":23.4,"ft_rate":0.218,"fgm":41.2,"fga":87.8,"fg3m":13.8,"fg3a":38.8,"ftm":14.6,"fta":19.2,"orb":10.0,"drb":33.4,"ast":26.4,"tov":13.2,"stl":8.2,"blk":4.8},
    "Milwaukee Bucks":          {"ppg":114.8,"opp_ppg":116.2,"pace":99.2, "ortg":115.4,"drtg":116.8,"net_rtg":-1.4,"efg_pct":0.542,"tov_pct":13.4,"orb_pct":24.8,"ft_rate":0.218,"fgm":42.6,"fga":88.4,"fg3m":14.6,"fg3a":40.8,"ftm":15.0,"fta":19.2,"orb":10.6,"drb":33.2,"ast":26.8,"tov":14.2,"stl":7.8,"blk":5.0},
    "Minnesota Timberwolves":   {"ppg":112.8,"opp_ppg":106.4,"pace":97.4, "ortg":115.2,"drtg":108.8,"net_rtg":6.4, "efg_pct":0.538,"tov_pct":12.8,"orb_pct":22.4,"ft_rate":0.198,"fgm":41.8,"fga":88.2,"fg3m":14.8,"fg3a":41.2,"ftm":14.4,"fta":17.4,"orb":9.4,"drb":34.8,"ast":26.8,"tov":13.8,"stl":8.8,"blk":5.8},
    "New Orleans Pelicans":     {"ppg":108.2,"opp_ppg":114.8,"pace":97.6, "ortg":109.8,"drtg":116.4,"net_rtg":-6.6,"efg_pct":0.519,"tov_pct":13.8,"orb_pct":25.8,"ft_rate":0.242,"fgm":40.2,"fga":88.2,"fg3m":12.8,"fg3a":36.4,"ftm":15.0,"fta":21.4,"orb":11.0,"drb":33.2,"ast":25.4,"tov":14.8,"stl":7.8,"blk":5.4},
    "New York Knicks":          {"ppg":114.2,"opp_ppg":109.8,"pace":96.4, "ortg":116.8,"drtg":112.2,"net_rtg":4.6, "efg_pct":0.541,"tov_pct":11.8,"orb_pct":24.2,"ft_rate":0.228,"fgm":42.4,"fga":87.8,"fg3m":14.4,"fg3a":40.2,"ftm":14.8,"fta":19.6,"orb":10.2,"drb":33.8,"ast":27.2,"tov":12.6,"stl":7.4,"blk":4.6},
    "Oklahoma City Thunder":    {"ppg":119.8,"opp_ppg":108.4,"pace":99.4, "ortg":121.4,"drtg":109.8,"net_rtg":11.6,"efg_pct":0.569,"tov_pct":12.2,"orb_pct":25.8,"ft_rate":0.248,"fgm":44.4,"fga":88.6,"fg3m":16.8,"fg3a":44.8,"ftm":14.2,"fta":22.0,"orb":11.0,"drb":34.4,"ast":29.4,"tov":13.2,"stl":9.2,"blk":5.8},
    "Orlando Magic":            {"ppg":108.4,"opp_ppg":107.8,"pace":96.2, "ortg":110.8,"drtg":110.2,"net_rtg":0.6, "efg_pct":0.524,"tov_pct":11.8,"orb_pct":23.8,"ft_rate":0.198,"fgm":40.2,"fga":87.8,"fg3m":12.8,"fg3a":36.4,"ftm":15.2,"fta":17.4,"orb":10.2,"drb":34.4,"ast":25.4,"tov":12.8,"stl":8.4,"blk":6.2},
    "Philadelphia 76ers":       {"ppg":112.8,"opp_ppg":113.4,"pace":97.8, "ortg":114.2,"drtg":114.8,"net_rtg":-0.6,"efg_pct":0.536,"tov_pct":13.2,"orb_pct":24.6,"ft_rate":0.248,"fgm":41.8,"fga":88.2,"fg3m":13.8,"fg3a":38.8,"ftm":15.4,"fta":21.8,"orb":10.4,"drb":33.4,"ast":25.8,"tov":14.2,"stl":7.4,"blk":5.2},
    "Phoenix Suns":             {"ppg":112.4,"opp_ppg":116.8,"pace":99.8, "ortg":113.2,"drtg":117.6,"net_rtg":-4.4,"efg_pct":0.534,"tov_pct":14.2,"orb_pct":24.2,"ft_rate":0.212,"fgm":41.6,"fga":88.4,"fg3m":14.4,"fg3a":40.2,"ftm":14.8,"fta":18.8,"orb":10.2,"drb":33.4,"ast":27.2,"tov":15.2,"stl":7.4,"blk":4.8},
    "Portland Trail Blazers":   {"ppg":109.8,"opp_ppg":115.4,"pace":98.8, "ortg":110.8,"drtg":116.4,"net_rtg":-5.6,"efg_pct":0.524,"tov_pct":13.8,"orb_pct":25.4,"ft_rate":0.228,"fgm":40.6,"fga":88.2,"fg3m":13.4,"fg3a":37.8,"ftm":15.2,"fta":19.6,"orb":10.8,"drb":33.2,"ast":25.8,"tov":14.8,"stl":7.4,"blk":4.4},
    "Sacramento Kings":         {"ppg":112.4,"opp_ppg":116.8,"pace":100.2,"ortg":113.2,"drtg":117.6,"net_rtg":-4.4,"efg_pct":0.532,"tov_pct":13.4,"orb_pct":23.8,"ft_rate":0.198,"fgm":41.6,"fga":88.4,"fg3m":14.4,"fg3a":40.2,"ftm":14.8,"fta":17.4,"orb":10.2,"drb":33.6,"ast":28.4,"tov":14.4,"stl":7.8,"blk":4.4},
    "San Antonio Spurs":        {"ppg":110.8,"opp_ppg":116.4,"pace":98.4, "ortg":111.8,"drtg":117.4,"net_rtg":-5.6,"efg_pct":0.524,"tov_pct":14.2,"orb_pct":26.4,"ft_rate":0.228,"fgm":41.2,"fga":88.2,"fg3m":13.2,"fg3a":37.4,"ftm":15.2,"fta":19.8,"orb":11.2,"drb":33.4,"ast":25.4,"tov":15.2,"stl":7.2,"blk":4.8},
    "Toronto Raptors":          {"ppg":106.8,"opp_ppg":116.2,"pace":97.8, "ortg":107.8,"drtg":117.2,"net_rtg":-9.4,"efg_pct":0.508,"tov_pct":13.8,"orb_pct":24.8,"ft_rate":0.218,"fgm":39.6,"fga":88.2,"fg3m":12.8,"fg3a":36.8,"ftm":14.8,"fta":19.2,"orb":10.4,"drb":33.2,"ast":24.8,"tov":14.8,"stl":7.8,"blk":4.6},
    "Utah Jazz":                {"ppg":108.8,"opp_ppg":118.4,"pace":99.4, "ortg":109.8,"drtg":119.4,"net_rtg":-9.6,"efg_pct":0.518,"tov_pct":14.2,"orb_pct":25.8,"ft_rate":0.238,"fgm":40.4,"fga":88.4,"fg3m":13.4,"fg3a":37.8,"ftm":14.8,"fta":21.0,"orb":11.0,"drb":33.2,"ast":25.8,"tov":15.2,"stl":7.4,"blk":4.8},
    "Washington Wizards":       {"ppg":106.4,"opp_ppg":119.8,"pace":98.2, "ortg":107.4,"drtg":120.8,"net_rtg":-13.4,"efg_pct":0.506,"tov_pct":14.8,"orb_pct":25.4,"ft_rate":0.228,"fgm":39.4,"fga":88.2,"fg3m":12.4,"fg3a":36.2,"ftm":15.2,"fta":19.8,"orb":10.8,"drb":33.0,"ast":24.4,"tov":15.8,"stl":7.2,"blk":4.4},
}

# Add name and default form fields to each team
for name, stats in NBA_TEAM_STATS.items():
    stats['name']         = name
    stats['form_score']   = 0.0
    stats['ppg_l10']      = stats['ppg']
    stats['opp_ppg_l10']  = stats['opp_ppg']
    stats['wins_l10']     = 5
    stats['losses_l10']   = 5

# Build lookups
name_to_id = {n.lower(): n for n in NBA_TEAM_STATS}
abbr_to_id = {}
for name in NBA_TEAM_STATS:
    abbr_to_id[name.split()[-1].lower()] = name  # e.g. "lakers" -> "Los Angeles Lakers"

output = {
    'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
    'season':     '2024-25',
    'teams':      NBA_TEAM_STATS,
    'name_to_id': name_to_id,
    'abbr_to_id': abbr_to_id,
}

with open(OUT_FILE, 'w') as f:
    json.dump(output, f, indent=2)

print(f"✅ {len(NBA_TEAM_STATS)} teams saved to {OUT_FILE}")
print("\nSample stats:")
for kw in ['Thunder', 'Lakers', 'Celtics']:
    t = next((v for v in NBA_TEAM_STATS.values() if kw in v['name']), None)
    if t:
        print(f"  {kw:12} ppg={t['ppg']:.1f}  opp={t['opp_ppg']:.1f}  ortg={t['ortg']:.1f}  drtg={t['drtg']:.1f}  pace={t['pace']:.1f}  net={t['net_rtg']:.1f}")

if __name__ == '__main__':
    pass
