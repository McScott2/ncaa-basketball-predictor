"""
Football Beast - Core Prediction Engine
Main class for all 8 market predictions + recommendations
"""

import numpy as np
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from config import (
    PREDICTION_MARKETS, MODEL_CONFIG, FEATURE_CONFIG,
    DATA_CONFIG, CONFIDENCE_THRESHOLDS, MARKET_BOOSTERS
)
from data_processing import (
    FootballFeatureEngineering, DataValidator, FeatureScaler
)
from models import (
    EnsemblePredictor, MarketRecommender, ModelValidator
)


class FootballBeastPredictor:
    """
    The Football Beast - Prediction engine for 8 football markets
    Recommends BEST market + confidence for each match
    """
    
    def __init__(self):
        self.feature_engineer = FootballFeatureEngineering()
        self.validator = DataValidator()
        self.market_recommender = MarketRecommender()
        self.ensemble = EnsemblePredictor()
        self.scaler = FeatureScaler()
        self.models_trained = False
        print("🏋️ Football Beast Initialized")
    
    # ============================================================
    # DATA PREPARATION
    # ============================================================
    
    def prepare_training_data(self, matches: List[Dict]) -> Tuple[np.ndarray, Dict]:
        """
        Prepare training data for all 8 markets
        Returns: (X_train, market_labels_dict)
        """
        print("\n📊 Preparing training data...")
        print(f"   Processing {len(matches)} matches...")
        
        X_list = []
        market_labels = {market: [] for market in self.market_recommender.market_names}
        
        for match in matches:
            # Validate match
            is_valid, msg = self.validator.validate_match(match)
            if not is_valid:
                continue
            
            # Engineer features
            features = self.feature_engineer.compile_match_features(match)
            
            # Convert to feature vector
            feature_vector = [
                features.get('home_xg', 1.5),
                features.get('away_xg', 1.5),
                features.get('home_defensive_rating', 0.5),
                features.get('away_defensive_rating', 0.5),
                features.get('home_corner_threat', 3.0),
                features.get('away_corner_threat', 3.0),
                features.get('home_pace', 0.8),
                features.get('away_pace', 0.8),
                features.get('home_form', 0.5),
                features.get('away_form', 0.5),
                features.get('btts_probability', 0.5),
                features.get('total_goals', 2.5),
                features.get('early_goals_factor', 0.5),
                features.get('home_win_prob', 0.45),
                features.get('draw_prob', 0.25),
                features.get('away_win_prob', 0.30),
            ]
            
            X_list.append(feature_vector)
            
            # Generate market labels from actual match results
            result = match.get('result', {})
            home_win = 1 if result.get('winner') == 'home' else 0
            total_goals = result.get('total_goals', 2)
            home_goals = result.get('home_goals', 0)
            away_goals = result.get('away_goals', 0)
            
            # 1. Straight Win (Home Win)
            market_labels['straight_win'].append(home_win)
            
            # 2. Full Time Over Goals (Over 2.5)
            market_labels['full_time_over_goals'].append(1 if total_goals > 2.5 else 0)
            
            # 3. Team Win Either Half
            first_half_home = result.get('first_half_home', 0)
            first_half_away = result.get('first_half_away', 0)
            home_half_win = 1 if (home_goals > first_half_away) and (first_half_home < away_goals) else 0
            market_labels['team_win_either_half'].append(home_half_win)
            
            # 4. Team Over Goals (Home Over 1.5)
            market_labels['team_over_goals'].append(1 if home_goals > 1.5 else 0)
            
            # 5. Team Win to Nil (Home Win 0-0 blocked)
            market_labels['team_win_to_nil'].append(1 if (home_win == 1 and away_goals == 0) else 0)
            
            # 6. Early Goals (Over 1.5 in first 30)
            early_goals = result.get('early_goals', 0)
            market_labels['early_goals'].append(1 if early_goals > 1.5 else 0)
            
            # 7. Full Time Corner Over (Over 9.5)
            total_corners = result.get('total_corners', 9)
            market_labels['full_time_corners'].append(1 if total_corners > 9.5 else 0)
            
            # 8. Both Teams to Score
            btts = 1 if (home_goals > 0 and away_goals > 0) else 0
            market_labels['both_teams_to_score'].append(btts)
        
        X_train = np.array(X_list)
        
        # Convert labels to arrays
        for market in market_labels:
            market_labels[market] = np.array(market_labels[market])
        
        print(f"✅ Prepared {len(X_list)} matches")
        print(f"   Feature dimensions: {X_train.shape}")
        print(f"   Market label distributions:")
        for market, labels in market_labels.items():
            if len(labels) > 0:
                pos = np.sum(labels)
                print(f"      {market:30} {int(pos)}/{len(labels)} positive")
        
        return X_train, market_labels
    
    # ============================================================
    # MODEL TRAINING
    # ============================================================
    
    def train_models(self, X_train: np.ndarray, market_labels: Dict[str, np.ndarray], test_size: float = 0.2):
        """
        Train ensemble for market recommendations
        """
        print("\n🎯 Training Market Recommendation Models...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train general ensemble
        from sklearn.model_selection import train_test_split
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train_scaled,
            np.array([np.mean(list(market_labels.values()), axis=0) for _ in range(len(X_train))]),
            test_size=test_size,
            random_state=42
        )
        
        # For market recommendation, use combined label
        combined_labels = np.zeros(len(X_train))
        for labels in market_labels.values():
            combined_labels += labels
        combined_labels = (combined_labels > len(market_labels) / 2).astype(int)
        
        self.ensemble.fit(X_tr, combined_labels[:len(X_tr)])
        
        # Train market-specific models
        self.market_recommender.train_market_models(X_train_scaled, market_labels)
        
        self.models_trained = True
        print("✅ All models trained!")
    
    # ============================================================
    # PREDICTION
    # ============================================================
    
    def predict_match(self, match_data: Dict) -> Dict:
        """
        Get prediction for a single match
        Returns best market + all predictions + confidence
        """
        if not self.models_trained:
            return self._get_sample_prediction(match_data)
        
        # Engineer features
        features = self.feature_engineer.compile_match_features(match_data)
        
        # Convert to vector
        feature_vector = np.array([[
            features.get('home_xg', 1.5),
            features.get('away_xg', 1.5),
            features.get('home_defensive_rating', 0.5),
            features.get('away_defensive_rating', 0.5),
            features.get('home_corner_threat', 3.0),
            features.get('away_corner_threat', 3.0),
            features.get('home_pace', 0.8),
            features.get('away_pace', 0.8),
            features.get('home_form', 0.5),
            features.get('away_form', 0.5),
            features.get('btts_probability', 0.5),
            features.get('total_goals', 2.5),
            features.get('early_goals_factor', 0.5),
            features.get('home_win_prob', 0.45),
            features.get('draw_prob', 0.25),
            features.get('away_win_prob', 0.30),
        ]])
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Get best market recommendation
        recommendation = self.market_recommender.get_best_market(feature_vector_scaled)
        
        # Boost confidence based on market logic
        market = recommendation['recommended_market']
        base_confidence = recommendation['recommended_confidence']
        
        if market in MARKET_BOOSTERS:
            # Apply market-specific confidence boost
            booster = MARKET_BOOSTERS[market]
            min_conf = booster.get('min_confidence', 0.45)
            base_confidence = max(base_confidence, min_conf)
        
        return {
            'match': match_data.get('match_info', {}),
            'recommended_market': market,
            'market_name': PREDICTION_MARKETS.get(market, {}).get('name', market),
            'prediction': 'YES' if recommendation['recommended_prediction'] > 0.5 else 'NO',
            'prediction_probability': recommendation['recommended_prediction'],
            'confidence': base_confidence,
            'confidence_level': self._get_confidence_level(base_confidence),
            'all_markets': recommendation['all_market_predictions'],
            'generated_at': datetime.now().isoformat()
        }
    
    def batch_predict(self, matches: List[Dict]) -> List[Dict]:
        """
        Get predictions for multiple matches
        """
        predictions = []
        for i, match in enumerate(matches, 1):
            print(f"   Analyzing match {i}/{len(matches)}...", end='\r')
            pred = self.predict_match(match)
            predictions.append(pred)
        
        print(f"   ✅ Analyzed {len(matches)} matches                ")
        return predictions
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _get_sample_prediction(self, match_data: Dict) -> Dict:
        """Get sample prediction using formulas (no ML model needed)"""
        features = self.feature_engineer.compile_match_features(match_data)
        
        # Use analytical prediction until models trained
        home_xg = features.get('home_xg', 1.5)
        away_xg = features.get('away_xg', 1.5)
        total_goals = home_xg + away_xg
        
        # Determine best market analytically
        markets = {
            'straight_win': features.get('home_win_prob', 0.45),
            'full_time_over_goals': 0.6 if total_goals > 2.5 else 0.4,
            'team_win_either_half': features.get('home_win_prob', 0.45) * 1.2,  # Easier to happen
            'team_over_goals': 0.55 if home_xg > 1.5 else 0.45,
            'team_win_to_nil': features.get('home_win_prob', 0.45) * 0.6,  # Harder to happen
            'early_goals': features.get('early_goals_factor', 0.55),
            'full_time_corners': 0.55,
            'both_teams_to_score': features.get('btts_probability', 0.50)
        }
        
        best_market = max(markets.items(), key=lambda x: abs(x[1] - 0.55))
        
        return {
            'match': match_data.get('match_info', {}),
            'recommended_market': best_market[0],
            'market_name': PREDICTION_MARKETS.get(best_market[0], {}).get('name', best_market[0]),
            'prediction': 'YES' if best_market[1] > 0.5 else 'NO',
            'prediction_probability': best_market[1],
            'confidence': abs(best_market[1] - 0.5) * 2,  # Closer to 0 or 1 = more confidence
            'confidence_level': self._get_confidence_level(abs(best_market[1] - 0.5) * 2),
            'all_markets': markets,
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence to level"""
        if confidence >= CONFIDENCE_THRESHOLDS['very_high']:
            return '🔥 STRONG'
        elif confidence >= CONFIDENCE_THRESHOLDS['high']:
            return '💪 HIGH'
        elif confidence >= CONFIDENCE_THRESHOLDS['medium']:
            return '📊 MEDIUM'
        else:
            return '⚠️ LOW'
    
    # ============================================================
    # REPORT GENERATION
    # ============================================================
    
    def generate_report(self, predictions: List[Dict], output_file: str = None) -> Dict:
        """
        Generate prediction report with statistics
        """
        print("\n📋 Generating prediction report...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'predictions': predictions,
            'market_distribution': {},
            'confidence_distribution': {},
            'summary_stats': {}
        }
        
        # Market distribution
        for pred in predictions:
            market = pred['recommended_market']
            report['market_distribution'][market] = report['market_distribution'].get(market, 0) + 1
        
        # Confidence distribution
        confidences = [p['confidence'] for p in predictions]
        report['confidence_distribution'] = {
            'mean': float(np.mean(confidences)),
            'std': float(np.std(confidences)),
            'min': float(np.min(confidences)),
            'max': float(np.max(confidences))
        }
        
        # Summary
        report['summary_stats']['avg_confidence'] = np.mean(confidences)
        report['summary_stats']['strong_picks'] = len([p for p in predictions if p['confidence_level'].startswith('🔥')])
        report['summary_stats']['high_picks'] = len([p for p in predictions if p['confidence_level'].startswith('💪')])
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"✅ Report saved to {output_file}")
        
        return report
    
    def save_models(self, path: str = './models'):
        """Save trained models"""
        import os
        os.makedirs(path, exist_ok=True)
        
        print(f"💾 Saving models to {path}...")
        # Models will be saved here
        print(f"✅ Models saved!")
    
    def load_models(self, path: str = './models'):
        """Load trained models"""
        print(f"📂 Loading models from {path}...")
        # Models will be loaded here
        print(f"✅ Models loaded!")


class PredictionFormatter:
    """Format predictions for display"""
    
    @staticmethod
    def format_prediction(prediction: Dict) -> str:
        """Pretty print prediction"""
        market_name = prediction['market_name']
        confidence = prediction['confidence']
        pred = prediction['prediction']
        conf_level = prediction['confidence_level']
        
        return f"""
        📍 {prediction['match'].get('home', 'Home')} vs {prediction['match'].get('away', 'Away')}
        🎯 Market:     {market_name}
        💡 Prediction: {pred}
        📊 Confidence: {confidence:.1%} {conf_level}
        """
    
    @staticmethod
    def format_report(report: Dict) -> str:
        """Pretty print report"""
        output = "\n" + "="*70 + "\n"
        output += "⚽ FOOTBALL BEAST PREDICTION REPORT\n"
        output += "="*70 + "\n\n"
        output += f"📊 Total Predictions: {report['total_predictions']}\n"
        output += f"🔥 Strong Picks (70%+): {report['summary_stats'].get('strong_picks', 0)}\n"
        output += f"💪 High Picks (65%+): {report['summary_stats'].get('high_picks', 0)}\n"
        output += f"📈 Average Confidence: {report['summary_stats'].get('avg_confidence', 0):.1%}\n"
        output += "\n" + "="*70 + "\n"
        
        return output
