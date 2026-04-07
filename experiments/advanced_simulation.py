"""
Enhanced simulation environment that generates 1-month realistic load patterns
with holidays, time-of-day variations, and demand spikes.

Collects comprehensive metrics for training predictive models.
"""

import simpy
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import csv
from src.core.event import Event
from src.core.server import Server
from src.utils.advanced_load_predictor import AdvancedLoadPredictor


class RealisticDemandSimulation:
    """
    Generates realistic demand with:
    - Holiday effects (reduced load)
    - Time-of-day patterns
    - Demand spikes
    - Weekly patterns
    """
    
    # US Holidays for the month (example: April)
    HOLIDAYS = [
        datetime(2024, 4, 1),  # Example: Spring event
    ]
    
    def __init__(self, 
                 days_to_simulate: int = 30,
                 base_arrival_rate: float = 5.0,
                 spike_multiplier: float = 3.0,
                 spike_probability: float = 0.15):
        
        self.days = days_to_simulate
        self.base_rate = base_arrival_rate
        self.spike_multiplier = spike_multiplier
        self.spike_probability_per_hour = spike_probability
        
        self.load_predictor = AdvancedLoadPredictor()
        self.metrics_log = []  # Collect all metrics
        self.current_spike_events = 0  # Track spike events
        
    def add_holidays(self, dates: List[datetime]):
        """Add custom holiday dates."""
        self.HOLIDAYS.extend(dates)
    
    def is_holiday(self, timestamp: datetime) -> bool:
        """Check if given timestamp is a holiday."""
        return any(timestamp.date() == h.date() for h in self.HOLIDAYS)
    
    def get_time_of_day_multiplier(self, hour: int) -> float:
        """Get demand multiplier based on time of day."""
        # Business hours: 9-17 = peak
        # Morning ramp: 6-9 = medium
        # Evening: 17-20 = medium-high
        # Night: 20-6 = low
        
        if 6 <= hour < 9:
            return 0.6  # Morning ramp-up
        elif 9 <= hour < 17:
            return 1.3  # Business hours peak
        elif 17 <= hour < 20:
            return 1.0  # Evening
        elif 20 <= hour < 24 or 0 <= hour < 6:
            return 0.4  # Night (low)
        else:
            return 1.0
    
    def get_day_of_week_multiplier(self, day_of_week: int) -> float:
        """Get demand multiplier based on day of week."""
        # Monday-Thursday: normal
        # Friday: slight decline (weekend start)
        # Saturday-Sunday: low
        
        if day_of_week < 4:  # Mon-Thu
            return 1.0
        elif day_of_week == 4:  # Friday
            return 0.85
        else:  # Sat-Sun
            return 0.4
    
    def should_generate_spike(self) -> bool:
        """Randomly decide if a spike should occur this hour."""
        return random.random() < self.spike_probability_per_hour
    
    def get_arrival_rate_for_time(self, timestamp: datetime) -> float:
        """
        Calculate dynamic arrival rate based on:
        - Time of day
        - Day of week
        - Holiday status
        - Random spikes
        """
        base = self.base_rate
        
        # Apply holiday effect (50% reduction)
        if self.is_holiday(timestamp):
            base *= 0.5
        
        # Apply day-of-week pattern
        day_multiplier = self.get_day_of_week_multiplier(timestamp.weekday())
        base *= day_multiplier
        
        # Apply time-of-day pattern
        time_multiplier = self.get_time_of_day_multiplier(timestamp.hour)
        base *= time_multiplier
        
        # Random spikes
        if self.should_generate_spike():
            base *= self.spike_multiplier
            self.current_spike_events += 1
        
        return base
    
    def event_producer(self, env, queue, start_time: datetime):
        """Generate events with realistic demand patterns."""
        event_id = 0
        timestamp = start_time
        
        # Generate events for entire simulation period
        while True:
            arrival_rate = self.get_arrival_rate_for_time(timestamp)
            
            # Inter-arrival time from exponential distribution
            inter_arrival_time = random.expovariate(arrival_rate)
            yield env.timeout(inter_arrival_time)
            
            # Calculate actual arrival timestamp
            sim_time_delta = timedelta(minutes=env.now / 60)  # Convert sim time to minutes
            timestamp = start_time + sim_time_delta
            
            # Skip if we've simulated enough days
            if (timestamp - start_time).days >= self.days:
                break
            
            # Create event with realistic parameters
            event = Event(
                event_id=event_id,
                arrival_time=env.now,
                deadline=random.uniform(30, 120),  # 30-120 minutes
                exec_time=random.uniform(2, 15),   # 2-15 minutes
                resource=random.uniform(0.2, 1.0),
                business=random.randint(0, 1)      # Priority: 0 or 1
            )
            
            queue.append(event)
            event_id += 1
    
    def routing_logic(self, env, queue, servers, logs):
        """Simple routing engine for simulation."""
        while True:
            yield env.timeout(1)  # Check every minute of sim time
            
            # Route events in queue to servers
            while queue and any(len(s.jobs) == 0 for s in servers):
                server = next((s for s in servers if len(s.jobs) == 0), None)
                if server is None:
                    break
                
                event = queue.pop(0)
                logs.append({
                    'event_id': event.id,
                    'server_id': server.id,
                    'assigned_time': env.now,
                    'deadline': event.deadline_remaining,
                    'exec_time': event.estimated_execution_time
                })
    
    def metrics_collector(self, env, queue, servers, start_time: datetime):
        """Collect metrics every 5 minutes of simulation."""
        while True:
            yield env.timeout(5)  # Collect every 5 minutes
            
            # Calculate actual timestamp
            sim_time_delta = timedelta(minutes=env.now / 60)
            timestamp = start_time + sim_time_delta
            
            if (timestamp - start_time).days >= self.days:
                break
            
            # Current metrics
            servers_active = sum(1 for s in servers if len(s.jobs) > 0)
            queue_depth = len(queue)
            
            # Calculate average response time from jobs
            response_times = []
            for server in servers:
                for job in server.jobs:
                    if hasattr(job, 'start_time') and hasattr(job, 'finish_time'):
                        if job.finish_time > 0:
                            response_times.append(job.finish_time - job.start_time)
            
            avg_response_time = np.mean(response_times) if response_times else 0
            
            # Resource utilization (ratio of active servers)
            resource_utilization = servers_active / len(servers) if servers else 0
            
            # Store metric
            metric = {
                'timestamp': timestamp.isoformat(),
                'datetime_obj': timestamp,
                'queue_depth': queue_depth,
                'servers_active': servers_active,
                'total_servers': len(servers),
                'response_time_ms': avg_response_time * 1000,
                'resource_utilization': resource_utilization,
                'is_holiday': self.is_holiday(timestamp),
                'hour': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'sim_time': env.now
            }
            
            self.metrics_log.append(metric)
            self.load_predictor.add_measurement(queue_depth, timestamp)
    
    def run_simulation(self, num_servers: int = 10) -> Dict:
        """
        Run full month simulation and return comprehensive metrics.
        
        Returns: {
            metrics: List[Dict],
            statistics: Dict,
            predictions: Dict,
            spike_count: int
        }
        """
        env = simpy.Environment()
        queue = []
        servers = [Server(i) for i in range(num_servers)]
        logs = []
        
        start_time = datetime(2024, 4, 1, 0, 0, 0)  # Start of month
        
        # Register processes
        env.process(self.event_producer(env, queue, start_time))
        env.process(self.routing_logic(env, queue, servers, logs))
        env.process(self.metrics_collector(env, queue, servers, start_time))
        
        # Run for 30 days = 30 * 24 * 60 = 43200 minutes
        sim_end_time = self.days * 24 * 60
        env.run(until=sim_end_time)
        
        return {
            'metrics': self.metrics_log,
            'statistics': self.load_predictor.get_statistics(),
            'spike_count': self.current_spike_events,
            'logs': logs
        }
    
    def export_metrics_to_csv(self, file_path: str):
        """Export collected metrics to CSV for training."""
        if not self.metrics_log:
            print("No metrics to export!")
            return
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.metrics_log[0].keys() 
                                    if self.metrics_log else [])
            writer.writeheader()
            for metric in self.metrics_log:
                # Remove datetime_obj before writing (not JSON serializable)
                metric_copy = {k: v for k, v in metric.items() if k != 'datetime_obj'}
                writer.writerow(metric_copy)
        
        print(f"✓ Exported {len(self.metrics_log)} metrics to {file_path}")
    
    def get_summary(self) -> Dict:
        """Get simulation summary."""
        if not self.metrics_log:
            return {}
        
        max_queue = max(m['queue_depth'] for m in self.metrics_log)
        avg_queue = np.mean([m['queue_depth'] for m in self.metrics_log])
        max_servers_needed = max(m['servers_active'] for m in self.metrics_log)
        
        return {
            'simulation_days': self.days,
            'total_metrics_collected': len(self.metrics_log),
            'max_queue_depth': max_queue,
            'avg_queue_depth': avg_queue,
            'max_servers_needed': max_servers_needed,
            'spike_events': self.current_spike_events,
            'holidays': len(self.HOLIDAYS)
        }
