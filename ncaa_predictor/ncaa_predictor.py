"""
NCAA Basketball Prediction Engine
Complete ML system for making predictions on college basketball games
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
import warnings
from typing import Dict, List, Tuple

from config import (
    MODEL_CONFIG, FEATURE_CONFIG, PREDICTION_CONFIG,
    DATA_CONFIG, ensure_directories
)
from data_processing import BasketballFeatureEngineering, DataValidator, FeatureSelector
from models import EnsemblePredictor, ModelValidator

warnings.filterwarnings('ignore')


class NCAABasketballPredictor:
    """
    Main NCAA Basketball Prediction Engine
    Handles data preprocessing, model training, and predictions
    """
    
    def __init__(self, config=None):
        self.config = config or {
            'model_config': MODEL_CONFIG,
            'feature_config': FEATURE_CONFIG,
            'prediction_config': PREDICTION_CONFIG,
            'data_config': DATA_CONFIG
        }
        
        self.ensemble = None
        self.feature_engineer = BasketballFeatureEngineering(FEATURE_CONFIG)
        self.validator = DataValidator()
        self.model_validator = ModelValidator()
        self.training_history = []
        self.prediction_cache = {}
        
        ensure_directories()
        
    def prepare_training_data(self, games_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare training data from game records
        """
        print("📊 Preparing training data...")
        
        features_list = []
        targets = []
        
        for game in games_data:
            # Validate game data
            is_valid, message = self.validator.validate_game_data(game)
            if not is_valid and False:
                print(f"  ⚠️  Skipping invalid game: {message}")
                continue
            
            # Engineer features
            team_stats = self.validator.clean_statistics(game.get('team_stats', {}))
            opponent_stats = self.validator.clean_statistics(game.get('opponent_stats', {}))
            recent_games = game.get('recent_games', None)
            
            features = self.feature_engineer.engineer_features(
                team_stats, opponent_stats, recent_games
            )
            
            # Determine target
            target = 1 if game.get('result') == 'W' else 0
            
            features_list.append(features)
            targets.append(target)
        
        X = self.feature_engineer.prepare_features_for_training(
            features_list, target_var='result'
        )
        y = pd.Series(targets)
        
        print(f"✅ Prepared {len(X)} games for training")
        print(f"  Feature dimensions: {X.shape}")
        print(f"  Class distribution: {y.value_counts().to_dict()}")
        
        return X, y
    
    def train_models(self, X: pd.DataFrame, y: pd.Series, test_size=0.2):
        """
        Train ensemble of models
        """
        print("\n🎯 Training Ensemble Prediction Models...")
        
        from sklearn.model_selection import train_test_split
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Train ensemble
        self.ensemble = EnsemblePredictor(MODEL_CONFIG)
        self.ensemble.fit(X_train, y_train, X_val, y_val)
        
        # Validate
        val_predictions, val_confidence = self.ensemble.predict(X_val)
        metrics = self.model_validator.calculate_metrics(y_val, val_predictions)
        
        print("\n📈 Validation Metrics:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1']:.4f}")
        print(f"  AUC-ROC:   {metrics['auc']:.4f}")
        
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'training_samples': len(X_train),
            'validation_samples': len(X_val)
        })
        
        return metrics
    
    def predict_game(self, game_data: Dict, return_detailed=False) -> Dict:
        """
        Predict outcome for a single game
        """
        if self.ensemble is None:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare game features
        team_stats = self.validator.clean_statistics(game_data.get('team_stats', {}))
        opponent_stats = self.validator.clean_statistics(game_data.get('opponent_stats', {}))
        recent_games = game_data.get('recent_games', None)
        
        features = self.feature_engineer.engineer_features(
            team_stats, opponent_stats, recent_games
        )
        
        X = pd.DataFrame([features])
        
        # Make prediction
        if return_detailed:
            detailed_preds = self.ensemble.predict_with_details(X)
            prediction = detailed_preds['ensemble'][0]
            agreement = detailed_preds['agreement'][0]
            
            return {
                'prediction': prediction,
                'confidence': np.abs(prediction - 0.5) * 2,
                'agreement': agreement,
                'individual_models': {k: v[0] for k, v in detailed_preds['individual'].items()},
                'game_info': game_data.get('game_info', {})
            }
        else:
            prediction, confidence = self.ensemble.predict(X)
            return {
                'prediction': prediction[0],
                'confidence': confidence[0],
                'game_info': game_data.get('game_info', {})
            }
    
    def predict_over_under(self, game_data: Dict, point_total: float) -> Dict:
        """
        Predict if game will go OVER or UNDER total points
        """
        prediction = self.predict_game(game_data, return_detailed=True)
        
        # Estimate combined points based on team stats
        team_pts_estimate = game_data.get('team_stats', {}).get('PTS', 0)
        opp_pts_estimate = game_data.get('opponent_stats', {}).get('PTS', 0)
        estimated_total = team_pts_estimate + opp_pts_estimate
        
        over_prob = 1 / (1 + np.exp(-(estimated_total - point_total) / 10))  # Logistic sigmoid
        
        return {
            'prediction': 'OVER' if over_prob > 0.5 else 'UNDER',
            'probability': max(over_prob, 1 - over_prob),
            'estimated_total': estimated_total,
            'point_total': point_total,
            'edge': abs(over_prob - 0.5) * 2
        }
    
    def predict_first_half_over_under(self, game_data: Dict, first_half_total: float) -> Dict:
        """
        Predict if first half will go OVER or UNDER total points
        """
        # First half typically accounts for ~45% of game points
        game_prediction = self.predict_over_under(game_data, first_half_total / 0.45)
        
        game_prediction['first_half_total'] = first_half_total
        game_prediction['estimated_first_half_total'] = game_prediction.get('estimated_total', 0) * 0.45
        
        return game_prediction
    
    def predict_team_over_under(self, game_data: Dict, team_total: float, is_home=True) -> Dict:
        """
        Predict if specific team will go OVER or UNDER their point total
        """
        team_key = 'team_stats' if is_home else 'opponent_stats'
        team_pts_estimate = game_data.get(team_key, {}).get('PTS', 0)
        
        # Simple probability based on historical average
        over_prob = 1 / (1 + np.exp(-(team_pts_estimate - team_total) / 5))
        
        return {
            'prediction': 'OVER' if over_prob > 0.5 else 'UNDER',
            'probability': max(over_prob, 1 - over_prob),
            'estimated_points': team_pts_estimate,
            'team_total': team_total,
            'edge': abs(over_prob - 0.5) * 2,
            'team_side': 'HOME' if is_home else 'AWAY'
        }
    
    def batch_predict(self, games_list: List[Dict]) -> List[Dict]:
        """
        Make predictions for multiple games
        """
        print(f"\n🎯 Making predictions for {len(games_list)} games...")
        
        predictions = []
        for i, game in enumerate(games_list):
            try:
                pred = self.predict_game(game, return_detailed=True)
                predictions.append(pred)
                
                if (i + 1) % 10 == 0:
                    print(f"  ✅ Completed {i + 1}/{len(games_list)} predictions")
            
            except Exception as e:
                print(f"  ⚠️  Error processing game {i}: {str(e)}")
                continue
        
        print(f"✅ Predictions complete!")
        
        return predictions
    
    def generate_report(self, predictions: List[Dict], output_file=None) -> Dict:
        """
        Generate comprehensive prediction report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'summary_stats': {},
            'predictions': predictions,
            'high_confidence_picks': [],
            'consensus_predictions': []
        }
        
        # Calculate summary statistics
        confidences = [p.get('confidence', 0) for p in predictions]
        report['summary_stats'] = {
            'avg_confidence': np.mean(confidences),
            'max_confidence': np.max(confidences),
            'min_confidence': np.min(confidences),
            'std_confidence': np.std(confidences)
        }
        
        # Identify high confidence picks
        high_conf_threshold = 0.70
        report['high_confidence_picks'] = [
            p for p in predictions if p.get('confidence', 0) > high_conf_threshold
        ]
        
        # Identify consensus predictions (high agreement)
        consensus_threshold = 0.75
        report['consensus_predictions'] = [
            p for p in predictions if p.get('agreement', 0) > consensus_threshold
        ]
        
        # Save report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"✅ Report saved to {output_file}")
        
        return report
    
    def save_models(self, path=None):
        """Save trained models"""
        path = path or DATA_CONFIG.get('model_dir', './models')
        if self.ensemble:
            self.ensemble.save(path)
    
    def load_models(self, path=None):
        """Load pre-trained models"""
        path = path or DATA_CONFIG.get('model_dir', './models')
        self.ensemble = EnsemblePredictor(MODEL_CONFIG)
        self.ensemble.load(path)


class PredictionFormatter:
    """Format predictions for display and output"""
    
    @staticmethod
    def format_game_prediction(prediction: Dict) -> str:
        """Format a single game prediction for display"""
        conf = prediction.get('confidence', 0)
        pred = 'WIN' if prediction.get('prediction', 0.5) > 0.5 else 'LOSS'
        game_info = prediction.get('game_info', {})
        
        output = f"""
╔════════════════════════════════════════════════╗
║ {game_info.get('matchup', 'Unknown')}
║ Prediction: {pred} | Confidence: {conf:.1%}
╚════════════════════════════════════════════════╝
        """
        return output
    
    @staticmethod
    def format_predictions_table(predictions: List[Dict]) -> str:
        """Format multiple predictions as a table"""
        df_data = []
        
        for pred in predictions:
            df_data.append({
                'Matchup': pred.get('game_info', {}).get('matchup', 'Unknown'),
                'Prediction': 'WIN' if pred.get('prediction', 0.5) > 0.5 else 'LOSS',
                'Confidence': f"{pred.get('confidence', 0):.1%}",
                'Agreement': f"{pred.get('agreement', 0):.1%}"
            })
        
        df = pd.DataFrame(df_data)
        return df.to_string(index=False)


if __name__ == "__main__":
    print("🏀 NCAA Basketball Prediction Engine")
    print("=" * 50)
    print("Ready for training and predictions!")
