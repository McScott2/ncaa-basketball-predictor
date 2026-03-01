"""
NCAA Basketball Prediction Engine - Quick Start
Run this script to train and make predictions
"""

import json
import pandas as pd
from datetime import datetime
from ncaa_predictor import NCAABasketballPredictor, PredictionFormatter

def load_sample_games():
    """Load sample game data for demonstration"""
    sample_games = [
        {
            'team_id': 'DUKE',
            'opponent_id': 'UNC',
            'team_stats': {
                'PTS': 75, 'FGM': 28, 'FGA': 65, '3PM': 8, '3PA': 22,
                'FTA': 14, 'FTM': 12, 'ORB': 8, 'DRB': 28, 'TRB': 36,
                'AST': 15, 'TO': 12, 'STL': 7, 'BLK': 4
            },
            'opponent_stats': {
                'PTS': 68, 'FGM': 25, 'FGA': 62, '3PM': 7, '3PA': 20,
                'FTA': 12, 'FTM': 10, 'ORB': 6, 'DRB': 25, 'TRB': 31,
                'AST': 13, 'TO': 14, 'STL': 6, 'BLK': 3
            },
            'recent_games': [
                {'result': 'W', 'PTS': 72, 'OPP_PTS': 65},
                {'result': 'W', 'PTS': 68, 'OPP_PTS': 60},
                {'result': 'L', 'PTS': 64, 'OPP_PTS': 71},
                {'result': 'W', 'PTS': 76, 'OPP_PTS': 62},
                {'result': 'W', 'PTS': 70, 'OPP_PTS': 68},
            ],
            'result': 'W',
            'game_info': {'matchup': 'Duke vs UNC', 'date': '2026-02-21'}
        },
        {
            'team_id': 'KANSAS',
            'opponent_id': 'OKLAHOMA',
            'team_stats': {
                'PTS': 82, 'FGM': 30, 'FGA': 67, '3PM': 9, '3PA': 23,
                'FTA': 15, 'FTM': 13, 'ORB': 9, 'DRB': 30, 'TRB': 39,
                'AST': 17, 'TO': 10, 'STL': 8, 'BLK': 5
            },
            'opponent_stats': {
                'PTS': 75, 'FGM': 27, 'FGA': 64, '3PM': 8, '3PA': 21,
                'FTA': 13, 'FTM': 11, 'ORB': 7, 'DRB': 26, 'TRB': 33,
                'AST': 14, 'TO': 13, 'STL': 6, 'BLK': 4
            },
            'recent_games': [
                {'result': 'W', 'PTS': 78, 'OPP_PTS': 72},
                {'result': 'W', 'PTS': 80, 'OPP_PTS': 68},
                {'result': 'W', 'PTS': 74, 'OPP_PTS': 64},
                {'result': 'L', 'PTS': 69, 'OPP_PTS': 76},
                {'result': 'W', 'PTS': 81, 'OPP_PTS': 70},
            ],
            'result': 'W',
            'game_info': {'matchup': 'Kansas vs Oklahoma', 'date': '2026-02-21'}
        },
        {
            'team_id': 'KENTUCKY',
            'opponent_id': 'TENNESSEE',
            'team_stats': {
                'PTS': 71, 'FGM': 26, 'FGA': 61, '3PM': 7, '3PA': 19,
                'FTA': 16, 'FTM': 12, 'ORB': 10, 'DRB': 26, 'TRB': 36,
                'AST': 13, 'TO': 13, 'STL': 6, 'BLK': 5
            },
            'opponent_stats': {
                'PTS': 74, 'FGM': 27, 'FGA': 63, '3PM': 8, '3PA': 21,
                'FTA': 14, 'FTM': 12, 'ORB': 7, 'DRB': 27, 'TRB': 34,
                'AST': 15, 'TO': 11, 'STL': 7, 'BLK': 4
            },
            'recent_games': [
                {'result': 'L', 'PTS': 68, 'OPP_PTS': 73},
                {'result': 'W', 'PTS': 75, 'OPP_PTS': 70},
                {'result': 'W', 'PTS': 72, 'OPP_PTS': 66},
                {'result': 'L', 'PTS': 65, 'OPP_PTS': 78},
                {'result': 'W', 'PTS': 80, 'OPP_PTS': 72},
            ],
            'result': 'L',
            'game_info': {'matchup': 'Kentucky vs Tennessee', 'date': '2026-02-19'}
        },
        {
            'team_id': 'GONZAGA',
            'opponent_id': 'SAINTMARYS',
            'team_stats': {
                'PTS': 88, 'FGM': 33, 'FGA': 66, '3PM': 11, '3PA': 25,
                'FTA': 17, 'FTM': 11, 'ORB': 10, 'DRB': 32, 'TRB': 42,
                'AST': 20, 'TO': 8, 'STL': 9, 'BLK': 6
            },
            'opponent_stats': {
                'PTS': 72, 'FGM': 26, 'FGA': 60, '3PM': 7, '3PA': 20,
                'FTA': 15, 'FTM': 13, 'ORB': 6, 'DRB': 24, 'TRB': 30,
                'AST': 13, 'TO': 14, 'STL': 5, 'BLK': 3
            },
            'recent_games': [
                {'result': 'W', 'PTS': 90, 'OPP_PTS': 74},
                {'result': 'W', 'PTS': 85, 'OPP_PTS': 70},
                {'result': 'W', 'PTS': 92, 'OPP_PTS': 68},
                {'result': 'W', 'PTS': 87, 'OPP_PTS': 75},
                {'result': 'W', 'PTS': 84, 'OPP_PTS': 69},
            ],
            'result': 'W',
            'game_info': {'matchup': 'Gonzaga vs Saint Marys', 'date': '2026-02-18'}
        },
        {
            'team_id': 'HOUSTON',
            'opponent_id': 'MEMPHIS',
            'team_stats': {
                'PTS': 69, 'FGM': 25, 'FGA': 59, '3PM': 6, '3PA': 17,
                'FTA': 18, 'FTM': 13, 'ORB': 11, 'DRB': 28, 'TRB': 39,
                'AST': 12, 'TO': 10, 'STL': 10, 'BLK': 7
            },
            'opponent_stats': {
                'PTS': 62, 'FGM': 22, 'FGA': 57, '3PM': 5, '3PA': 16,
                'FTA': 16, 'FTM': 13, 'ORB': 8, 'DRB': 25, 'TRB': 33,
                'AST': 11, 'TO': 14, 'STL': 7, 'BLK': 4
            },
            'recent_games': [
                {'result': 'W', 'PTS': 72, 'OPP_PTS': 58},
                {'result': 'W', 'PTS': 65, 'OPP_PTS': 55},
                {'result': 'W', 'PTS': 70, 'OPP_PTS': 61},
                {'result': 'W', 'PTS': 68, 'OPP_PTS': 59},
                {'result': 'L', 'PTS': 63, 'OPP_PTS': 67},
            ],
            'result': 'W',
            'game_info': {'matchup': 'Houston vs Memphis', 'date': '2026-02-17'}
        },
    ]

    # Expand dataset with variations for better training
    expanded = []
    for i, game in enumerate(sample_games * 10):
        import random
        variation = {
            'team_id': game['team_id'] + str(i),
            'opponent_id': game['opponent_id'] + str(i),
            'team_stats': {k: max(1, v + random.randint(-5, 5)) for k, v in game['team_stats'].items()},
            'opponent_stats': {k: max(1, v + random.randint(-5, 5)) for k, v in game['opponent_stats'].items()},
            'recent_games': game['recent_games'],
            'result': game['result'],
            'game_info': game['game_info']
        }
        expanded.append(variation)

    return expanded


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("🏀 NCAA BASKETBALL PREDICTION ENGINE")
    print("="*60)

    # Initialize predictor
    print("\n📊 Initializing prediction system...")
    predictor = NCAABasketballPredictor()

    # Load sample data
    print("📂 Loading game data...")
    historical_games = load_sample_games()
    print(f"   ✅ Loaded {len(historical_games)} games")

    # Prepare training data
    print("\n🔧 Preparing features...")
    X_train, y_train = predictor.prepare_training_data(historical_games)

    # Train models
    print("\n🎯 Training ensemble of models...")
    print("   This may take a few minutes...")
    metrics = predictor.train_models(X_train, y_train, test_size=0.2)

    # Save models
    print("\n💾 Saving trained models...")
    predictor.save_models()

    # Make predictions on sample games
    print("\n" + "="*60)
    print("🎲 MAKING PREDICTIONS")
    print("="*60)

    test_games = [
        {
            'team_id': 'TEXAS',
            'opponent_id': 'OKSTATE',
            'team_stats': {
                'PTS': 77, 'FGM': 29, 'FGA': 66, '3PM': 8, '3PA': 22,
                'FTA': 13, 'FTM': 11, 'ORB': 8, 'DRB': 27, 'TRB': 35,
                'AST': 14, 'TO': 11, 'STL': 7, 'BLK': 4
            },
            'opponent_stats': {
                'PTS': 70, 'FGM': 26, 'FGA': 63, '3PM': 7, '3PA': 21,
                'FTA': 11, 'FTM': 9, 'ORB': 6, 'DRB': 24, 'TRB': 30,
                'AST': 12, 'TO': 13, 'STL': 6, 'BLK': 3
            },
            'recent_games': [
                {'result': 'W', 'PTS': 75, 'OPP_PTS': 68},
                {'result': 'W', 'PTS': 71, 'OPP_PTS': 65},
                {'result': 'L', 'PTS': 66, 'OPP_PTS': 72},
            ],
            'game_info': {'matchup': 'Texas vs Oklahoma State', 'date': '2026-02-21'}
        },
        {
            'team_id': 'UCLA',
            'opponent_id': 'STANFORD',
            'team_stats': {
                'PTS': 85, 'FGM': 31, 'FGA': 68, '3PM': 10, '3PA': 24,
                'FTA': 16, 'FTM': 14, 'ORB': 9, 'DRB': 31, 'TRB': 40,
                'AST': 18, 'TO': 9, 'STL': 8, 'BLK': 5
            },
            'opponent_stats': {
                'PTS': 77, 'FGM': 28, 'FGA': 65, '3PM': 8, '3PA': 22,
                'FTA': 14, 'FTM': 12, 'ORB': 7, 'DRB': 27, 'TRB': 34,
                'AST': 15, 'TO': 12, 'STL': 7, 'BLK': 4
            },
            'recent_games': [
                {'result': 'W', 'PTS': 82, 'OPP_PTS': 75},
                {'result': 'W', 'PTS': 79, 'OPP_PTS': 70},
                {'result': 'W', 'PTS': 81, 'OPP_PTS': 72},
            ],
            'game_info': {'matchup': 'UCLA vs Stanford', 'date': '2026-02-21'}
        }
    ]

    # Get predictions
    predictions = predictor.batch_predict(test_games)

    # Display results
    print("\n" + "="*60)
    print("📋 PREDICTION RESULTS")
    print("="*60)

    for i, pred in enumerate(predictions, 1):
        game_info = pred.get('game_info', {})
        matchup = game_info.get('matchup', 'Unknown')
        prediction = 'WIN ✅' if pred.get('prediction', 0.5) > 0.5 else 'LOSS ❌'
        confidence = pred.get('confidence', 0)
        agreement = pred.get('agreement', 0)

        print(f"\n🎯 Game {i}: {matchup}")
        print(f"   Prediction:  {prediction}")
        print(f"   Confidence:  {confidence:.1%}")
        print(f"   Agreement:   {agreement:.1%}")

        individual = pred.get('individual_models', {})
        if individual:
            print(f"   Model Breakdown:")
            for model_name, model_pred in individual.items():
                model_pred_text = 'WIN' if model_pred > 0.5 else 'LOSS'
                print(f"      • {model_name:18} {model_pred:.1%} ({model_pred_text})")

    # Over/Under predictions
    print("\n" + "="*60)
    print("📊 OVER/UNDER PREDICTIONS")
    print("="*60)

    ou_pred = predictor.predict_over_under(test_games[0], point_total=152.5)
    print(f"\nGame 1 Total Line: {ou_pred.get('point_total', 0)}")
    print(f"Estimated Total:   {ou_pred.get('estimated_total', 0):.0f}")
    print(f"Prediction:        {ou_pred.get('prediction', 'UNKNOWN')}")
    print(f"Probability:       {ou_pred.get('probability', 0):.1%}")
    print(f"Edge:              {ou_pred.get('edge', 0):.1%}")

    # Generate report
    print("\n" + "="*60)
    print("📈 GENERATING REPORT")
    print("="*60)
    report = predictor.generate_report(
        predictions,
        output_file='predictions_report.json'
    )

    print(f"\n✅ Report generated!")
    print(f"   Total predictions: {report['total_predictions']}")
    print(f"   Avg confidence: {report['summary_stats']['avg_confidence']:.1%}")
    print(f"   High confidence picks: {len(report['high_confidence_picks'])}")
    print(f"   Consensus predictions: {len(report['consensus_predictions'])}")

    print("\n" + "="*60)
    print("🎉 PREDICTION ENGINE READY FOR PRODUCTION!")
    print("="*60)
    print("\n📚 Next steps:")
    print("   1. Connect to real data sources (ESPN, official APIs)")
    print("   2. Deploy to production server")
    print("   3. Monitor prediction accuracy")
    print("   4. Continuously retrain with new data")
    print("   5. Deploy web interface for live predictions")
    print("\n💡 Use predictor.predict_game() for individual games")
    print("💡 Use predictor.batch_predict() for multiple games")
    print("💡 Use predictor.predict_over_under() for O/U bets\n")


if __name__ == "__main__":
    main()