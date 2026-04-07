"""
Multi-Horizon Proactive Orchestrator
Combines hourly planning with real-time 10-minute lookahead
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from src.models.integrated_predictor import IntegratedPredictor
from src.policies.spike_aware_rearrangement import SpikeAwarePriorityPolicy
from enum import Enum


class DecisionTimescale(Enum):
    """Different prediction horizons"""
    IMMEDIATE = "10min_lookahead"      # Real-time (5-10 min ahead)
    HOURLY = "next_hour"                # Hourly planning
    DAILY = "daily_plan"                # Daily capacity
    WEEKLY = "weekly_plan"              # Weekly trends


class MultiHorizonOrchestrator:
    """
    Orchestrator that makes decisions at multiple time scales:
    
    1. DAILY PLANNING (06:00 AM)
       - Predict all 24 hours
       - Identify peak times
       - Pre-allocate resources
    
    2. HOURLY CHECKPOINTS (every :00)
       - Predict next hour
       - Pre-warm servers 30 min before spike
       - Alert ops team
    
    3. REAL-TIME DECISIONS (every 5 min)
       - 10-min lookahead
       - Make immediate scaling decisions
       - Handle surprises
    """
    
    def __init__(self, lookahead_minutes: int = 10):
        self.predictor = IntegratedPredictor()
        self.policy = SpikeAwarePriorityPolicy()
        self.lookahead_minutes = lookahead_minutes
        
        # Daily plan (refreshed every 24 hours)
        self.daily_plan = None
        self.daily_plan_timestamp = None
        
        # Hourly alerts (refreshed every hour)
        self.next_hour_alert = None
        self.last_hour_check = None
    
    # ============================================================
    # LAYER 1: DAILY PLANNING (Call at 6 AM)
    # ============================================================
    
    def generate_daily_plan(self, target_date: datetime = None) -> Dict:
        """
        Generate daily capacity plan (24 hourly predictions)
        
        Call this ONCE per day at 6:00 AM
        """
        if target_date is None:
            target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_profile = self.predictor.predict_day_profile(target_date)
        
        # Analyze the day
        peaks = [h for h in daily_profile if h['peak']]
        valley = min(daily_profile, key=lambda x: x['servers'])
        peak = max(daily_profile, key=lambda x: x['servers'])
        avg = sum(h['servers'] for h in daily_profile) / len(daily_profile)
        
        # Identify spike windows (3+ consecutive peak hours)
        spike_windows = self._identify_spike_windows(daily_profile)
        
        self.daily_plan = {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
            'hourly_forecast': daily_profile,
            'summary': {
                'peak_servers': peak['servers'],
                'peak_hour': peak['hour'],
                'valley_servers': valley['servers'],
                'avg_servers': avg,
                'peak_hours_count': len(peaks),
                'spike_windows': spike_windows
            },
            'recommendations': self._generate_daily_recommendations(daily_profile)
        }
        
        self.daily_plan_timestamp = datetime.now()
        return self.daily_plan
    
    def _identify_spike_windows(self, hourly_data: List[Dict]) -> List[Dict]:
        """Find consecutive hours of peak demand"""
        windows = []
        current_window = None
        
        for hour_data in hourly_data:
            if hour_data['peak']:
                if current_window is None:
                    current_window = {
                        'start_hour': hour_data['hour'],
                        'servers': [hour_data['servers']]
                    }
                else:
                    current_window['servers'].append(hour_data['servers'])
            else:
                if current_window and len(current_window['servers']) >= 3:
                    current_window['end_hour'] = hourly_data[hourly_data.index(hour_data) - 1]['hour']
                    current_window['avg_servers'] = sum(current_window['servers']) / len(current_window['servers'])
                    windows.append(current_window)
                current_window = None
        
        return windows
    
    def _generate_daily_recommendations(self, hourly_data: List[Dict]) -> Dict:
        """Generate ops recommendations for the day"""
        spike_windows = self._identify_spike_windows(hourly_data)
        
        recommendations = []
        
        for window in spike_windows:
            pre_spike_hour = max(0, window['start_hour'] - 1)
            recommendations.append({
                'action': 'PRE_SCALE',
                'time': f"{pre_spike_hour:02d}:30",
                'reason': f"Spike window from {window['start_hour']:02d}:00-{window['end_hour']:02d}:00",
                'pre_scale_servers': int(window['avg_servers']),
                'message': f"Scale to {int(window['avg_servers'])} servers 30 min before spike"
            })
        
        return recommendations
    
    # ============================================================
    # LAYER 2: HOURLY CHECKPOINTS (Call every hour at :00)
    # ============================================================
    
    def hourly_checkpoint(self, current_servers: int) -> Dict:
        """
        Hourly decision point
        
        Call this EXACTLY at the top of each hour (:00)
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Get next hour prediction
        next_hour_time = now + timedelta(hours=1)
        daily_profile = self.predictor.predict_day_profile(now)
        
        # Find next hour in profile
        next_hour_data = None
        for h in daily_profile:
            if h['hour_value'] == next_hour_time.hour:
                next_hour_data = h
                break
        
        if next_hour_data is None:
            return {'error': 'Could not predict next hour'}
        
        servers_needed = next_hour_data['servers']
        is_peak = next_hour_data['peak']
        
        # Decision
        decision = {
            'timestamp': now.isoformat(),
            'current_hour': f"{current_hour:02d}:00",
            'next_hour': f"{next_hour_time.hour:02d}:00",
            'current_servers': current_servers,
            'predicted_servers': servers_needed,
            'is_peak': is_peak
        }
        
        if servers_needed > current_servers + 2:
            # Major spike coming - pre-warm
            decision['action'] = 'PRE_WARM'
            decision['servers_to_add'] = servers_needed - current_servers
            decision['message'] = f"Spike incoming! Pre-warm {decision['servers_to_add']} servers"
        elif servers_needed < current_servers - 2:
            # Low demand coming - scale down
            decision['action'] = 'STANDBY_REMOVE'
            decision['servers_to_remove'] = current_servers - servers_needed
            decision['message'] = f"Valley incoming. Can remove {decision['servers_to_remove']} servers"
        else:
            # Stable
            decision['action'] = 'HOURLY_STABLE'
            decision['message'] = "Next hour stable, maintain current servers"
        
        self.next_hour_alert = decision
        self.last_hour_check = now
        
        return decision
    
    # ============================================================
    # LAYER 3: REAL-TIME DECISIONS (Call every 5 minutes)
    # ============================================================
    
    def get_realtime_decision(self, 
                             current_rps: float,
                             current_servers: int,
                             queue_depth: int,
                             max_servers: int = 20) -> Tuple[str, Dict]:
        """
        Real-time 10-minute lookahead decision
        
        Call this every 5 minutes for immediate scaling
        """
        now = datetime.now()
        
        # Predict 10 minutes ahead
        future_time = now + timedelta(minutes=self.lookahead_minutes)
        
        # Get temporal features for future time
        future_rps = self.predictor.predict_rps(future_time)
        future_servers = self.predictor.predict_servers(future_rps)
        future_features = self.predictor.get_temporal_features(future_time)
        
        # Calculate gaps
        rps_gap = future_rps - current_rps
        rps_change_pct = (rps_gap / current_rps * 100) if current_rps > 0 else 0
        server_gap = future_servers - current_servers
        
        # Confidence (how sure are we?)
        confidence = self._calculate_confidence(rps_change_pct, future_features)
        
        # Decision logic
        decision_details = {
            'timestamp': now.isoformat(),
            'lookahead_minutes': self.lookahead_minutes,
            'current_state': {
                'rps': current_rps,
                'servers': current_servers,
                'queue': queue_depth
            },
            'predicted_state': {
                'rps': future_rps,
                'servers': future_servers
            },
            'trends': {
                'rps_change_pct': rps_change_pct,
                'server_gap': server_gap
            },
            'confidence': confidence
        }
        
        # Make decision
        action = self._make_realtime_decision(
            current_servers, server_gap, queue_depth, 
            confidence, rps_change_pct, max_servers
        )
        
        decision_details['action'] = action
        decision_details['reasoning'] = self._explain_decision(
            action, rps_change_pct, server_gap, confidence
        )
        
        return action, decision_details
    
    def _calculate_confidence(self, rps_change_pct: float, features: Dict) -> float:
        """
        Confidence score (0-1) based on:
        - Magnitude of predicted change
        - Time of day (predictable hours?)
        - Day type (weekday/weekend/holiday)
        """
        # Base confidence from RPS change magnitude
        if abs(rps_change_pct) < 5:
            base = 0.4  # Small change - low confidence
        elif abs(rps_change_pct) < 15:
            base = 0.6
        elif abs(rps_change_pct) < 30:
            base = 0.8
        else:
            base = 0.95  # Large jump - high confidence
        
        # Adjust by day type
        if features.get('is_holiday'):
            base *= 0.8  # Holidays less predictable
        
        return min(1.0, base)
    
    def _make_realtime_decision(self, current_servers: int, server_gap: int,
                                queue_depth: int, confidence: float,
                                rps_change_pct: float, max_servers: int) -> str:
        """Make the actual decision"""
        
        # Strong proactive add
        if server_gap > 2 and current_servers < max_servers and confidence > 0.7:
            return "ADD_SERVERS_PROACTIVE"
        
        # Reactive add (queue too deep)
        elif queue_depth > 20:
            return "ADD_SERVERS_REACTIVE"
        
        # Strong proactive remove
        elif server_gap < -3 and queue_depth < 5 and confidence > 0.7:
            return "REMOVE_SERVERS"
        
        # Queue intelligence
        elif queue_depth > 10 and rps_change_pct > 20:
            return "REARRANGE_QUEUE"
        
        # Stable
        else:
            return "MAINTAIN"
    
    def _explain_decision(self, action: str, rps_change: float, 
                         server_gap: int, confidence: float) -> str:
        """Human-readable explanation"""
        explanations = {
            'ADD_SERVERS_PROACTIVE': f"Proactive: {rps_change:+.0f}% RPS change incoming, gap={server_gap}, confidence={confidence:.0%}",
            'ADD_SERVERS_REACTIVE': f"Reactive: Queue too deep, need capacity now",
            'REMOVE_SERVERS': f"Proactive: Demand declining {rps_change:+.0f}%, over-provisioned (gap={server_gap})",
            'REARRANGE_QUEUE': f"Spike phase: Reorder queue to meet SLAs",
            'MAINTAIN': f"Stable: RPS {rps_change:+.0f}%, maintain current capacity"
        }
        return explanations.get(action, "Unknown decision")
    
    # ============================================================
    # INTEGRATED WORKFLOW
    # ============================================================
    
    def run_daily_workflow(self, current_servers: int, 
                          current_rps: float, queue_depth: int) -> Dict:
        """
        Complete daily workflow - combines all 3 layers
        
        Returns comprehensive decision package
        """
        now = datetime.now()
        hour_minute = now.strftime('%H:%M')
        
        # Check if daily plan needs refresh (6 AM)
        if self.daily_plan is None or now.hour == 6:
            daily_plan = self.generate_daily_plan()
        else:
            daily_plan = self.daily_plan
        
        # Check if hourly checkpoint (at :00)
        if now.minute == 0:
            hourly_check = self.hourly_checkpoint(current_servers)
        else:
            hourly_check = self.next_hour_alert
        
        # Always make real-time decision
        realtime_action, realtime_details = self.get_realtime_decision(
            current_rps, current_servers, queue_depth
        )
        
        return {
            'timestamp': now.isoformat(),
            'time': hour_minute,
            'daily_plan': daily_plan['summary'] if daily_plan else None,
            'hourly_checkpoint': hourly_check,
            'realtime_decision': {
                'action': realtime_action,
                'details': realtime_details
            }
        }
    
    # ============================================================
    # UTILITIES
    # ============================================================
    
    def get_status(self) -> Dict:
        """System status"""
        return {
            'daily_plan_set': self.daily_plan is not None,
            'last_hourly_check': self.last_hour_check.isoformat() if self.last_hour_check else None,
            'next_hour_alert': self.next_hour_alert
        }
    
    def format_daily_plan_for_ops(self) -> str:
        """Format daily plan as ops report"""
        if not self.daily_plan:
            return "No daily plan generated"
        
        report = f"\n{'='*60}\n"
        report += f"DAILY CAPACITY PLAN - {self.daily_plan['target_date']}\n"
        report += f"Generated: {self.daily_plan['generated_at']}\n"
        report += f"{'='*60}\n\n"
        
        s = self.daily_plan['summary']
        report += f"Peak: {s['peak_servers']} servers at {s['peak_hour']:02d}:00\n"
        report += f"Average: {s['avg_servers']:.0f} servers\n"
        report += f"Valley: {s['valley_servers']} servers\n"
        report += f"Peak Hours: {s['peak_hours_count']} hours\n\n"
        
        if s['spike_windows']:
            report += "SPIKE WINDOWS:\n"
            for i, window in enumerate(s['spike_windows'], 1):
                report += f"  Window {i}: {window['start_hour']:02d}:00-{window['end_hour']:02d}:00, "
                report += f"avg {window['avg_servers']:.0f} servers\n"
            report += "\n"
        
        report += "RECOMMENDATIONS:\n"
        for rec in self.daily_plan['recommendations']:
            report += f"  {rec['time']}: {rec['message']}\n"
        
        report += f"\n{'='*60}\n"
        
        return report
