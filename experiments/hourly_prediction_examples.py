"""
HOURLY PREDICTION USAGE GUIDE
How to use hourly forecasts for proactive scaling
"""

import os
import sys
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.integrated_predictor import IntegratedPredictor
from src.orchestration.multi_horizon_orchestrator import MultiHorizonOrchestrator

# ============================================================
# OPTION 1: SIMPLE HOURLY FORECAST (Easiest)
# ============================================================

def simple_hourly_forecast():
    """
    Predict the next 24 hours and see what server count you need each hour
    
    Best for: Morning planning, understanding daily patterns
    """
    predictor = IntegratedPredictor()
    
    # Get 24-hour forecast
    daily_profile = predictor.predict_day_profile(datetime.now())
    
    # Calculate average servers to determine peaks
    avg_servers = sum(h['servers'] for h in daily_profile) / len(daily_profile)
    peak_threshold = avg_servers * 1.3  # 30% above average = peak
    
    print("\n📊 TODAY'S HOURLY CAPACITY FORECAST")
    print("=" * 70)
    print(f"{'Hour':<6} {'RPS':<8} {'Servers':<10} {'Peak?':<8} Status")
    print("-" * 70)
    
    for hour_data in daily_profile:
        is_peak = hour_data['servers'] >= peak_threshold
        status = "🔴 SPIKE" if is_peak else "✅ Normal"
        print(f"{hour_data['hour']:02d}:00  {hour_data['rps']:>6.0f}  {hour_data['servers']:>8}  "
              f"{str(is_peak):<6}  {status}")
    
    # Summary
    peak_hour = max(daily_profile, key=lambda x: x['servers'])
    avg = sum(h['servers'] for h in daily_profile) / len(daily_profile)
    min_hour = min(daily_profile, key=lambda x: x['servers'])
    
    print("\n" + "=" * 70)
    print(f"📈 Peak: {peak_hour['servers']} servers at {peak_hour['hour']:02d}:00")
    print(f"📊 Average: {avg:.0f} servers")
    print(f"📉 Valley: {min_hour['servers']} servers at {min_hour['hour']:02d}:00")
    print("=" * 70)


# ============================================================
# OPTION 2: MULTI-HORIZON ORCHESTRATOR (Recommended)
# ============================================================

def multi_horizon_strategy(current_servers: int, current_rps: float, queue_depth: int):
    """
    3-layer strategy:
    1. Daily plan at 6 AM
    2. Hourly checkpoints at :00
    3. Real-time 10-min decisions every 5 min
    
    Best for: Production deployment, balancing planning + real-time
    """
    orchestrator = MultiHorizonOrchestrator(lookahead_minutes=10)
    
    # ─────────────────────────────────────────────────────────
    # LAYER 1: MORNING DAILY PLAN (Call at 06:00 AM)
    # ─────────────────────────────────────────────────────────
    
    daily_plan = orchestrator.generate_daily_plan()
    
    print(orchestrator.format_daily_plan_for_ops())
    # Output:
    # ============================================================
    # DAILY CAPACITY PLAN - 2026-04-05
    # ============================================================
    # Peak: 15 servers at 13:00
    # Average: 8 servers
    # Valley: 2 servers
    #
    # SPIKE WINDOWS:
    #   Window 1: 12:00-15:00, avg 13 servers
    #   Window 2: 19:00-21:00, avg 11 servers
    #
    # RECOMMENDATIONS:
    #   11:30: Scale to 13 servers 30 min before lunch spike
    #   18:30: Scale to 11 servers 30 min before evening spike
    # ============================================================
    
    # ─────────────────────────────────────────────────────────
    # LAYER 2: HOURLY CHECKPOINT (Call at :00 PM)
    # ─────────────────────────────────────────────────────────
    
    if datetime.now().minute == 0:
        hourly_check = orchestrator.hourly_checkpoint(current_servers)
        
        print(f"\n⏰ HOURLY CHECKPOINT - {hourly_check['current_hour']}")
        print(f"   Current: {hourly_check['current_servers']} servers")
        print(f"   Next hour ({hourly_check['next_hour']}): {hourly_check['predicted_servers']} servers")
        print(f"   Action: {hourly_check['action']}")
        print(f"   Message: {hourly_check['message']}")
    
    # ─────────────────────────────────────────────────────────
    # LAYER 3: REAL-TIME DECISION (Call every 5 min)
    # ─────────────────────────────────────────────────────────
    
    action, details = orchestrator.get_realtime_decision(
        current_rps=current_rps,
        current_servers=current_servers,
        queue_depth=queue_depth,
        max_servers=20
    )
    
    print(f"\n⚡ REAL-TIME DECISION (10-min lookahead)")
    print(f"   Action: {action}")
    print(f"   Reason: {details['reasoning']}")
    print(f"   RPS trend: {details['trends']['rps_change_pct']:+.0f}%")
    print(f"   Server gap: {details['trends']['server_gap']:+d}")
    print(f"   Confidence: {details['confidence']:.0%}")


# ============================================================
# OPTION 3: PER-HOUR DECISION LOOP (For automation)
# ============================================================

def automated_hourly_loop():
    """
    Automation loop that runs every hour at :00
    Makes hourly pre-scaling decisions
    
    Best for: DevOps automation, scheduled tasks
    """
    orchestrator = MultiHorizonOrchestrator()
    
    # Call this in a cron job at every :00 mark
    now = datetime.now()
    
    if now.minute == 0:  # Only at top of hour
        # Get tomorrow's plan
        from datetime import timedelta
        tomorrow = datetime.now() + timedelta(days=1)
        
        daily_plan = orchestrator.generate_daily_plan(tomorrow)
        
        # Check if spike coming in the next 1-2 hours
        hourly_check = orchestrator.hourly_checkpoint(current_servers=8)  # Get from your system
        
        if hourly_check['action'] in ['PRE_WARM', 'STANDBY_REMOVE']:
            print(f"✅ Automated Action: {hourly_check['action']}")
            print(f"   Message: {hourly_check['message']}")
            # TODO: Execute the action in your load balancer
        
        return hourly_check
    
    return None


# ============================================================
# OPTION 4: PREDICTIONS AT SPECIFIC TIMES
# ============================================================

def predict_at_specific_times():
    """
    Get predictions for specific hours of the day
    
    Best for: Manual checks, understanding specific time periods
    """
    predictor = IntegratedPredictor()
    
    # Get all 24 hours
    daily_profile = predictor.predict_day_profile(datetime.now())
    
    # Find specific times
    lunch_hour = [h for h in daily_profile if h['hour'] in [12, 13, 14]]
    evening_rush = [h for h in daily_profile if h['hour'] in [17, 18, 19]]
    night = [h for h in daily_profile if h['hour'] in [22, 23, 0, 1]]
    
    print("\n🍽️  LUNCH PERIOD (12:00-14:00)")
    for h in lunch_hour:
        print(f"  {h['hour']:02d}:00 - {h['rps']} RPS, {h['servers']} servers")
    
    print("\n🚗 EVENING RUSH (17:00-19:00)")
    for h in evening_rush:
        print(f"  {h['hour']:02d}:00 - {h['rps']} RPS, {h['servers']} servers")
    
    print("\n🌙 NIGHT (22:00-01:00)")
    for h in night:
        print(f"  {h['hour']:02d}:00 - {h['rps']} RPS, {h['servers']} servers")


# ============================================================
# OPTION 5: COMPARATIVE ANALYSIS
# ============================================================

def compare_days():
    """
    Compare predictions for different days to understand patterns
    
    Best for: Understanding weekly patterns, seasonality
    """
    predictor = IntegratedPredictor()
    from datetime import timedelta
    
    print("\n📊 COMPARING PREDICTED CAPACITY ACROSS DAYS")
    print("=" * 70)
    print(f"{'Day':<15} {'Peak Servers':<15} {'Avg Servers':<15} {'Pattern'}")
    print("-" * 70)
    
    # Check pattern for 7 days
    for i in range(7):
        target_date = datetime.now() + timedelta(days=i)
        day_name = target_date.strftime('%A')
        
        daily = predictor.predict_day_profile(target_date)
        peak = max(daily, key=lambda x: x['servers'])['servers']
        avg = sum(h['servers'] for h in daily) / len(daily)
        
        # Pattern analysis
        if day_name in ['Saturday', 'Sunday']:
            pattern = "🏖️  Weekend"
        else:
            pattern = "💼 Weekday"
        
        print(f"{day_name:<15} {peak:<15.0f} {avg:<15.0f} {pattern}")
    
    print("=" * 70)


# ============================================================
# OPTION 6: INTEGRATED WITH YOUR LOAD BALANCER
# ============================================================

def integrate_with_load_balancer():
    """
    Full integration: Decision thread that runs continuously
    
    Best for: Production deployment into your LB
    """
    import time
    from threading import Thread
    
    orchestrator = MultiHorizonOrchestrator(lookahead_minutes=10)
    
    def decision_loop():
        """Runs in background thread, makes decisions every 5 minutes"""
        while True:
            now = datetime.now()
            
            # Every 5 minutes
            if now.second < 30:
                # Get current system state (from your LB)
                current_servers = 8  # TODO: Get from your system
                current_rps = 900    # TODO: Get from your system
                queue_depth = 12     # TODO: Get from your system
                
                # Make decision
                action, details = orchestrator.get_realtime_decision(
                    current_rps=current_rps,
                    current_servers=current_servers,
                    queue_depth=queue_depth
                )
                
                # Execute action
                if action == 'ADD_SERVERS_PROACTIVE':
                    num_servers = details['trends']['server_gap']
                    print(f"✅ ADD {num_servers} SERVERS (proactive)")
                    # TODO: spawn_servers(num_servers)
                
                elif action == 'REMOVE_SERVERS':
                    num_servers = abs(details['trends']['server_gap'])
                    print(f"⬇️  REMOVE {num_servers} SERVERS")
                    # TODO: remove_servers(num_servers)
                
                elif action == 'REARRANGE_QUEUE':
                    print(f"🔄 REARRANGE QUEUE")
                    # TODO: rearrange_queue()
                
                else:
                    print(f"⏸️  MAINTAIN ({action})")
                
                # Sleep until next check window
                time.sleep(300)  # 5 minutes
    
    # Start background thread
    decision_thread = Thread(target=decision_loop, daemon=True)
    decision_thread.start()
    print("✅ Decision thread started (background)")


# ============================================================
# RUNNING THE EXAMPLES
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("HOURLY PREDICTION EXAMPLES")
    print("="*70)
    
    # Example 1: Simple hourly forecast
    print("\n\n1️⃣  SIMPLE HOURLY FORECAST")
    print("-" * 70)
    simple_hourly_forecast()
    
    # Example 2: Multi-horizon (current system state)
    print("\n\n2️⃣  MULTI-HORIZON ORCHESTRATOR")
    print("-" * 70)
    multi_horizon_strategy(current_servers=8, current_rps=1200, queue_depth=15)
    
    # Example 3: Specific times
    print("\n\n3️⃣  PREDICTIONS AT SPECIFIC TIMES")
    print("-" * 70)
    predict_at_specific_times()
    
    # Example 4: Comparative analysis
    print("\n\n4️⃣  COMPARING DAYS")
    print("-" * 70)
    compare_days()
    
    print("\n" + "="*70)
    print("✅ All examples complete!")
    print("="*70)
