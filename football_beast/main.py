"""
Football Beast - Manual Match Input Version
You input real matches, engine provides predictions
"""

import json
import numpy as np
from datetime import datetime
from typing import List, Dict

from football_beast import FootballBeastPredictor, PredictionFormatter


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("⚽ FOOTBALL BEAST PREDICTION ENGINE")
    print("="*70)
    
    # Initialize predictor
    predictor = FootballBeastPredictor()
    
    # TODAY'S REAL MATCHES - YOU INPUT THESE
    matches = [
        {
            'match_info': {
                'home': input("Home team 1: "),
                'away': input("Away team 1: "),
                'league': input("League 1: "),
                'date': datetime.now().isoformat(),
                'status': 'SCHEDULED'
            },
            'home_team': {
                'goals_for': int(input("Home 1 Goals For (season): ")),
                'goals_against': int(input("Home 1 Goals Against: ")),
                'shots_on_target': int(input("Home 1 Shots On Target: ")),
                'shots_total': int(input("Home 1 Total Shots: ")),
                'corners_for': int(input("Home 1 Corners: ")),
                'matches_played': int(input("Home 1 Matches Played: ")),
                'clean_sheets': int(input("Home 1 Clean Sheets: ")),
                'tackles': int(input("Home 1 Tackles: ")),
                'interceptions': int(input("Home 1 Interceptions: ")),
                'possession_pct': float(input("Home 1 Possession %: ")) / 100,
                'passes_per_game': float(input("Home 1 Passes Per Game: ")),
                'last_10_wins': int(input("Home 1 Wins Last 10: ")),
                'last_10_draws': int(input("Home 1 Draws Last 10: ")),
                'last_10_losses': int(input("Home 1 Losses Last 10: "))
            },
            'away_team': {
                'goals_for': int(input("Away 1 Goals For (season): ")),
                'goals_against': int(input("Away 1 Goals Against: ")),
                'shots_on_target': int(input("Away 1 Shots On Target: ")),
                'shots_total': int(input("Away 1 Total Shots: ")),
                'corners_for': int(input("Away 1 Corners: ")),
                'matches_played': int(input("Away 1 Matches Played: ")),
                'clean_sheets': int(input("Away 1 Clean Sheets: ")),
                'tackles': int(input("Away 1 Tackles: ")),
                'interceptions': int(input("Away 1 Interceptions: ")),
                'possession_pct': float(input("Away 1 Possession %: ")) / 100,
                'passes_per_game': float(input("Away 1 Passes Per Game: ")),
                'last_10_wins': int(input("Away 1 Wins Last 10: ")),
                'last_10_draws': int(input("Away 1 Draws Last 10: ")),
                'last_10_losses': int(input("Away 1 Losses Last 10: "))
            }
        }
    ]
    
    if len(matches) == 0:
        print("❌ No matches provided.")
        return
    
    print(f"\n🎯 Making predictions for {len(matches)} match...")
    
    # Make predictions
    predictions = predictor.batch_predict(matches)
    
    # Display predictions
    print("\n" + "="*70)
    print("📊 FOOTBALL BEAST PICKS")
    print("="*70 + "\n")
    
    for i, pred in enumerate(predictions, 1):
        home = pred['match'].get('home', 'Home')
        away = pred['match'].get('away', 'Away')
        league = pred['match'].get('league', '')
        market = pred['market_name']
        pick = pred['prediction']
        confidence = pred['confidence']
        conf_level = pred['confidence_level']
        
        print(f"{away} @ {home} ({league})")
        print(f"   🎯 Market: {market}")
        print(f"   💡 Pick:   {pick}")
        print(f"   📊 Confidence: {confidence:.1%} {conf_level}\n")
    
    # Generate report
    report = predictor.generate_report(predictions, 'predictions.json')
    
    # Save all predictions
    with open('all_predictions.json', 'w') as f:
        json.dump(predictions, f, indent=2)
    
    print("="*70)
    print("✅ Predictions saved to all_predictions.json")
    print("="*70)


if __name__ == '__main__':
    main()