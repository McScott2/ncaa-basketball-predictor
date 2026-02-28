"""
Football Beast - ML Models & Recommendation Engine
4-Model Ensemble + Market Recommendation System
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_CONFIG, XGBOOST_PARAMS, LGBM_PARAMS, CATBOOST_PARAMS, NN_PARAMS

try:
    import xgboost as xgb
except:
    xgb = None

try:
    import lightgbm as lgb
except:
    lgb = None

try:
    from catboost import CatBoostClassifier
except:
    CatBoostClassifier = None

try:
    from tensorflow import keras
    from tensorflow.keras import layers
except:
    keras = None


class XGBoostPredictor:
    """XGBoost model for market prediction"""
    
    def __init__(self):
        if xgb is None:
            raise ImportError("xgboost not installed")
        self.model = xgb.XGBClassifier(**XGBOOST_PARAMS)
        self.name = 'xgboost'
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train XGBoost"""
        if X_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)
    
    def predict(self, X):
        """Predict probabilities"""
        return self.model.predict_proba(X)[:, 1]
    
    def feature_importance(self):
        """Get feature importance"""
        return self.model.feature_importances_


class LightGBMPredictor:
    """LightGBM model for market prediction"""
    
    def __init__(self):
        if lgb is None:
            raise ImportError("lightgbm not installed")
        self.model = lgb.LGBMClassifier(**LGBM_PARAMS)
        self.name = 'lightgbm'
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train LightGBM"""
        if X_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose_eval=False
            )
        else:
            self.model.fit(X_train, y_train)
    
    def predict(self, X):
        """Predict probabilities"""
        return self.model.predict_proba(X)[:, 1]
    
    def feature_importance(self):
        """Get feature importance"""
        return self.model.feature_importances_


class CatBoostPredictor:
    """CatBoost model for market prediction"""
    
    def __init__(self):
        if CatBoostClassifier is None:
            raise ImportError("catboost not installed")
        self.model = CatBoostClassifier(**CATBOOST_PARAMS)
        self.name = 'catboost'
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train CatBoost"""
        if X_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)
    
    def predict(self, X):
        """Predict probabilities"""
        return self.model.predict_proba(X)[:, 1]
    
    def feature_importance(self):
        """Get feature importance"""
        return self.model.feature_importances_


class NeuralNetworkPredictor:
    """Neural Network model for market prediction"""
    
    def __init__(self, input_dim=20):
        if keras is None:
            raise ImportError("tensorflow not installed")
        
        model = keras.Sequential([
            layers.Input(shape=(input_dim,)),
            layers.Dense(128, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.Dropout(0.3),
            layers.Dense(32, activation='relu', kernel_regularizer=keras.regularizers.l2(0.001)),
            layers.Dropout(0.2),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC()]
        )
        
        self.model = model
        self.name = 'neural_network'
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train neural network"""
        validation_data = (X_val, y_val) if X_val is not None else None
        
        self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=100,
            batch_size=32,
            verbose=0
        )
    
    def predict(self, X):
        """Predict probabilities"""
        return self.model.predict(X, verbose=0).flatten()
    
    def feature_importance(self):
        """Get feature importance (from first dense layer)"""
        weights = self.model.layers[0].get_weights()[0]
        return np.abs(weights).mean(axis=1)


class EnsemblePredictor:
    """4-Model Ensemble with weighted voting"""
    
    def __init__(self):
        self.models = {}
        self.weights = MODEL_CONFIG['ensemble_weights']
        self.agreement_scores = {}
    
    def add_model(self, model):
        """Add model to ensemble"""
        self.models[model.name] = model
    
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train all models"""
        print("🚀 Training Ensemble Models...")
        
        try:
            print("  ⚡ Training XGBoost...")
            xgb_model = XGBoostPredictor()
            xgb_model.fit(X_train, y_train, X_val, y_val)
            self.models['xgboost'] = xgb_model
        except Exception as e:
            print(f"     ⚠️  XGBoost failed: {e}")
        
        try:
            print("  ⚡ Training LightGBM...")
            lgb_model = LightGBMPredictor()
            lgb_model.fit(X_train, y_train, X_val, y_val)
            self.models['lightgbm'] = lgb_model
        except Exception as e:
            print(f"     ⚠️  LightGBM failed: {e}")
        
        try:
            print("  ⚡ Training CatBoost...")
            cat_model = CatBoostPredictor()
            cat_model.fit(X_train, y_train, X_val, y_val)
            self.models['catboost'] = cat_model
        except Exception as e:
            print(f"     ⚠️  CatBoost failed: {e}")
        
        try:
            print("  ⚡ Training Neural Network...")
            nn_model = NeuralNetworkPredictor(input_dim=X_train.shape[1])
            nn_model.fit(X_train, y_train, X_val, y_val)
            self.models['neural_network'] = nn_model
        except Exception as e:
            print(f"     ⚠️  Neural Network failed: {e}")
        
        print("✅ Ensemble training complete!")
    
    def predict(self, X) -> Tuple[np.ndarray, np.ndarray, Dict]:
        """
        Ensemble prediction with weighted voting
        Returns: (predictions, confidence, individual_model_predictions)
        """
        predictions = {}
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X)
                predictions[name] = pred
            except:
                continue
        
        if not predictions:
            return np.array([0.5]), np.array([0.0]), {}
        
        # Weighted ensemble average
        ensemble_pred = np.zeros(len(X))
        total_weight = 0
        
        for name, pred in predictions.items():
            weight = self.weights.get(name, 0.25)
            ensemble_pred += pred * weight
            total_weight += weight
        
        ensemble_pred /= max(total_weight, 0.01)
        
        # Confidence = agreement between models (lower std = higher confidence)
        model_preds = np.array(list(predictions.values()))
        agreement = 1.0 - np.std(model_preds, axis=0)
        
        return ensemble_pred, agreement, predictions
    
    def predict_detailed(self, X) -> Dict:
        """Get detailed prediction with all models"""
        ensemble_pred, agreement, individual_preds = self.predict(X)
        
        return {
            'ensemble_prediction': ensemble_pred[0],
            'confidence': agreement[0],
            'individual_models': {k: v[0] for k, v in individual_preds.items()},
            'agreement': agreement[0]
        }


class MarketRecommender:
    """Recommends BEST market (1 of 8) for each match"""
    
    def __init__(self):
        self.market_models = {}  # One model per market
        self.market_names = [
            'straight_win',
            'full_time_over_goals',
            'team_win_either_half',
            'team_over_goals',
            'team_win_to_nil',
            'early_goals',
            'full_time_corners',
            'both_teams_to_score'
        ]
    
    def train_market_models(self, X_train: np.ndarray, market_labels: Dict[str, np.ndarray]):
        """
        Train a separate ensemble for each market
        market_labels = {'straight_win': y_win, 'btts': y_btts, ...}
        """
        print("\n📊 Training Market-Specific Models...")
        
        for market in self.market_names:
            if market in market_labels:
                print(f"   Training {market}...")
                ensemble = EnsemblePredictor()
                try:
                    ensemble.fit(X_train, market_labels[market])
                    self.market_models[market] = ensemble
                except Exception as e:
                    print(f"      ⚠️  Failed: {e}")
        
        print("✅ Market models trained!")
    
    def get_best_market(self, features: np.ndarray) -> Dict:
        """
        Predict all 8 markets, return the BEST one with highest confidence
        """
        market_predictions = {}
        
        for market, model in self.market_models.items():
            try:
                pred, conf, _ = model.predict(features)
                market_predictions[market] = {
                    'prediction': pred[0],
                    'confidence': conf[0],
                    'market': market
                }
            except:
                market_predictions[market] = {
                    'prediction': 0.5,
                    'confidence': 0.0,
                    'market': market
                }
        
        # Find market with highest confidence
        best_market = max(
            market_predictions.items(),
            key=lambda x: x[1]['confidence']
        )
        
        return {
            'recommended_market': best_market[0],
            'recommended_prediction': best_market[1]['prediction'],
            'recommended_confidence': best_market[1]['confidence'],
            'all_market_predictions': market_predictions
        }


class ModelValidator:
    """Validate model performance"""
    
    @staticmethod
    def calculate_metrics(y_true, y_pred, y_pred_proba=None):
        """Calculate accuracy, precision, recall, F1, AUC"""
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, 
            f1_score, roc_auc_score, confusion_matrix
        )
        
        y_pred_binary = (y_pred_proba > 0.5).astype(int) if y_pred_proba is not None else y_pred
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred_binary),
            'precision': precision_score(y_true, y_pred_binary, zero_division=0),
            'recall': recall_score(y_true, y_pred_binary, zero_division=0),
            'f1': f1_score(y_true, y_pred_binary, zero_division=0)
        }
        
        if y_pred_proba is not None:
            metrics['auc'] = roc_auc_score(y_true, y_pred_proba)
            metrics['confusion_matrix'] = confusion_matrix(y_true, y_pred_binary).tolist()
        
        return metrics
    
    @staticmethod
    def cross_validate(model, X, y, cv=5):
        """K-fold cross validation"""
        from sklearn.model_selection import cross_val_score
        
        scores = cross_val_score(model.model, X, y, cv=cv, scoring='roc_auc')
        
        return {
            'mean_auc': scores.mean(),
            'std_auc': scores.std(),
            'fold_scores': scores.tolist()
        }
