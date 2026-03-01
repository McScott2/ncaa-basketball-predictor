"""
NCAA Basketball Prediction Engine Configuration
Advanced ML-based prediction system
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Model Configuration
MODEL_CONFIG = {
    "use_ensemble": True,
    "ensemble_models": ["xgboost", "lightgbm", "catboost", "neural_network"],
    "ensemble_weights": {
        "xgboost": 0.30,
        "lightgbm": 0.25,
        "catboost": 0.25,
        "neural_network": 0.20
    },
    "cv_folds": 5,
    "test_size": 0.2,
    "random_state": 42
}

# Feature Engineering
FEATURE_CONFIG = {
    "advanced_metrics": True,
    "use_player_efficiency": True,
    "use_four_factors": True,
    "scale_features": True,
    "pca_enabled": False,
    "feature_selection": "mutual_info"
}

# Prediction Settings
PREDICTION_CONFIG = {
    "prediction_types": ["full_game_over_under", "first_half_over_under", "team_over_under"],
    "confidence_threshold": 0.60,
    "min_sample_size": 30,
    "lookback_games": 20,
    "use_recent_form": True
}

# Data Sources
DATA_CONFIG = {
    "cache_enabled": True,
    "cache_dir": "./data/cache",
    "raw_data_dir": "./data/raw",
    "processed_data_dir": "./data/processed",
    "model_dir": "./models",
    "predictions_dir": "./predictions"
}

# API Configuration
API_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 2,
    "rate_limit": 100  # Requests per minute
}

# Performance Metrics
METRICS_CONFIG = {
    "track_accuracy": True,
    "track_precision": True,
    "track_recall": True,
    "track_auc": True,
    "track_calibration": True
}

# XGBoost Parameters
XGBOOST_PARAMS = {
    "max_depth": 7,
    "learning_rate": 0.05,
    "n_estimators": 200,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 1,
    "gamma": 0.5,
    "objective": "binary:logistic",
    "eval_metric": "auc"
}

# LightGBM Parameters
LGBM_PARAMS = {
    "max_depth": 8,
    "learning_rate": 0.05,
    "n_estimators": 200,
    "num_leaves": 31,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_samples": 20,
    "objective": "binary",
    "metric": "auc"
}

# CatBoost Parameters
CATBOOST_PARAMS = {
    "max_depth": 7,
    "learning_rate": 0.05,
    "iterations": 200,
    "subsample": 0.8,
    "colsample_bylevel": 0.8,
    "loss_function": "Logloss",
    "eval_metric": "AUC",
    "verbose": 0
}

# Neural Network Parameters
NN_PARAMS = {
    "input_dim": 50,  # Will be adjusted based on features
    "hidden_layers": [128, 64, 32],
    "activation": "relu",
    "dropout_rate": 0.3,
    "learning_rate": 0.001,
    "batch_size": 32,
    "epochs": 100,
    "validation_split": 0.2
}

# Output Settings
OUTPUT_CONFIG = {
    "output_format": "json",  # json, csv, html
    "include_confidence": True,
    "include_explanation": True,
    "include_historical_stats": True,
    "prediction_limit": 100
}

def get_project_root():
    """Get the root directory of the project"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ensure_directories():
    """Ensure all required directories exist"""
    root = get_project_root()
    dirs = [
        DATA_CONFIG["cache_dir"],
        DATA_CONFIG["raw_data_dir"],
        DATA_CONFIG["processed_data_dir"],
        DATA_CONFIG["model_dir"],
        DATA_CONFIG["predictions_dir"]
    ]
    
    for dir_path in dirs:
        full_path = os.path.join(root, dir_path)
        os.makedirs(full_path, exist_ok=True)
