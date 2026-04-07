"""
HOURLY PREDICTION EXAMPLES - SIMPLIFIED
Simple hourly forecasts for proactive scaling decisions
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.integrated_predictor import IntegratedPredictor


def example_1_daily_forecast():
    """
    Example 1: See today's hourly predictions
    """
    predictor = IntegratedPredictor()
    
    print("\n" + "="*70)
    print("EXAMPLE 1: TODAY'S HOURLY CAPACITY FORECAST")
    print("="*70)
    
    daily = predictor.predict_day_profile(datetime.now())
    
    # Calculate peak threshold
    avg_servers = sum(h['servers'] for h in daily) / len(daily)
    peak_threshold = avg_servers * 1.3
    
    print(f"\n{'Hour':<6} {'RPS':<10} {'Servers':<10} {'Status':<20}")
    print("-"*70)
    
    for h in daily:
        is_peak = h['servers'] >= peak_threshold
        status = "🔴 SPIKE" if is_peak else "✅ NORMAL"
        print(f"{h['hour']:02d}:00  {h['rps']:>8.0f}  {h['servers']:>8}  {status:<20}")
    
    peak = max(daily, key=lambda x: x['servers'])
    valley = min(daily, key=lambda x: x['servers'])
    
    print("\n" + "-"*70)
    print(f"📈 Peak:    {peak['servers']} servers at {peak['hour']:02d}:00 ({peak['rps']:.0f} RPS)")
    print(f"📉 Valley:  {valley['servers']} servers at {valley['hour']:02d}:00 ({valley['rps']:.0f} RPS)")
    print(f"📊 Average: {avg_servers:.0f} servers")


def example_2_next_hour():
    """
    Example 2: Check recommendations for the NEXT hour
    """
    predictor = IntegratedPredictor()
    
    print("\n" + "="*70)
    print("EXAMPLE 2: NEXT HOUR PREDICTION & RECOMMENDATION")
    print("="*70)
    
    now = datetime.now()
    current_hour = now.hour
    next_hour = (current_hour + 1) % 24
    
    daily = predictor.predict_day_profile(now)
    current = daily[current_hour]
    next_pred = daily[next_hour]
    
    print(f"\nCurrent time: {current_hour:02d}:00")
    print(f"  Predicted RPS:     {current['rps']:>8.0f}")
    print(f"  Servers needed:    {current['servers']:>8}")
    
    print(f"\nNext hour ({next_hour:02d}:00):")
    print(f"  Predicted RPS:     {next_pred['rps']:>8.0f}")
    print(f"  Servers needed:    {next_pred['servers']:>8}")
    
    # Recommendation
    today_avg = sum(h['servers'] for h in daily) / len(daily)
    
    if next_pred['servers'] > current['servers'] + 2:
        change = next_pred['servers'] - current['servers']
        print(f"\n✅ RECOMMENDATION: ADD {change} SERVERS")
        print(f"   Reason: Spike coming at {next_hour:02d}:00")
        print(f"   Action: Pre-scale NOW to {next_pred['servers']} servers")
    
    elif next_pred['servers'] < current['servers'] - 2:
        change = current['servers'] - next_pred['servers']
        print(f"\n✅ RECOMMENDATION: PREPARE TO REMOVE {change} SERVERS")
        print(f"   Reason: Demand decreasing at {next_hour:02d}:00")
        print(f"   Action: Plan graceful drain to {next_pred['servers']} servers")
    
    else:
        print(f"\n✅ RECOMMENDATION: MAINTAIN CURRENT SERVERS")
        print(f"   Reason: Next hour is stable")
        print(f"   Action: Keep current server count")


def example_3_specific_hours():
    """
    Example 3: Check specific busy hours (lunch, evening, etc)
    """
    predictor = IntegratedPredictor()
    
    print("\n" + "="*70)
    print("EXAMPLE 3: PEAK HOURS ANALYSIS")
    print("="*70)
    
    daily = predictor.predict_day_profile(datetime.now())
    
    # Sort by servers needed
    sorted_by_load = sorted(daily, key=lambda x: x['servers'], reverse=True)
    
    print("\nTop 5 Busiest Hours:")
    print(f"{'Hour':<6} {'RPS':<10} {'Servers':<10} {'Utilization %':<15}")
    print("-"*70)
    
    max_servers = max(daily, key=lambda x: x['servers'])['servers']
    
    for i, h in enumerate(sorted_by_load[:5], 1):
        utilization = (h['servers'] / max_servers) * 100
        print(f"{h['hour']:02d}:00  {h['rps']:>8.0f}  {h['servers']:>8}  {utilization:>13.0f}%")
    
    print("\nLightest 5 Hours:")
    print(f"{'Hour':<6} {'RPS':<10} {'Servers':<10} {'Utilization %':<15}")
    print("-"*70)
    
    for i, h in enumerate(sorted_by_load[-5:], 1):
        utilization = (h['servers'] / max_servers) * 100
        print(f"{h['hour']:02d}:00  {h['rps']:>8.0f}  {h['servers']:>8}  {utilization:>13.0f}%")


def example_4_compare_days():
    """
    Example 4: Compare predicted loads across multiple days
    """
    predictor = IntegratedPredictor()
    
    print("\n" + "="*70)
    print("EXAMPLE 4: NEXT 7 DAYS COMPARISON")
    print("="*70)
    
    print(f"\n{'Day':<12} {'Peak Servers':<15} {'Avg Servers':<15} {'Peak Hour':<12}")
    print("-"*70)
    
    for day_offset in range(7):
        target_date = datetime.now() + timedelta(days=day_offset)
        day_name = target_date.strftime('%A')
        
        daily = predictor.predict_day_profile(target_date)
        peak = max(daily, key=lambda x: x['servers'])
        avg = sum(h['servers'] for h in daily) / len(daily)
        
        print(f"{day_name:<12} {peak['servers']:<15} {avg:<15.0f} {peak['hour']:02d}:00")


def example_5_automated_decision():
    """
    Example 5: Automated hourly decision (simulate every hour)
    """
    predictor = IntegratedPredictor()
    
    print("\n" + "="*70)
    print("EXAMPLE 5: AUTOMATED HOURLY DECISIONS (24-HOUR SIMULATION)")
    print("="*70)
    
    daily = predictor.predict_day_profile(datetime.now())
    
    current_servers = 5  # Start with minimum
    decisions = []
    
    print(f"\n{'Hour':<6} {'Predicted':<10} {'Current':<10} {'Decision':<35}")
    print("-"*70)
    
    for i, hour_data in enumerate(daily):
        needed = hour_data['servers']
        
        if needed > current_servers + 2:
            decision = f"ADD {needed - current_servers} SERVERS"
            current_servers = needed
        elif needed < current_servers - 2:
            decision = f"REMOVE {current_servers - needed} SERVERS"
            current_servers = needed
        else:
            decision = "MAINTAIN"
        
        decisions.append({
            'hour': hour_data['hour'],
            'decision': decision,
            'servers': current_servers
        })
        
        print(f"{hour_data['hour']:02d}:00  {needed:<8}  {current_servers:<8}  {decision:<35}")
    
    # Summary
    add_count = sum(1 for d in decisions if 'ADD' in d['decision'])
    remove_count = sum(1 for d in decisions if 'REMOVE' in d['decision'])
    maintain_count = sum(1 for d in decisions if 'MAINTAIN' in d['decision'])
    
    print("\n" + "-"*70)
    print(f"Total decisions: ADD {add_count}, REMOVE {remove_count}, MAINTAIN {maintain_count}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("HOURLY PREDICTION EXAMPLES - SIMPLIFIED".center(70))
    print("="*70)
    
    # Run all examples
    example_1_daily_forecast()
    example_2_next_hour()
    example_3_specific_hours()
    example_4_compare_days()
    example_5_automated_decision()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETE!".center(70))
    print("="*70 + "\n")
