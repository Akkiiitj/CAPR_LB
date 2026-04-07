"""
Advanced load predictor with temporal patterns, spike detection, and forecasting.
Supports holidays, time-of-day patterns, and demand spikes.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
import json


class AdvancedLoadPredictor:
    """Predicts system load using temporal patterns and spike detection."""
    
    def __init__(self, window=10, spike_threshold=1.5):
        self.window = window
        self.history = []  # (timestamp, load) tuples
        self.spike_threshold = spike_threshold  # Multiplier above baseline
        self.baseline = None
        self.spike_history = []
        
        # Time-of-day patterns (baseline multipliers)
        self.time_patterns = {
            'night': 0.3,      # 0-6: low load
            'morning': 0.8,    # 6-9: medium
            'business_hours': 1.2,  # 9-17: high
            'evening': 0.9,    # 17-20: medium
            'late_night': 0.4  # 20-24: low
        }
        
        # Day-of-week patterns
        self.day_patterns = {
            0: 0.9,   # Monday
            1: 1.0,   # Tuesday
            2: 1.0,   # Wednesday
            3: 0.95,  # Thursday
            4: 0.85,  # Friday (start of weekend drop)
            5: 0.5,   # Saturday (weekend)
            6: 0.4    # Sunday (weekend)
        }
    
    def add_measurement(self, queue_length: float, timestamp: datetime = None):
        """Add new queue length measurement."""
        if timestamp is None:
            timestamp = datetime.now()
        self.history.append((timestamp, queue_length))
    
    def moving_average(self, window: int = None) -> float:
        """Calculate moving average of queue lengths."""
        if window is None:
            window = self.window
        
        if not self.history:
            return 0
        
        loads = [load for _, load in self.history[-window:]]
        return sum(loads) / len(loads) if loads else 0
    
    def get_baseline_load(self) -> float:
        """Get baseline load (using moving average of recent history)."""
        if self.baseline is None:
            self.baseline = self.moving_average(window=max(20, self.window * 2))
        return self.baseline
    
    def get_time_factor(self, hour: int) -> float:
        """Get load multiplier based on time of day."""
        if 0 <= hour < 6:
            return self.time_patterns['night']
        elif 6 <= hour < 9:
            return self.time_patterns['morning']
        elif 9 <= hour < 17:
            return self.time_patterns['business_hours']
        elif 17 <= hour < 20:
            return self.time_patterns['evening']
        else:
            return self.time_patterns['late_night']
    
    def get_day_factor(self, day_of_week: int, is_holiday: bool = False) -> float:
        """Get load multiplier based on day of week and holiday status."""
        if is_holiday:
            return 0.3  # Holiday: 70% reduction
        return self.day_patterns.get(day_of_week, 1.0)
    
    def predict_load(self, timestamp: datetime = None, 
                    is_holiday: bool = False) -> float:
        """
        Predict load at given timestamp based on temporal patterns.
        
        Returns: predicted_load (float)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        baseline = self.get_baseline_load()
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        
        time_factor = self.get_time_factor(hour)
        day_factor = self.get_day_factor(day_of_week, is_holiday)
        
        predicted = baseline * time_factor * day_factor
        return predicted
    
    def detect_spike(self, current_load: float, 
                    minutes_back: int = 15) -> Tuple[bool, float]:
        """
        Detect if current load is anomalously high (spike).
        
        Returns: (is_spike: bool, spike_magnitude: float)
        """
        if len(self.history) < 5:
            return False, 1.0
        
        # Get average of recent history
        recent = [load for _, load in self.history[-(minutes_back):]]
        baseline = sum(recent) / len(recent) if recent else 1
        
        spike_magnitude = current_load / baseline if baseline > 0 else 1.0
        is_spike = spike_magnitude > self.spike_threshold
        
        if is_spike:
            self.spike_history.append((datetime.now(), spike_magnitude))
        
        return is_spike, spike_magnitude
    
    def predict_spike_probability(self, lookahead_minutes: int = 10) -> float:
        """
        Predict probability of spike in next N minutes.
        Based on spike history patterns.
        
        Returns: probability (0.0 to 1.0)
        """
        if len(self.spike_history) < 5:
            return 0.0
        
        # Recent spikes (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_spikes = [ts for ts, _ in self.spike_history 
                        if ts > one_hour_ago]
        
        if len(recent_spikes) == 0:
            return 0.0
        
        # Simple heuristic: if spikes happened recently, likely to happen again
        # Calculate spike frequency
        spike_frequency = len(recent_spikes) / 60.0  # spikes per minute
        probability = min(spike_frequency * lookahead_minutes, 1.0)
        
        return probability
    
    def get_extended_prediction(self, timestamps: List[datetime],
                               holiday_dates: List[datetime] = None
                               ) -> List[Dict]:
        """
        Get extended predictions for multiple timestamps.
        Useful for capacity planning.
        
        Returns: List of {timestamp, predicted_load, spike_probability}
        """
        if holiday_dates is None:
            holiday_dates = []
        
        predictions = []
        for ts in timestamps:
            is_holiday = any(ts.date() == hd.date() for hd in holiday_dates)
            predicted = self.predict_load(ts, is_holiday)
            spike_prob = self.predict_spike_probability()
            
            predictions.append({
                'timestamp': ts.isoformat(),
                'predicted_load': predicted,
                'spike_probability': spike_prob,
                'is_holiday': is_holiday
            })
        
        return predictions
    
    def forecast_for_day(self, target_date: datetime, 
                        is_holiday: bool = False) -> Dict:
        """Get detailed forecast for an entire day."""
        forecasts = []
        current = target_date.replace(hour=0, minute=0, second=0)
        end_of_day = current.replace(hour=23, minute=59, second=59)
        
        while current <= end_of_day:
            hour = current.hour
            predicted = self.predict_load(current, is_holiday)
            forecasts.append({
                'hour': hour,
                'load': predicted,
                'time_factor': self.get_time_factor(hour),
                'day_factor': self.get_day_factor(current.weekday(), is_holiday)
            })
            current += timedelta(hours=1)
        
        return {
            'date': target_date.isoformat(),
            'is_holiday': is_holiday,
            'hourly_forecasts': forecasts,
            'peak_load': max(f['load'] for f in forecasts),
            'min_load': min(f['load'] for f in forecasts)
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about load patterns."""
        if not self.history:
            return {}
        
        loads = [load for _, load in self.history]
        return {
            'mean_load': np.mean(loads),
            'median_load': np.median(loads),
            'std_load': np.std(loads),
            'max_load': max(loads),
            'min_load': min(loads),
            'spike_count': len(self.spike_history),
            'observations': len(loads)
        }
