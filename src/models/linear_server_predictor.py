"""
Linear regression model for predicting optimal number of servers needed.

Features: date, time-of-day, day-of-week, holiday, historical load, spike probability
Target: optimal_servers_needed

Includes model training, evaluation, and deployment logic.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pickle
from scipy import stats
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error


class LinearServerPredictor:
    """
    Trains and deploys a linear regression model to predict optimal server count.
    """
    
    def __init__(self, model_type: str = 'ridge', alpha: float = 1.0):
        """
        Initialize predictor.
        
        Args:
            model_type: 'linear', 'ridge', or 'lasso'
            alpha: regularization strength (for ridge/lasso)
        """
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.feature_scaler = StandardScaler()
        
        if model_type == 'linear':
            self.model = LinearRegression()
        elif model_type == 'ridge':
            self.model = Ridge(alpha=alpha)
        elif model_type == 'lasso':
            self.model = Lasso(alpha=alpha)
        else:
            raise ValueError("model_type must be 'linear', 'ridge', or 'lasso'")
        
        self.is_trained = False
        self.feature_names = None
        self.training_stats = {}
        
        # Thresholds for server management
        self.shutdown_threshold = 0.3  # Shutdown if < 30% utilized
        self.spinup_threshold = 0.85   # Spin up if > 85% utilized
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from raw metrics data.
        
        Expected columns: timestamp, queue_depth, servers_active, 
                         resource_utilization, is_holiday, hour, day_of_week
        """
        df = df.copy()
        
        # Parse timestamp
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Temporal features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['is_weekday'] = (df['day_of_week'] < 5).astype(int)
        
        # Cyclical encoding for hour (sine/cosine)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Cyclical encoding for day of week
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Load features
        df['queue_depth'] = df['queue_depth'].fillna(0)
        df['resource_utilization'] = df['resource_utilization'].fillna(0)
        
        # Rolling averages (look-back features)
        df['queue_depth_ma5'] = df['queue_depth'].rolling(window=5, min_periods=1).mean()
        df['queue_depth_ma15'] = df['queue_depth'].rolling(window=15, min_periods=1).mean()
        df['resource_util_ma5'] = df['resource_utilization'].rolling(window=5, min_periods=1).mean()
        
        # Volatility (spike indicator)
        df['queue_depth_std'] = df['queue_depth'].rolling(window=10, min_periods=1).std().fillna(0)
        
        # Holiday flag
        df['is_holiday'] = df.get('is_holiday', 0).astype(int)
        
        return df
    
    def create_training_data(self, df: pd.DataFrame, 
                            target_column: str = 'servers_active',
                            test_size: float = 0.2,
                            random_state: int = 42) \
                            -> Tuple[np.ndarray, np.ndarray, 
                                   np.ndarray, np.ndarray, List[str]]:
        """
        Prepare training and test data.
        
        Returns: X_train, X_test, y_train, y_test, feature_names
        """
        df = self.engineer_features(df)
        
        # Select features
        feature_cols = [
            'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos',
            'is_weekday', 'is_holiday', 'day_of_month',
            'queue_depth', 'resource_utilization',
            'queue_depth_ma5', 'queue_depth_ma15',
            'resource_util_ma5', 'queue_depth_std'
        ]
        
        # Keep only existing columns
        feature_cols = [col for col in feature_cols if col in df.columns]
        self.feature_names = feature_cols
        
        X = df[feature_cols].values
        y = df[target_column].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        return X_train, X_test, y_train, y_test, feature_cols
    
    def train(self, df: pd.DataFrame, 
             target_column: str = 'servers_active',
             verbose: bool = True) -> Dict:
        """
        Train the linear regression model.
        
        Returns: training metrics dict
        """
        X_train, X_test, y_train, y_test, feature_cols = self.create_training_data(
            df, target_column
        )
        
        # Scale features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        X_test_scaled = self.feature_scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        self.training_stats = {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'n_samples': len(X_train) + len(X_test),
            'n_features': len(feature_cols),
            'model_type': self.model_type
        }
        
        if verbose:
            print(f"✓ Model trained: {self.model_type}")
            print(f"  Train RMSE: {train_rmse:.3f} | Test RMSE: {test_rmse:.3f}")
            print(f"  Train MAE: {train_mae:.3f} | Test MAE: {test_mae:.3f}")
            print(f"  Train R²: {train_r2:.3f} | Test R²: {test_r2:.3f}")
        
        return self.training_stats
    
    def predict_servers_needed(self, timestamp: datetime, 
                             queue_depth: float,
                             resource_utilization: float,
                             is_holiday: bool = False,
                             historical_data: pd.DataFrame = None) -> int:
        """
        Predict optimal number of servers needed at given time.
        
        Returns: predicted server count (int)
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        # Create feature vector
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        day_of_month = timestamp.day
        
        features = [
            np.sin(2 * np.pi * hour / 24),           # hour_sin
            np.cos(2 * np.pi * hour / 24),           # hour_cos
            np.sin(2 * np.pi * day_of_week / 7),     # dow_sin
            np.cos(2 * np.pi * day_of_week / 7),     # dow_cos
            int(day_of_week < 5),                    # is_weekday
            int(is_holiday),                         # is_holiday
            float(day_of_month),                     # day_of_month
            float(queue_depth),                      # queue_depth
            float(resource_utilization),               # resource_utilization
            float(queue_depth),                      # queue_depth_ma5 (approximate)
            float(queue_depth),                      # queue_depth_ma15 (approximate)
            float(resource_utilization),             # resource_util_ma5
            0.1                                       # queue_depth_std (default)
        ]
        
        # Scale and predict
        X = np.array(features).reshape(1, -1)
        X_scaled = self.feature_scaler.transform(X)
        prediction = self.model.predict(X_scaled)[0]
        
        # Clamp to reasonable range [1, max_servers]
        predicted_servers = max(1, min(int(np.ceil(prediction)), 100))
        
        return predicted_servers
    
    def predict_batch(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict for batch of rows.
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        df = self.engineer_features(df)
        feature_cols = self.feature_names
        
        X = df[feature_cols].values
        X_scaled = self.feature_scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return np.maximum(1, np.ceil(predictions)).astype(int)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance (coefficients)."""
        if not self.is_trained or self.feature_names is None:
            raise ValueError("Model not trained yet!")
        
        coefficients = self.model.coef_
        importance = {}
        
        for name, coef in zip(self.feature_names, coefficients):
            importance[name] = float(coef)
        
        # Sort by absolute value
        importance = dict(sorted(importance.items(), 
                                key=lambda x: abs(x[1]), reverse=True))
        
        return importance
    
    def should_shutdown_server(self, current_utilization: float) -> bool:
        """Determine if a server should be shut down."""
        return current_utilization < self.shutdown_threshold
    
    def should_spinup_server(self, current_utilization: float) -> bool:
        """Determine if a new server should be spun up."""
        return current_utilization > self.spinup_threshold
    
    def save_model(self, file_path: str):
        """Save trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model not trained yet!")
        
        model_data = {
            'model': self.model,
            'scaler': self.feature_scaler,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'training_stats': self.training_stats,
            'shutdown_threshold': self.shutdown_threshold,
            'spinup_threshold': self.spinup_threshold
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"✓ Model saved to {file_path}")
    
    def load_model(self, file_path: str):
        """Load trained model from disk."""
        with open(file_path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.model_type = model_data['model_type']
        self.training_stats = model_data['training_stats']
        self.shutdown_threshold = model_data.get('shutdown_threshold', 0.3)
        self.spinup_threshold = model_data.get('spinup_threshold', 0.85)
        self.is_trained = True
        
        print(f"✓ Model loaded from {file_path}")
    
    def get_deployment_info(self) -> Dict:
        """Get deployment-ready information."""
        return {
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'feature_names': self.feature_names,
            'training_stats': self.training_stats,
            'shutdown_threshold': self.shutdown_threshold,
            'spinup_threshold': self.spinup_threshold,
            'intercept': float(self.model.intercept_) if hasattr(self.model, 'intercept_') else None,
            'feature_importance': self.get_feature_importance()
        }
