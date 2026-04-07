"""
Integrated Predictor - Uses pre-trained RPS and Server models.

This module loads and orchestrates the two pre-trained models:
1. RPS Predictor: Predicts requests per second from temporal features
2. Server Predictor: Predicts servers needed from RPS

Feature set (YEARLY):
- hour: 0-23
- day_of_year: 1-365
- day_of_week: 0-6 (Monday=0, Sunday=6)
- is_weekend: 0-1
- is_holiday: 0-1
"""

import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os


class IntegratedPredictor:
    """
    Loads pre-trained RPS and Server models and provides unified predictions.
    
    Two-stage prediction:
    Stage 1: Temporal features → RPS Predictor → Predicted RPS
    Stage 2: Predicted RPS → Server Predictor → Servers Needed
    """
    
    def __init__(self, 
                 rps_model_path: str = None,
                 server_model_path: str = None):
        """
        Initialize with pre-trained models.
        
        Args:
            rps_model_path: Path to RPS predictor pickle
            server_model_path: Path to Server predictor pickle
        """
        # Default paths
        if rps_model_path is None:
            rps_model_path = r"c:\Users\PC\Downloads\rps_predictor.pkl"
        if server_model_path is None:
            server_model_path = r"c:\Users\PC\Downloads\server_predictor.pkl"
        
        self.rps_model_path = rps_model_path
        self.server_model_path = server_model_path
        
        self.rps_model = None
        self.server_model = None
        self.is_loaded = False
        
        # Load models
        self._load_models()
        
        # Tracking
        self.prediction_history = []
        self.statistics = {
            'predictions_made': 0,
            'avg_rps': 0.0,
            'avg_servers': 0.0,
            'max_rps': 0.0,
            'max_servers': 0
        }
    
    def _load_models(self):
        """Load both pre-trained models from disk."""
        try:
            # Load RPS model
            if os.path.exists(self.rps_model_path):
                print(f"Loading RPS model from {self.rps_model_path}...")
                self.rps_model = self._load_pickle_file(self.rps_model_path)
                if self.rps_model is not None:
                    print(f"✓ RPS model loaded successfully")
                else:
                    print(f"✗ Failed to load RPS model")
            else:
                print(f"⚠ RPS model not found at {self.rps_model_path}")
            
            # Load Server model
            if os.path.exists(self.server_model_path):
                print(f"Loading Server model from {self.server_model_path}...")
                self.server_model = self._load_pickle_file(self.server_model_path)
                if self.server_model is not None:
                    print(f"✓ Server model loaded successfully")
                else:
                    print(f"✗ Failed to load Server model")
            else:
                print(f"⚠ Server model not found at {self.server_model_path}")
            
            self.is_loaded = (self.rps_model is not None and 
                            self.server_model is not None)
            
            if not self.is_loaded:
                print(f"✗ ERROR: Could not load one or both models!")
                print(f"   RPS model: {'✓' if self.rps_model else '✗'}")
                print(f"   Server model: {'✓' if self.server_model else '✗'}")
            
        except Exception as e:
            print(f"✗ Unexpected error loading models: {e}")
            import traceback
            traceback.print_exc()
            self.is_loaded = False
    
    def _load_pickle_file(self, filepath: str):
        """
        Load pickle file with multiple fallback strategies.
        
        Handles:
        - Joblib (preferred for sklearn models)
        - Standard pickle protocol
        - Different encodings
        - Protocol version mismatches
        """
        # Strategy 1: Try joblib first (best for sklearn models)
        try:
            import joblib
            model = joblib.load(filepath)
            return model
        except ImportError:
            pass
        except Exception as e:
            print(f"   (joblib load failed: {e})")
        
        # Strategy 2: Try standard pickle load
        try:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            return model
            
        except (pickle.UnpicklingError, ValueError) as e:
            # Strategy 3: Try with different encoding
            try:
                with open(filepath, 'rb') as f:
                    model = pickle.load(f, encoding='latin1')
                return model
            except:
                pass
        
        except Exception as e:
            pass
        
        # All strategies failed
        print(f"✗ Could not load {filepath}")
        return None
    
    def get_temporal_features(self, timestamp: datetime = None, 
                             is_holiday: bool = False) -> Dict:
        """
        Extract temporal features from timestamp (YEARLY format).
        
        Returns: {
            'hour': 0-23,
            'day_of_year': 1-365,
            'day_of_week': 0-6,
            'is_weekend': 0-1,
            'is_holiday': 0-1
        }
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday  # 1-365/366
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        is_weekend = 1 if day_of_week >= 5 else 0
        is_holiday_flag = 1 if is_holiday else 0
        
        return {
            'hour': hour,
            'day_of_year': day_of_year,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'is_holiday': is_holiday_flag,
            'timestamp': timestamp.isoformat()
        }
    
    def predict_rps(self, timestamp: datetime = None, 
                   is_holiday: bool = False) -> float:
        """
        Predict RPS (requests per second) for given timestamp.
        
        Args:
            timestamp: Target time to predict for
            is_holiday: Whether it's a holiday
        
        Returns: Predicted RPS (float)
        """
        if not self.is_loaded or self.rps_model is None:
            raise RuntimeError("RPS model not loaded!")
        
        # Get features
        features_dict = self.get_temporal_features(timestamp, is_holiday)
        
        # Create feature array in correct order
        features = np.array([[
            features_dict['hour'],
            features_dict['day_of_year'],
            features_dict['day_of_week'],
            features_dict['is_weekend'],
            features_dict['is_holiday']
        ]])
        
        # Predict RPS
        predicted_rps = self.rps_model.predict(features)[0]
        
        # Ensure positive
        predicted_rps = max(0.1, predicted_rps)
        
        return predicted_rps
    
    def predict_servers(self, rps: float) -> int:
        """
        Predict servers needed for given RPS.
        
        Args:
            rps: Requests per second
        
        Returns: Number of servers needed (int)
        """
        if not self.is_loaded or self.server_model is None:
            raise RuntimeError("Server model not loaded!")
        
        # Create feature array
        features = np.array([[rps]])
        
        # Predict servers
        predicted_servers = self.server_model.predict(features)[0]
        
        # Round up to nearest integer, minimum 1
        servers_needed = int(np.ceil(max(1, predicted_servers)))
        
        return servers_needed
    
    def predict_full_pipeline(self, timestamp: datetime = None,
                             is_holiday: bool = False) -> Dict:
        """
        Complete two-stage prediction: temporal → RPS → Servers.
        
        Returns: {
            'timestamp': ISO timestamp,
            'features': temporal features dict,
            'predicted_rps': float,
            'predicted_servers': int,
            'confidence': float (0-1)
        }
        """
        features_dict = self.get_temporal_features(timestamp, is_holiday)
        
        # Stage 1: Predict RPS
        predicted_rps = self.predict_rps(timestamp, is_holiday)
        
        # Stage 2: Predict Servers from RPS
        predicted_servers = self.predict_servers(predicted_rps)
        
        # Confidence: higher RPS uncertainty = lower confidence
        # Conservative estimate: typical RPS ranges 100-10000
        confidence = min(0.95, 1.0 - abs(predicted_rps - 1000) / 5000)
        confidence = max(0.5, confidence)
        
        result = {
            'timestamp': features_dict['timestamp'],
            'temporal_features': features_dict,
            'predicted_rps': float(predicted_rps),
            'predicted_servers': int(predicted_servers),
            'confidence': float(confidence),
            'pipeline': 'temporal_features → rps_model → server_model'
        }
        
        # Track statistics
        self._update_statistics(predicted_rps, predicted_servers)
        self.prediction_history.append(result)
        
        return result
    
    def _update_statistics(self, rps: float, servers: int):
        """Update running statistics."""
        n = self.statistics['predictions_made']
        
        # Running average
        self.statistics['avg_rps'] = (
            (self.statistics['avg_rps'] * n + rps) / (n + 1)
        )
        self.statistics['avg_servers'] = (
            (self.statistics['avg_servers'] * n + servers) / (n + 1)
        )
        
        # Max values
        self.statistics['max_rps'] = max(
            self.statistics['max_rps'], rps
        )
        self.statistics['max_servers'] = max(
            self.statistics['max_servers'], servers
        )
        
        self.statistics['predictions_made'] += 1
    
    def predict_day_profile(self, target_date: datetime,
                           is_holiday: bool = False) -> List[Dict]:
        """
        Predict RPS and servers for entire day (hourly).
        
        Returns: List of predictions for each hour
        """
        predictions = []
        current = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for hour in range(24):
            current = current.replace(hour=hour)
            pred = self.predict_full_pipeline(current, is_holiday)
            predictions.append({
                'hour': hour,
                'rps': pred['predicted_rps'],
                'servers': pred['predicted_servers']
            })
        
        return predictions
    
    def predict_week_ahead(self, start_date: datetime = None) -> Dict:
        """
        Predict RPS and servers for next 7 days (daily peaks).
        
        Returns: {
            'start_date': date,
            'daily_predictions': List[{date, peak_rps, peak_servers, avg_servers}],
            'week_avg_servers': float,
            'week_peak_rps': float,
            'week_peak_servers': int
        }
        """
        if start_date is None:
            start_date = datetime.now().replace(hour=0, minute=0, second=0)
        
        daily_predictions = []
        all_servers = []
        all_rps = []
        
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            is_holiday = False  # You can add holiday logic here
            
            # Get daily profile (hourly)
            hourly = self.predict_day_profile(current_date, is_holiday)
            
            daily_data = {
                'date': current_date.date().isoformat(),
                'day_of_week': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][
                    current_date.weekday()
                ],
                'peak_rps': max(h['rps'] for h in hourly),
                'peak_servers': max(h['servers'] for h in hourly),
                'avg_servers': int(np.mean([h['servers'] for h in hourly])),
                'hourly': hourly
            }
            
            daily_predictions.append(daily_data)
            all_servers.extend([h['servers'] for h in hourly])
            all_rps.extend([h['rps'] for h in hourly])
        
        return {
            'start_date': start_date.date().isoformat(),
            'daily_predictions': daily_predictions,
            'week_avg_servers': float(np.mean(all_servers)),
            'week_peak_rps': float(max(all_rps)),
            'week_peak_servers': int(max(all_servers)),
            'week_min_servers': int(min(all_servers))
        }
    
    def predict_year_ahead(self, start_date: datetime = None) -> Dict:
        """
        Predict monthly capacity for entire year.
        
        Returns: Monthly aggregated predictions
        """
        if start_date is None:
            start_date = datetime.now().replace(
                month=1, day=1, hour=0, minute=0, second=0
            )
        
        monthly_data = []
        
        for month in range(1, 13):
            # Get first day of month
            month_start = start_date.replace(month=month, day=1)
            
            # Get 7 predictions throughout the month (1st, 8th, 15th, 22nd, 29th)
            sample_days = [1, 8, 15, 22, 29]
            month_predictions = []
            
            for day in sample_days:
                try:
                    sample_date = month_start.replace(day=day)
                    daily_profile = self.predict_day_profile(sample_date, False)
                    month_predictions.extend([h['servers'] for h in daily_profile])
                except:
                    pass
            
            if month_predictions:
                monthly_data.append({
                    'month': month,
                    'month_name': [
                        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
                    ][month - 1],
                    'avg_servers': float(np.mean(month_predictions)),
                    'peak_servers': int(max(month_predictions)),
                    'min_servers': int(min(month_predictions))
                })
        
        return {
            'year': start_date.year,
            'monthly_data': monthly_data,
            'yearly_avg_servers': float(
                np.mean([m['avg_servers'] for m in monthly_data])
            ),
            'yearly_peak_servers': int(
                max(m['peak_servers'] for m in monthly_data)
            )
        }
    
    def get_statistics(self) -> Dict:
        """Get predictor statistics."""
        return {
            **self.statistics,
            'models_loaded': self.is_loaded,
            'rps_model_path': self.rps_model_path,
            'server_model_path': self.server_model_path,
            'prediction_history_length': len(self.prediction_history)
        }
    
    def batch_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Batch predict RPS and servers for DataFrame.
        
        DataFrame should have columns: hour, day_of_year, day_of_week, is_weekend, is_holiday
        """
        results = []
        
        for idx, row in df.iterrows():
            try:
                rps = self.rps_model.predict([[
                    row['hour'],
                    row['day_of_year'],
                    row['day_of_week'],
                    row['is_weekend'],
                    row['is_holiday']
                ]])[0]
                
                servers = self.server_model.predict([[rps]])[0]
                servers = int(np.ceil(max(1, servers)))
                
                results.append({
                    'predicted_rps': float(rps),
                    'predicted_servers': servers
                })
            except Exception as e:
                results.append({
                    'predicted_rps': 0.0,
                    'predicted_servers': 1,
                    'error': str(e)
                })
        
        result_df = pd.DataFrame(results)
        return pd.concat([df, result_df], axis=1)


# Convenience function
def get_servers_for_time(hour: int, day_of_year: int, day_of_week: int,
                        is_weekend: int, is_holiday: int) -> int:
    """
    Quick function to get server prediction for given temporal parameters.
    
    Example:
        servers = get_servers_for_time(
            hour=20,
            day_of_year=180,
            day_of_week=6,
            is_weekend=1,
            is_holiday=0
        )
    """
    predictor = IntegratedPredictor()
    
    if not predictor.is_loaded:
        print("ERROR: Models not loaded")
        return 1
    
    rps = predictor.rps_model.predict([[
        hour, day_of_year, day_of_week, is_weekend, is_holiday
    ]])[0]
    
    servers = predictor.server_model.predict([[rps]])[0]
    servers = int(np.ceil(max(1, servers)))
    
    return servers
