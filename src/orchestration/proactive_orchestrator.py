"""
Proactive Orchestrator - Ensemble coordinator for proactive load balancing.

Combines:
1. Linear server prediction (capacity planning)
2. Q-Learning agent (dynamic decisions)
3. Spike detection (pattern recognition)
4. Queue rearrangement (task prioritization)

Makes decisions 5-10 minutes AHEAD of actual demand spikes.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from enum import Enum


class SystemAction(Enum):
    """Possible system actions."""
    ADD_SERVERS = "add_servers"
    REMOVE_SERVERS = "remove_servers"
    REARRANGE_QUEUE = "rearrange_queue"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY_SCALING = "emergency_scaling"


class ProactiveOrchestrator:
    """
    Master controller for proactive load balancing.
    Makes decisions based on ensemble of predictions.
    """
    
    def __init__(self,
                 linear_predictor,  # LinearServerPredictor
                 q_learning_agent,   # EnhancedQLearningAgent
                 rearrangement_policy,  # SpikeAwarePriorityPolicy
                 load_predictor,  # AdvancedLoadPredictor
                 lookahead_window: int = 10,  # Minutes to look ahead
                 confidence_threshold: float = 0.7):
        """
        Initialize orchestrator.
        
        Args:
            linear_predictor: Trained linear regression model
            q_learning_agent: Trained Q-learning agent
            rearrangement_policy: Queue rearrangement policy
            load_predictor: Advanced load predictor with spike detection
            lookahead_window: How many minutes to predict ahead
            confidence_threshold: Confidence level for taking action (0-1)
        """
        self.linear_predictor = linear_predictor
        self.q_learning_agent = q_learning_agent
        self.rearrangement_policy = rearrangement_policy
        self.load_predictor = load_predictor
        
        self.lookahead_window = lookahead_window
        self.confidence_threshold = confidence_threshold
        
        # State tracking
        self.current_state = None
        self.action_history = []
        self.decision_log = []
        self.metrics = {
            'proactive_actions': 0,
            'reactive_actions': 0,
            'correct_predictions': 0,
            'false_positives': 0,
            'avg_prediction_accuracy': 0.0,
            'avg_response_improvement': 0.0
        }
    
    def predict_future_load(self,
                           timestamp: datetime,
                           is_holiday: bool = False,
                           minutes_ahead: int = None) -> Dict:
        """
        Predict load N minutes into future using time-based patterns.
        """
        if minutes_ahead is None:
            minutes_ahead = self.lookahead_window
        
        future_time = timestamp + timedelta(minutes=minutes_ahead)
        
        # Use linear predictor for server needs
        predicted_servers = self.linear_predictor.predict_servers_needed(
            future_time, 
            queue_depth=0,  # Will be estimated
            resource_utilization=0.5,
            is_holiday=is_holiday
        )
        
        # Use load predictor for queue/spike forecast
        future_load = self.load_predictor.predict_load(future_time, is_holiday)
        spike_prob = self.load_predictor.predict_spike_probability(minutes_ahead)
        
        return {
            'timestamp': future_time,
            'predicted_servers_needed': predicted_servers,
            'predicted_queue_load': future_load,
            'spike_probability': spike_prob,
            'is_holiday': is_holiday,
            'lookahead_minutes': minutes_ahead
        }
    
    def get_ensemble_prediction(self,
                               timestamp: datetime,
                               current_queue_depth: int,
                               current_servers_active: int,
                               max_servers: int,
                               is_holiday: bool = False) -> Dict:
        """
        Get ensemble prediction combining multiple models.
        """
        # Prediction 1: Linear model
        linear_pred = self.linear_predictor.predict_servers_needed(
            timestamp,
            queue_depth=current_queue_depth,
            resource_utilization=current_servers_active / max_servers,
            is_holiday=is_holiday
        )
        
        # Prediction 2: Q-Learning analysis
        state = self.q_learning_agent.get_state(
            current_queue_depth,
            current_queue_depth,
            current_servers_active,
            0.0
        )
        ql_action, ql_confidence = self.q_learning_agent.get_recommended_action(
            current_queue_depth,
            current_queue_depth,
            current_servers_active,
            max_servers
        )
        
        # Prediction 3: Load prediction with spike detection
        future_load = self.load_predictor.predict_load(timestamp, is_holiday)
        spike_prob = self.load_predictor.predict_spike_probability(self.lookahead_window)
        
        # Ensemble averaging
        ensemble_servers = (linear_pred * 0.5 + current_servers_active * 0.3 + 
                          (max_servers * spike_prob) * 0.2)
        
        # Confidence calculation
        confidence = min(1.0, spike_prob + abs(future_load - current_queue_depth) / max_servers)
        
        return {
            'timestamp': timestamp,
            'linear_prediction': linear_pred,
            'ql_recommendation': ql_action,
            'spike_probability': spike_prob,
            'ensemble_servers_needed': int(np.ceil(ensemble_servers)),
            'confidence': confidence,
            'future_load_estimate': future_load,
            'predictions': {
                'linear': linear_pred,
                'spike_signal': spike_prob,
                'future_queue': future_load
            }
        }
    
    def decide_action(self,
                     timestamp: datetime,
                     current_queue_depth: int,
                     current_servers_active: int,
                     max_servers: int,
                     ensemble_pred: Dict = None,
                     is_holiday: bool = False) -> Tuple[SystemAction, Dict]:
        """
        Make proactive action decision based on ensemble predictions.
        
        Returns: (action, decision_details)
        """
        if ensemble_pred is None:
            ensemble_pred = self.get_ensemble_prediction(
                timestamp, current_queue_depth, current_servers_active, 
                max_servers, is_holiday
            )
        
        confidence = ensemble_pred['confidence']
        
        decision_details = {
            'timestamp': timestamp.isoformat(),
            'current_state': {
                'queue_depth': current_queue_depth,
                'active_servers': current_servers_active,
                'utilization': current_servers_active / max_servers
            },
            'prediction': ensemble_pred,
            'confidence': confidence,
            'is_proactive': False
        }
        
        # Extract key signals
        servers_needed = ensemble_pred['ensemble_servers_needed']
        spike_prob = ensemble_pred['spike_probability']
        future_load = ensemble_pred['future_load_estimate']
        
        # Decision logic
        if confidence < self.confidence_threshold:
            # Low confidence - maintain current state
            action = SystemAction.MAINTAIN
            decision_details['reason'] = "Low confidence"
        
        elif spike_prob > 0.7 and current_servers_active < servers_needed:
            # Spike detected - proactively ADD servers
            action = SystemAction.ADD_SERVERS
            decision_details['reason'] = f"Proactive: spike probability {spike_prob:.2f}"
            decision_details['is_proactive'] = True
            decision_details['servers_to_add'] = servers_needed - current_servers_active
            self.metrics['proactive_actions'] += 1
        
        elif spike_prob > 0.5 and current_queue_depth > 15:
            # High load and high spike probability - REARRANGE AND POSSIBLY ADD
            action = SystemAction.REARRANGE_QUEUE
            if current_servers_active < servers_needed:
                action = SystemAction.ADD_SERVERS
            decision_details['reason'] = "High queue + spike probability - rearrange/add"
            decision_details['is_proactive'] = True
        
        elif current_servers_active > servers_needed + 2 and current_queue_depth < 5:
            # Over-provisioned - SCALE DOWN
            action = SystemAction.SCALE_DOWN
            decision_details['reason'] = f"Over-provisioned: {current_servers_active} > {servers_needed}"
            decision_details['servers_to_remove'] = max(1, current_servers_active - servers_needed)
        
        elif current_queue_depth > 20 and spike_prob < 0.5:
            # Reactive: Queue overload without spike - add servers reactively
            action = SystemAction.ADD_SERVERS
            decision_details['reason'] = "Reactive: queue overload"
            decision_details['servers_to_add'] = 2
            self.metrics['reactive_actions'] += 1
        
        else:
            # Maintain current state
            action = SystemAction.MAINTAIN
            decision_details['reason'] = "Stable state"
        
        # Log decision
        self.decision_log.append(decision_details)
        
        return action, decision_details
    
    def execute_action(self,
                      action: SystemAction,
                      servers: List,
                      queue: List,
                      decision_details: Dict,
                      env = None) -> Dict:
        """
        Execute action and return result.
        """
        result = {
            'action': action.value,
            'timestamp': decision_details['timestamp'],
            'success': False,
            'details': {}
        }
        
        if action == SystemAction.ADD_SERVERS:
            servers_to_add = decision_details.get('servers_to_add', 1)
            # In real system: spin up new server instances
            result['servers_to_add'] = servers_to_add
            result['success'] = True
            result['details'] = f"Added {servers_to_add} servers"
        
        elif action == SystemAction.REMOVE_SERVERS:
            servers_to_remove = decision_details.get('servers_to_remove', 1)
            result['servers_to_remove'] = servers_to_remove
            result['success'] = True
            result['details'] = f"Removed {servers_to_remove} servers"
        
        elif action == SystemAction.SCALE_DOWN:
            servers_to_remove = decision_details.get('servers_to_remove', 1)
            result['success'] = True
            result['details'] = f"Scaled down by {servers_to_remove} servers"
        
        elif action == SystemAction.REARRANGE_QUEUE:
            # Trigger queue rearrangement
            if self.rearrangement_policy and queue:
                current_time = env.now if env else 0
                rearranged = self.rearrangement_policy.rearrange_queue(
                    queue, current_time, len(servers)
                )
                result['success'] = True
                result['details'] = f"Rearranged queue of {len(queue)} tasks"
        
        elif action == SystemAction.MAINTAIN:
            result['success'] = True
            result['details'] = "Maintaining current state"
        
        elif action == SystemAction.EMERGENCY_SCALING:
            # Spin up maximum servers
            result['success'] = True
            result['details'] = "Emergency scaling activated"
        
        self.action_history.append(result)
        return result
    
    def get_forecast_report(self,
                           timestamp: datetime,
                           hours_ahead: int = 24,
                           is_holiday: bool = False) -> Dict:
        """
        Generate comprehensive forecast report for the day.
        """
        forecasts = []
        for hour in range(hours_ahead):
            future_time = timestamp + timedelta(hours=hour)
            pred = self.predict_future_load(future_time, is_holiday, minutes_ahead=hour*60)
            forecasts.append(pred)
        
        peak_servers = max(p['predicted_servers_needed'] for p in forecasts)
        peak_time = max(forecasts, key=lambda p: p['predicted_servers_needed'])['timestamp']
        
        return {
            'start_time': timestamp.isoformat(),
            'hours_ahead': hours_ahead,
            'peak_servers_needed': peak_servers,
            'peak_time': peak_time.isoformat() if peak_time else None,
            'hourly_forecasts': forecasts,
            'summary': {
                'avg_servers_needed': np.mean([p['predicted_servers_needed'] for p in forecasts]),
                'max_queue_load': max(p['predicted_queue_load'] for p in forecasts)
            }
        }
    
    def get_performance_metrics(self) -> Dict:
        """Get orchestrator performance metrics."""
        return {
            **self.metrics,
            'total_decisions': len(self.decision_log),
            'proactive_ratio': (self.metrics['proactive_actions'] / 
                              max(1, self.metrics['proactive_actions'] + 
                                  self.metrics['reactive_actions'])),
            'action_history_length': len(self.action_history)
        }
    
    def compare_with_baseline(self,
                            proactive_results: Dict,
                            baseline_results: Dict) -> Dict:
        """
        Compare proactive approach with non-proactive baseline.
        """
        return {
            'proactive_avg_response_time': proactive_results.get('avg_response_time', 0),
            'baseline_avg_response_time': baseline_results.get('avg_response_time', 0),
            'improvement_percent': (
                (baseline_results.get('avg_response_time', 1) - 
                 proactive_results.get('avg_response_time', 0)) / 
                max(baseline_results.get('avg_response_time', 1), 0.001)
            ) * 100,
            'proactive_sla_compliance': proactive_results.get('sla_compliance', 0),
            'baseline_sla_compliance': baseline_results.get('sla_compliance', 0),
            'cost_savings': proactive_results.get('server_hours', 0) - 
                          baseline_results.get('server_hours', 0)
        }
    
    def get_status_summary(self) -> Dict:
        """Get current orchestrator status."""
        return {
            'initialized': all([
                self.linear_predictor,
                self.q_learning_agent,
                self.rearrangement_policy
            ]),
            'decisions_made': len(self.decision_log),
            'actions_executed': len(self.action_history),
            'proactive_actions': self.metrics['proactive_actions'],
            'reactive_actions': self.metrics['reactive_actions'],
            'lookahead_window_minutes': self.lookahead_window,
            'confidence_threshold': self.confidence_threshold,
            'latest_decision': self.decision_log[-1] if self.decision_log else None
        }
