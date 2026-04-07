"""
Spike-aware queue rearrangement policy for dynamic task prioritization.

During normal periods: FIFO
During spikes: Prioritize by deadline, business priority, and resource efficiency
Trigger: Can use prediction signals or threshold-based detection
"""

from typing import List, Tuple, Callable
import heapq
from datetime import datetime
from src.core.event import Event


class SpikeAwarePriorityPolicy:
    """
    Rearranges task queue based on priority, with special handling during spikes.
    """
    
    def __init__(self, 
                 spike_threshold: float = 0.7,
                 deadline_weight: float = 0.4,
                 priority_weight: float = 0.3,
                 efficiency_weight: float = 0.3):
        """
        Initialize policy.
        
        Args:
            spike_threshold: Queue depth ratio to consider spike (0-1)
            deadline_weight: Weight for deadline urgency (0-1)
            priority_weight: Weight for business priority (0-1)
            efficiency_weight: Weight for resource efficiency (0-1)
        """
        self.spike_threshold = spike_threshold
        self.deadline_weight = deadline_weight
        self.priority_weight = priority_weight
        self.efficiency_weight = efficiency_weight
        
        # Ensure weights sum to 1
        total = deadline_weight + priority_weight + efficiency_weight
        self.deadline_weight /= total
        self.priority_weight /= total
        self.efficiency_weight /= total
        
        self.is_in_spike = False
        self.spike_start_time = None
        self.rearrangements_count = 0
        
        # Statistics tracking
        self.stats = {
            'rearrangements': 0,
            'tasks_prioritized': 0,
            'spike_events': 0,
            'avg_queue_depth_spike': 0,
            'max_queue_depth_spike': 0
        }
    
    def detect_spike(self, queue_depth: int, 
                    max_servers: int,
                    spike_predictor: Callable = None) -> bool:
        """
        Detect if system is in spike state.
        
        Can use:
        1. Threshold-based: queue_depth / total_servers > threshold
        2. Prediction-based: if provided spike_predictor
        
        Returns: True if spike detected
        """
        # Method 1: Threshold-based
        queue_ratio = queue_depth / max(max_servers, 1)
        threshold_spike = queue_ratio > self.spike_threshold
        
        # Method 2: Prediction-based (if available)
        prediction_spike = False
        if spike_predictor is not None:
            try:
                prediction_spike = spike_predictor()
            except:
                pass
        
        # Combined decision (either method triggers spike)
        in_spike = threshold_spike or prediction_spike
        
        # Track spike transitions
        if in_spike and not self.is_in_spike:
            self.is_in_spike = True
            self.spike_start_time = datetime.now()
            self.stats['spike_events'] += 1
        elif not in_spike and self.is_in_spike:
            self.is_in_spike = False
        
        return in_spike
    
    def calculate_priority_score(self, event: Event,
                                current_time: float,
                                spike_mode: bool = True) -> float:
        """
        Calculate comprehensive priority score for event.
        
        Higher score = higher priority.
        
        Factors:
        - Deadline urgency (time until deadline)
        - Business priority (business flag)
        - Resource efficiency (lower exec time = higher priority)
        """
        # 1. Deadline urgency (0-1)
        time_remaining = event.deadline - (current_time - event.arrival_time)
        urgency = max(0, min(1, 1 - (time_remaining / (event.deadline + 0.1))))
        
        # 2. Business priority (0-1)
        biz_priority = float(event.business) if event.business > 0 else 0.5
        
        # 3. Resource efficiency (prefer quick tasks)
        # Normalize by typical exec time (assume 5-10 minutes typical)
        efficiency = max(0, 1 - (event.exec_time / 15.0))
        
        if spike_mode:
            # During spikes: emphasize deadline and business priority
            score = (
                self.deadline_weight * urgency * 2 +  # Double deadline weight in spike
                self.priority_weight * biz_priority * 1.5 +  # Boost business priority
                self.efficiency_weight * efficiency * 0.5    # Lower emphasis on efficiency
            )
        else:
            # Normal mode: balanced
            score = (
                self.deadline_weight * urgency +
                self.priority_weight * biz_priority +
                self.efficiency_weight * efficiency
            )
        
        return score
    
    def rearrange_queue(self, queue: List[Event],
                       current_time: float,
                       max_servers: int = 10,
                       spike_predictor: Callable = None) -> List[Event]:
        """
        Rearrange queue based on priority and spike status.
        
        Args:
            queue: Current task queue
            current_time: Simulation time
            max_servers: Total server count
            spike_predictor: Optional callable that returns spike probability
        
        Returns: Rearranged queue
        """
        if not queue:
            return queue
        
        # Detect spike
        spike = self.detect_spike(len(queue), max_servers, spike_predictor)
        self.stats['avg_queue_depth_spike'] = (
            self.stats['avg_queue_depth_spike'] * 0.9 + len(queue) * 0.1
        )
        self.stats['max_queue_depth_spike'] = max(
            self.stats['max_queue_depth_spike'], len(queue)
        )
        
        # In spike mode: sort by priority score
        if spike:
            # Calculate scores
            scored_queue = [
                (event, self.calculate_priority_score(event, current_time, spike_mode=True))
                for event in queue
            ]
            
            # Sort by score (descending) - highest priority first
            scored_queue.sort(key=lambda x: x[1], reverse=True)
            
            rearranged = [event for event, score in scored_queue]
            self.stats['rearrangements'] += 1
            self.stats['tasks_prioritized'] += len(queue)
            
            return rearranged
        else:
            # Normal mode: keep FIFO or light sorting
            return queue  # Keep original order
    
    def get_next_task(self, queue: List[Event],
                     current_time: float,
                     max_servers: int = 10,
                     spike_predictor: Callable = None) -> Tuple[Event, bool]:
        """
        Get next task to execute, with optional rearrangement.
        
        Returns: (event, was_rearranged)
        """
        if not queue:
            return None, False
        
        # Check for spike
        spike = self.detect_spike(len(queue), max_servers, spike_predictor)
        
        if spike and len(queue) > 1:
            # Rearrange before getting top task
            queue = self.rearrange_queue(queue, current_time, max_servers, spike_predictor)
            return queue[0], True
        else:
            # Return first task (FIFO)
            return queue[0], False
    
    def adaptive_rearrangement(self, queue: List[Event],
                              current_time: float,
                              max_servers: int,
                              queue_history: List[int],
                              spike_predictor: Callable = None) -> List[Event]:
        """
        Adaptively rearrange based on queue history and trends.
        Detects rising trends and pre-emptively rearranges.
        """
        if len(queue_history) < 3:
            return self.rearrange_queue(queue, current_time, max_servers, spike_predictor)
        
        # Calculate trend (is queue growing?)
        recent_avg = sum(queue_history[-5:]) / 5 if len(queue_history) >= 5 else 0
        previous_avg = sum(queue_history[-10:-5]) / 5 if len(queue_history) >= 10 else recent_avg
        
        trend = recent_avg - previous_avg
        
        # If trends show growing queue, be more aggressive with rearrangement
        if trend > 0:
            # Increasing queue - use spike mode even if threshold not met
            spike_predictor_enhanced = lambda: True
        else:
            spike_predictor_enhanced = spike_predictor
        
        return self.rearrange_queue(queue, current_time, max_servers, spike_predictor_enhanced)
    
    def batch_rearrange(self, queue: List[Event],
                       batch_size: int = 5) -> List[Event]:
        """
        Rearrange only top N items in queue (batch rearrangement).
        Reduces computation for very large queues.
        """
        if len(queue) <= batch_size:
            return queue
        
        top_batch = queue[:batch_size]
        rest = queue[batch_size:]
        
        # Sort top batch by estimated size (smaller tasks first to clear queue)
        top_batch.sort(key=lambda e: e.exec_time)
        
        return top_batch + rest
    
    def get_spike_status(self) -> dict:
        """Get current spike status."""
        return {
            'is_in_spike': self.is_in_spike,
            'spike_start_time': self.spike_start_time.isoformat() if self.spike_start_time else None,
            'spike_duration': (datetime.now() - self.spike_start_time).total_seconds() 
                            if self.spike_start_time else 0
        }
    
    def get_statistics(self) -> dict:
        """Get rearrangement statistics."""
        return {
            **self.stats,
            **self.get_spike_status()
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'rearrangements': 0,
            'tasks_prioritized': 0,
            'spike_events': 0,
            'avg_queue_depth_spike': 0,
            'max_queue_depth_spike': 0
        }


class HybridPriorityPolicy:
    """
    Combines spike detection with weighted priority for sophisticated queue management.
    Uses ensemble approach: prediction + threshold + trend analysis.
    """
    
    def __init__(self, 
                 spike_policy: SpikeAwarePriorityPolicy = None,
                 prediction_weight: float = 0.5,
                 threshold_weight: float = 0.3,
                 trend_weight: float = 0.2):
        """Initialize hybrid policy with ensemble weights."""
        self.policy = spike_policy or SpikeAwarePriorityPolicy()
        self.prediction_weight = prediction_weight
        self.threshold_weight = threshold_weight
        self.trend_weight = trend_weight
        
        self.queue_history = []
    
    def ensemble_spike_detection(self, 
                                queue_depth: int,
                                max_servers: int,
                                spike_predictor: Callable = None,
                                trend_data: List[int] = None) -> Tuple[bool, float]:
        """
        Ensemble spike detection combining multiple signals.
        
        Returns: (is_spike, confidence)
        """
        signals = []
        
        # Signal 1: Prediction-based
        pred_signal = 0.0
        if spike_predictor:
            try:
                pred_signal = float(spike_predictor())
            except:
                pred_signal = 0.0
        signals.append(('prediction', pred_signal))
        
        # Signal 2: Threshold-based
        threshold_signal = min(1.0, queue_depth / max(max_servers, 1))
        signals.append(('threshold', threshold_signal))
        
        # Signal 3: Trend-based
        trend_signal = 0.0
        if trend_data and len(trend_data) >= 2:
            recent = trend_data[-5:] if len(trend_data) >= 5 else trend_data
            if len(recent) > 1:
                # Calculate rate of change
                slope = (recent[-1] - recent[0]) / len(recent)
                trend_signal = min(1.0, slope / max_servers)
        signals.append(('trend', trend_signal))
        
        # Weighted ensemble
        confidence = (
            self.prediction_weight * signals[0][1] +
            self.threshold_weight * signals[1][1] +
            self.trend_weight * signals[2][1]
        )
        
        is_spike = confidence > 0.5
        
        return is_spike, confidence
