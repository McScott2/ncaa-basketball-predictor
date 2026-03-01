"""
Machine Learning Models for NCAA Basketball Prediction
Ensemble of XGBoost, LightGBM, CatBoost, and Neural Networks
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import joblib
import json
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class XGBoostPredictor:
    """XGBoost model for basketball predictions"""
    
    def __init__(self, params=None):
        self.params = params or {
            'max_depth': 7,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'tree_method': 'hist',
            'device': 'cuda'  # Use GPU if available
        }
        self.model = None
        self.scaler = StandardScaler()
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train XGBoost model"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_val_scaled, y_val)]
        else:
            eval_set = None
        
        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X_train_scaled, y_train, eval_set=eval_set, verbose=False)
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]
    
    def get_feature_importance(self, n_features=20):
        """Get feature importance"""
        if self.model is None:
            return None
        importances = self.model.feature_importances_
        return importances.argsort()[-n_features:][::-1]


class LightGBMPredictor:
    """LightGBM model for basketball predictions"""
    
    def __init__(self, params=None):
        self.params = params or {
            'max_depth': 8,
            'learning_rate': 0.05,
            'n_estimators': 200,
            'num_leaves': 31,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary',
            'metric': 'auc',
            'device': 'cpu'
        }
        self.model = None
        self.scaler = StandardScaler()
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train LightGBM model"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        eval_set = None
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_val_scaled, y_val)]
        
        self.model = lgb.LGBMClassifier(**self.params)
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=eval_set,
            callbacks=[lgb.log_evaluation(period=0)]
        )
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]


class CatBoostPredictor:
    """CatBoost model for basketball predictions"""
    
    def __init__(self, params=None):
        self.params = params or {
            'max_depth': 7,
            'learning_rate': 0.05,
            'iterations': 200,
            'loss_function': 'Logloss',
            'eval_metric': 'AUC',
            'verbose': 0,
            'random_state': 42
        }
        self.model = None
        self.scaler = StandardScaler()
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train CatBoost model"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        eval_set = None
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            eval_set = [(X_val_scaled, y_val)]
        
        self.model = CatBoostClassifier(**self.params)
        self.model.fit(X_train_scaled, y_train, eval_set=eval_set)
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]


class NeuralNetworkPredictor:
    """Deep neural network for basketball predictions"""
    
    def __init__(self, input_dim, hidden_layers=None):
        self.input_dim = input_dim
        self.hidden_layers = hidden_layers or [128, 64, 32]
        self.model = None
        self.scaler = StandardScaler()
        self._build_model()
        
    def _build_model(self):
        """Build neural network architecture"""
        self.model = Sequential([
            Dense(self.hidden_layers[0], activation='relu', input_dim=self.input_dim),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(self.hidden_layers[1], activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            
            Dense(self.hidden_layers[2], activation='relu'),
            BatchNormalization(),
            Dropout(0.2),
            
            Dense(16, activation='relu'),
            Dropout(0.2),
            
            Dense(1, activation='sigmoid')
        ])
        
        optimizer = Adam(learning_rate=0.001)
        self.model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['auc'])
        
    def fit(self, X_train, y_train, X_val=None, y_val=None, epochs=100):
        """Train neural network"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        callbacks = [
            EarlyStopping(monitor='loss', patience=15, restore_best_weights=True),
            ReduceLROnPlateau(monitor='loss', factor=0.5, patience=5, min_lr=0.00001)
        ]
        
        validation_data = None
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            validation_data = (X_val_scaled, y_val)
        
        self.model.fit(
            X_train_scaled, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=32,
            callbacks=callbacks,
            verbose=0
        )
        
        return self
    
    def predict(self, X):
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled, verbose=0).flatten()


class EnsemblePredictor:
    """
    Ensemble of multiple models with weighted averaging
    """
    
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.weights = config.get('ensemble_weights', {})
        self.history = []
        
    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """
        Train all ensemble models
        """
        print("🚀 Training Ensemble Models...")
        
        # XGBoost
        print("  ⚡ Training XGBoost...")
        xgb_model = XGBoostPredictor()
        xgb_model.fit(X_train, y_train, X_val, y_val)
        self.models['xgboost'] = xgb_model
        
        # LightGBM
        print("  ⚡ Training LightGBM...")
        lgb_model = LightGBMPredictor()
        lgb_model.fit(X_train, y_train, X_val, y_val)
        self.models['lightgbm'] = lgb_model
        
        # CatBoost
        print("  ⚡ Training CatBoost...")
        cat_model = CatBoostPredictor()
        cat_model.fit(X_train, y_train, X_val, y_val)
        self.models['catboost'] = cat_model
        
        # Neural Network
        print("  ⚡ Training Neural Network...")
        nn_model = NeuralNetworkPredictor(X_train.shape[1])
        nn_model.fit(X_train, y_train, X_val, y_val, epochs=100)
        self.models['neural_network'] = nn_model
        
        print("✅ Ensemble training complete!")
        
        return self
    
    def predict(self, X, return_confidence=True):
        """
        Make ensemble predictions
        """
        predictions = {}
        
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict(X)
        
        # Weighted ensemble
        ensemble_pred = np.zeros_like(predictions['xgboost'])
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 1.0 / len(self.models))
            ensemble_pred += weight * pred
        
        if return_confidence:
            confidence = np.abs(ensemble_pred - 0.5) * 2  # 0-1 scale
            return ensemble_pred, confidence
        
        return ensemble_pred
    
    def predict_with_details(self, X):
        """
        Make predictions with detailed breakdown
        """
        predictions = {}
        
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict(X)
        
        # Ensemble prediction
        ensemble_pred = np.zeros_like(predictions['xgboost'])
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 1.0 / len(self.models))
            ensemble_pred += weight * pred
        
        return {
            'ensemble': ensemble_pred,
            'individual': predictions,
            'agreement': self._calculate_agreement(predictions)
        }
    
    def _calculate_agreement(self, predictions):
        """Calculate how much models agree on predictions"""
        preds_array = np.array(list(predictions.values()))
        std_dev = np.std(preds_array, axis=0)
        agreement = 1 - np.clip(std_dev, 0, 1)  # Higher = more agreement
        return agreement
    
    def save(self, path):
        """Save ensemble models"""
        for model_name, model in self.models.items():
            joblib.dump(model, f"{path}/{model_name}_model.pkl")
        
        meta = {
            'timestamp': datetime.now().isoformat(),
            'weights': self.weights,
            'models': list(self.models.keys())
        }
        
        with open(f"{path}/ensemble_meta.json", 'w') as f:
            json.dump(meta, f)
        
        print(f"✅ Models saved to {path}")
    
    def load(self, path):
        """Load ensemble models"""
        for model_name in ['xgboost', 'lightgbm', 'catboost', 'neural_network']:
            try:
                self.models[model_name] = joblib.load(f"{path}/{model_name}_model.pkl")
            except:
                pass
        
        print(f"✅ Models loaded from {path}")


class ModelValidator:
    """
    Validate and evaluate model performance
    """
    
    @staticmethod
    def cross_validate(model, X, y, cv=5):
        """Perform cross-validation"""
        scores = cross_val_score(model, X, y, cv=cv, scoring='roc_auc')
        return {
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'individual_scores': scores
        }
    
    @staticmethod
    def calculate_metrics(y_true, y_pred):
        """Calculate comprehensive evaluation metrics"""
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, 
            f1_score, roc_auc_score, confusion_matrix
        )
        
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        return {
            'accuracy': accuracy_score(y_true, y_pred_binary),
            'precision': precision_score(y_true, y_pred_binary),
            'recall': recall_score(y_true, y_pred_binary),
            'f1': f1_score(y_true, y_pred_binary),
            'auc': roc_auc_score(y_true, y_pred),
            'confusion_matrix': confusion_matrix(y_true, y_pred_binary).tolist()
        }
