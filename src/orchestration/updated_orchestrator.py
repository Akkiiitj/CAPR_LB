"""
Updated Proactive Orchestrator using pre-trained RPS and Server models.

This version:
- Uses integrated_predictor.py for RPS → Servers predictions
- Works with yearly temporal features (day_of_year instead of monthly)
- Maintains all orchestration logic
- Makes proactive decisions 5-10 min ahead
"""

from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from src.models.integrated_predictor import IntegratedPredictor
from src.policies.spike_aware_rearrangement import SpikeAwarePriorityPolicy
from src.rl.enhanced_q_learning_agent import EnhancedQLearningAgent


class SystemAction(Enum):
    """Possible system actions."""
    ADD_SERVERS = "add_servers"
    REMOVE_SERVERS = "remove_servers"
    REARRANGE_QUEUE = "rearrange_queue"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY_SCALING = "emergency_scaling"


class UpdatedProactiveOrchestrator:
    """
    Maintains all proactive orchestration logic with integrated predictors.
    Uses pre-trained RPS and Server prediction models.
    """
    
    def __init__(self,
                 integrated_predictor: IntegratedPredictor = None,
                 q_learning_agent: EnhancedQLearningAgent = None,
                 rearrangement_policy: SpikeAwarePriorityPolicy = None,
                 lookahead_window: int = 10,
                 confidence_threshold: float = 0.7):
        """
        Initialize orchestrator with integrated models.
        
        Args:
            integrated_predictor: RPS + Server predictor (loads models from disk)
            q_learning_agent: Optional Q-Learning agent
            rearrangement_policy: Queue rearrangement policy
            lookahead_window: Minutes to look ahead (default: 10)
            confidence_threshold: Minimum confidence for action (0-1)
        """
        if integrated_predictor is None:
            integrated_predictor = IntegratedPredictor()
        
        self.integrated_predictor = integrated_predictor
        self.q_learning_agent = q_learning_agent
        self.rearrangement_policy = rearrangement_policy
        
        self.lookahead_window = lookahead_window
        self.confidence_threshold = confidence_threshold
        
        # Tracking
        self.decision_history = []
        self.action_history = []
        self.metrics = {
            'proactive_actions': 0,
            'reactive_actions': 0,
            'maintain_actions': 0,
            'total_decisions': 0
        }
    
    def get_temporal_state(self, timestamp: datetime = None,
                          is_holiday: bool = False) -> Dict:
        """Get current temporal state for predictions."""
        if timestamp is None:
            timestamp = datetime.now()
        
        return self.integrated_predictor.get_temporal_features(timestamp, is_holiday)
    
    def predict_future_rps(self, minutes_ahead: int = None) -> float:
        """
        Predict RPS at future time (N minutes from now).
        """
        if minutes_ahead is None:
            minutes_ahead = self.lookahead_window
        
        future_time = datetime.now() + timedelta(minutes=minutes_ahead)
        predicted_rps = self.integrated_predictor.predict_rps(future_time)
        
        return predicted_rps
    
    def predict_future_servers(self, minutes_ahead: int = None) -> int:
        """
        Predict servers needed N minutes from now.
        """
        if minutes_ahead is None:
            minutes_ahead = self.lookahead_window
        
        future_time = datetime.now() + timedelta(minutes=minutes_ahead)
        prediction = self.integrated_predictor.predict_full_pipeline(future_time)
        
        return prediction['predicted_servers']
    
    def get_decision(self,
                    current_rps: float,
                    current_servers: int,
                    max_servers: int,
                    queue_depth: int = 0,
                    timestamp: datetime = None,
                    is_holiday: bool = False) -> Tuple[SystemAction, Dict]:
        """
        Make proactive decision based on current state and future predictions.
        
        Decision logic:
        1. Predict future RPS (10 min ahead)
        2. Predict future servers needed
        3. Compare with current state
        4. Act proactively
        
        Args:
            current_rps: Current requests per second
            current_servers: Active servers now
            max_servers: Maximum available servers
            queue_depth: Current queue length
            timestamp: Current time
            is_holiday: Is today a holiday?
        
        Returns: (action, decision_details)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Get future predictions
        future_rps = self.predict_future_rps(self.lookahead_window)
        future_servers = self.predict_future_servers(self.lookahead_window)
        
        # Calculate trends
        rps_trend = (future_rps - current_rps) / max(current_rps, 0.1)
        server_gap = future_servers - current_servers
        
        # Confidence: based on prediction agreement
        confidence = min(1.0, abs(rps_trend) + 0.5)
        
        decision_details = {
            'timestamp': timestamp.isoformat(),
            'current_state': {
                'rps': current_rps,
                'servers': current_servers,
                'queue': queue_depth
            },
            'future_state': {
                'rps': future_rps,
                'servers': future_servers,
                'lookahead_minutes': self.lookahead_window
            },
            'trends': {
                'rps_change_percent': rps_trend * 100,
                'server_gap': server_gap
            },
            'confidence': confidence
        }
        
        # Decision logic
        action = SystemAction.MAINTAIN
        
        if confidence < self.confidence_threshold:
            action = SystemAction.MAINTAIN
            decision_details['reason'] = "Low confidence - maintaining"
        
        elif server_gap > 2 and current_servers < max_servers:
            # Spike coming - proactively add servers
            action = SystemAction.ADD_SERVERS
            decision_details['reason'] = f"Proactive: spike incoming, need {future_servers} servers"
            decision_details['is_proactive'] = True
            self.metrics['proactive_actions'] += 1
        
        elif future_rps > (current_rps * 1.3) and queue_depth > 10:
            # High RPS increase + queue building
            action = SystemAction.ADD_SERVERS
            decision_details['reason'] = "Proactive: RPS surge detected"
            decision_details['is_proactive'] = True
            self.metrics['proactive_actions'] += 1
        
        elif server_gap < -3 and queue_depth < 5:
            # Over-provisioned - scale down
            action = SystemAction.SCALE_DOWN
            decision_details['reason'] = f"Over-provisioned: {current_servers} > {future_servers}"
            decision_details['servers_to_remove'] = abs(server_gap)
        
        elif queue_depth > 20:
            # Queue overload - reactive action
            if current_servers < max_servers * 0.8:
                action = SystemAction.ADD_SERVERS
                decision_details['reason'] = "Reactive: queue overload"
                self.metrics['reactive_actions'] += 1
            else:
                action = SystemAction.REARRANGE_QUEUE
                decision_details['reason'] = "Queue full - rearrange by priority"
        
        else:
            self.metrics['maintain_actions'] += 1
        
        self.metrics['total_decisions'] += 1
        
        # Log decision
        self.decision_history.append(decision_details)
        
        return action, decision_details
    
    def get_daily_forecast(self, target_date: datetime = None,
                          is_holiday: bool = False) -> Dict:
        """
        Get hourly RPS and server forecast for entire day.
        """
        if target_date is None:
            target_date = datetime.now()
        
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_profile = self.integrated_predictor.predict_day_profile(target_date, is_holiday)
        
        return {
            'date': target_date.date().isoformat(),
            'is_holiday': is_holiday,
            'hourly_profile': daily_profile,
            'peak_rps': max(h['rps'] for h in daily_profile),
            'peak_servers': max(h['servers'] for h in daily_profile),
            'avg_servers': int(np.mean([h['servers'] for h in daily_profile])),
            'min_servers': min(h['servers'] for h in daily_profile)
        }
    
    def get_weekly_forecast(self, start_date: datetime = None) -> Dict:
        """Get 7-day server forecast."""
        return self.integrated_predictor.predict_week_ahead(start_date)
    
    def get_yearly_capacity_plan(self, year: int = None) -> Dict:
        """
        Get yearly capacity planning data.
        Useful for budgeting and long-term planning.
        """
        if year is None:
            year = datetime.now().year
        
        start_date = datetime(year, 1, 1)
        return self.integrated_predictor.predict_year_ahead(start_date)
    
    def get_performance_metrics(self) -> Dict:
        """Get orchestrator performance metrics."""
        total = self.metrics['total_decisions']
        
        return {
            **self.metrics,
            'proactive_ratio': (
                self.metrics['proactive_actions'] / max(total, 1)
            ),
            'decision_history_length': len(self.decision_history),
            'models_loaded': self.integrated_predictor.is_loaded
        }
    
    def simulate_day(self, target_date: datetime = None,
                    decision_interval_minutes: int = 5) -> Dict:
        """
        Simulate a full day's decisions with regular intervals.
        Useful for testing and validation.
        """
        if target_date is None:
            target_date = datetime.now()
        
        target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        simulation_results = {
            'date': target_date.date().isoformat(),
            'decisions': [],
            'actions_taken': []
        }
        
        current_servers = 5  # Starting point
        current_rps = 100
        
        # Simulate for each interval throughout the day
        current_time = target_date
        end_time = target_date + timedelta(days=1)
        
        while current_time < end_time:
            # Get decision
            action, details = self.get_decision(
                current_rps=current_rps,
                current_servers=current_servers,
                max_servers=20,
                queue_depth=int(current_rps / 10),
                timestamp=current_time
            )
            
            simulation_results['decisions'].append(details)
            
            # Update servers based on action
            if action == SystemAction.ADD_SERVERS:
                current_servers = min(20, current_servers + 2)
                simulation_results['actions_taken'].append({
                    'time': current_time.isoformat(),
                    'action': 'add_servers',
                    'new_server_count': current_servers
                })
            elif action == SystemAction.SCALE_DOWN:
                current_servers = max(1, current_servers - 1)
                simulation_results['actions_taken'].append({
                    'time': current_time.isoformat(),
                    'action': 'scale_down',
                    'new_server_count': current_servers
                })
            
            # Get RPS for next interval
            future_pred = self.integrated_predictor.predict_full_pipeline(
                current_time + timedelta(minutes=decision_interval_minutes)
            )
            current_rps = future_pred['predicted_rps']
            
            current_time += timedelta(minutes=decision_interval_minutes)
        
        return simulation_results
    
    def get_status(self) -> Dict:
        """Get current orchestrator status."""
        return {
            'is_ready': self.integrated_predictor.is_loaded,
            'models_paths': {
                'rps_model': self.integrated_predictor.rps_model_path,
                'server_model': self.integrated_predictor.server_model_path
            },
            'lookahead_window': self.lookahead_window,
            'confidence_threshold': self.confidence_threshold,
            'decision_count': self.metrics['total_decisions'],
            'proactive_ratio': (
                self.metrics['proactive_actions'] / max(self.metrics['total_decisions'], 1)
            ),
            'latest_decision': self.decision_history[-1] if self.decision_history else None
        }


# Convenience function for quick decisions
def quick_decision(hour: int, day_of_year: int, day_of_week: int,
                  is_weekend: int, is_holiday: int,
                  current_servers: int,
                  queue_depth: int = 0) -> Dict:
    """
    Quick function to get server prediction and action recommendation.
    
    Example:
        result = quick_decision(
            hour=20,
            day_of_year=180,
            day_of_week=6,
            is_weekend=1,
            is_holiday=0,
            current_servers=8,
            queue_depth=15
        )
        print(f"Action: {result['action']}")
        print(f"Be proactive: {result['is_proactive']}")
    """
    orchestrator = UpdatedProactiveOrchestrator()
    
    if not orchestrator.integrated_predictor.is_loaded:
        return {
            'error': 'Models not loaded',
            'action': 'MAINTAIN'
        }
    
    # Get RPS prediction for this time
    predictor = orchestrator.integrated_predictor
    rps = predictor.rps_model.predict([[
        hour, day_of_year, day_of_week, is_weekend, is_holiday
    ]])[0]
    
    # Get server prediction
    servers_needed = predictor.server_model.predict([[rps]])[0]
    servers_needed = int(np.ceil(max(1, servers_needed)))
    
    # Get action
    action, details = orchestrator.get_decision(
        current_rps=rps,
        current_servers=current_servers,
        max_servers=20,
        queue_depth=queue_depth
    )
    
    return {
        'action': action.value,
        'reason': details.get('reason', ''),
        'predicted_rps': float(rps),
        'predicted_servers': servers_needed,
        'is_proactive': details.get('is_proactive', False),
        'confidence': details.get('confidence', 0),
        'details': details
    }
