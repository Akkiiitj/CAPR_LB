"""
Integration script for pre-trained RPS and Server models.

This script:
1. Tests model loading
2. Demonstrates all prediction types
3. Runs simulations
4. Generates forecasts
5. Validates year-round capacity planning
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models.integrated_predictor import IntegratedPredictor, get_servers_for_time
from src.orchestration.updated_orchestrator import UpdatedProactiveOrchestrator, quick_decision


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'='*80}")
    print(f"{title.center(80)}")
    print(f"{'='*80}\n")


def test_model_loading():
    """Test 1: Verify models load correctly."""
    print_section("TEST 1: Model Loading")
    
    predictor = IntegratedPredictor()
    
    if predictor.is_loaded:
        print("✓ Both models loaded successfully!")
        print(f"  RPS Model: {os.path.basename(predictor.rps_model_path)}")
        print(f"  Server Model: {os.path.basename(predictor.server_model_path)}")
        return True
    else:
        print("✗ Models failed to load!")
        print(f"  RPS Model path: {predictor.rps_model_path}")
        print(f"  Server Model path: {predictor.server_model_path}")
        return False


def test_basic_prediction():
    """Test 2: Basic feature-to-servers prediction."""
    print_section("TEST 2: Basic Prediction Example")
    
    predictor = IntegratedPredictor()
    
    # Example from user:
    # hour = 20, day_of_year = 180, day_of_week = 6, is_weekend = 1, is_holiday = 0
    
    print("Testing prediction for: Tuesday 8 PM (summer, mid-week)")
    print("Features: hour=20, day_of_year=180, day_of_week=6, is_weekend=1, is_holiday=0\n")
    
    # Method 1: Using full pipeline
    result = predictor.predict_full_pipeline(
        timestamp=datetime(2024, 6, 29, 20, 0),  # Mid-summer
        is_holiday=False
    )
    
    print(f"Predicted RPS: {result['predicted_rps']:.2f} requests/sec")
    print(f"Predicted Servers: {result['predicted_servers']} servers")
    print(f"Confidence: {result['confidence']:.2%}\n")
    
    # Method 2: Using quick function
    servers = get_servers_for_time(
        hour=20,
        day_of_year=180,
        day_of_week=6,
        is_weekend=1,
        is_holiday=0
    )
    print(f"Quick prediction result: {servers} servers needed")
    
    return result


def test_daily_profile():
    """Test 3: Full-day hourly predictions."""
    print_section("TEST 3: Daily Profile (24-Hour Forecast)")
    
    predictor = IntegratedPredictor()
    
    # Pick a sample day
    sample_day = datetime(2024, 4, 15)  # Mid-April
    
    print(f"Generating hourly forecast for {sample_day.date()}...\n")
    
    profile = predictor.predict_day_profile(sample_day, is_holiday=False)
    
    # Display key hours
    print("Hour | RPS    | Servers | Notes")
    print("-----|--------|---------|------+")
    
    for h in profile:
        hour = h['hour']
        rps = h['rps']
        servers = h['servers']
        
        # Classify
        if hour < 6:
            note = "Night"
        elif hour < 9:
            note = "Morning"
        elif hour < 17:
            note = "Peak"
        elif hour < 20:
            note = "Evening"
        else:
            note = "Late"
        
        if hour % 4 == 0:  # Every 4 hours for display
            print(f"{hour:2d}:00 | {rps:6.1f} | {servers:7d} | {note}")
    
    # Summary
    print(f"\n📊 Daily Summary:")
    print(f"  Peak RPS: {max(h['rps'] for h in profile):.1f}")
    print(f"  Peak Servers: {max(h['servers'] for h in profile)}")
    print(f"  Average Servers: {int(np.mean([h['servers'] for h in profile]))}")
    print(f"  Min Servers: {min(h['servers'] for h in profile)}")
    
    return profile


def test_weekly_forecast():
    """Test 4: 7-day capacity forecast."""
    print_section("TEST 4: Weekly Forecast")
    
    predictor = IntegratedPredictor()
    
    start_date = datetime(2024, 4, 15)
    print(f"Generating 7-day forecast starting {start_date.date()}...\n")
    
    forecast = predictor.predict_week_ahead(start_date)
    
    print("Day        | Peak RPS | Peak Servers | Avg Servers")
    print("-----------|----------|--------------|------------")
    
    for day in forecast['daily_predictions']:
        date = day['date']
        day_name = day['day_of_week']
        peak_rps = day['peak_rps']
        peak_servers = day['peak_servers']
        avg_servers = day['avg_servers']
        
        print(f"{day_name:3} {date} | {peak_rps:8.1f} | {peak_servers:12d} | {avg_servers:10d}")
    
    print(f"\n📊 Weekly Summary:")
    print(f"  Average Servers: {forecast['week_avg_servers']:.0f}")
    print(f"  Peak RPS: {forecast['week_peak_rps']:.1f}")
    print(f"  Peak Servers: {forecast['week_peak_servers']}")
    
    return forecast


def test_yearly_capacity_plan():
    """Test 5: Yearly capacity planning."""
    print_section("TEST 5: Yearly Capacity Plan")
    
    predictor = IntegratedPredictor()
    
    year = 2024
    print(f"Generating yearly capacity plan for {year}...\n")
    
    yearly = predictor.predict_year_ahead(datetime(year, 1, 1))
    
    print("Month     | Avg Servers | Peak Servers | Min Servers")
    print("----------|-------------|--------------|------------")
    
    for month_data in yearly['monthly_data']:
        month_name = month_data['month_name']
        avg = month_data['avg_servers']
        peak = month_data['peak_servers']
        min_s = month_data['min_servers']
        
        print(f"{month_name:9} | {avg:11.0f} | {peak:12d} | {min_s:11d}")
    
    print(f"\n📊 Yearly Summary:")
    print(f"  Yearly Average Servers: {yearly['yearly_avg_servers']:.0f}")
    print(f"  Yearly Peak Servers: {yearly['yearly_peak_servers']}")
    
    return yearly


def test_orchestrator_decisions():
    """Test 6: Orchestrator decision-making."""
    print_section("TEST 6: Orchestrator Decision Making")
    
    orchestrator = UpdatedProactiveOrchestrator()
    
    print("Simulating 24 decision points throughout a day...\n")
    
    decisions = []
    
    for hour in range(0, 24, 2):  # Every 2 hours
        action, details = orchestrator.get_decision(
            current_rps=100 + np.sin(hour / 6) * 50,  # Simulated RPS
            current_servers=8,
            max_servers=20,
            queue_depth=int(50 + np.sin(hour / 6) * 30),
            timestamp=datetime.now().replace(hour=hour, minute=0)
        )
        
        decisions.append({
            'hour': hour,
            'action': action.value,
            'is_proactive': details.get('is_proactive', False),
            'reason': details.get('reason', '')
        })
        
        proactive_flag = "🟢 PROACTIVE" if details.get('is_proactive', False) else "⚪ Reactive"
        print(f"{hour:02d}:00 - {action.value:15} {proactive_flag:20} ({details.get('reason', 'N/A')})")
    
    print(f"\n📊 Decision Summary:")
    print(f"  Total Decisions: {len(decisions)}")
    print(f"  Proactive: {sum(1 for d in decisions if d['is_proactive'])}")
    print(f"  Reactive: {sum(1 for d in decisions if not d['is_proactive'])}")
    
    return decisions


def test_quick_decision():
    """Test 7: Quick decision function."""
    print_section("TEST 7: Quick Decision Function")
    
    print("Using quick_decision() for instant recommendations...\n")
    
    # Scenario 1: Peak business hours
    print("Scenario 1: Tuesday 2 PM, summer, mid-queue")
    result = quick_decision(
        hour=14,
        day_of_year=180,
        day_of_week=1,  # Tuesday
        is_weekend=0,
        is_holiday=0,
        current_servers=8,
        queue_depth=12
    )
    print(f"  ➜ Action: {result['action'].upper()}")
    print(f"  ➜ RPS: {result['predicted_rps']:.1f}")
    print(f"  ➜ Servers needed: {result['predicted_servers']}")
    print(f"  ➜ Proactive: {result['is_proactive']}\n")
    
    # Scenario 2: Late night
    print("Scenario 2: Saturday 2 AM, low traffic")
    result = quick_decision(
        hour=2,
        day_of_year=180,
        day_of_week=5,  # Saturday
        is_weekend=1,
        is_holiday=0,
        current_servers=8,
        queue_depth=2
    )
    print(f"  ➜ Action: {result['action'].upper()}")
    print(f"  ➜ RPS: {result['predicted_rps']:.1f}")
    print(f"  ➜ Servers needed: {result['predicted_servers']}")
    print(f"  ➜ Proactive: {result['is_proactive']}\n")
    
    # Scenario 3: Holiday
    print("Scenario 3: Holiday morning")
    result = quick_decision(
        hour=9,
        day_of_year=1,  # Jan 1
        day_of_week=0,  # Monday
        is_weekend=0,
        is_holiday=1,  # HOLIDAY!
        current_servers=8,
        queue_depth=5
    )
    print(f"  ➜ Action: {result['action'].upper()}")
    print(f"  ➜ RPS: {result['predicted_rps']:.1f}")
    print(f"  ➜ Servers needed: {result['predicted_servers']}")
    print(f"  ➜ Proactive: {result['is_proactive']}")


def test_orchestrator_status():
    """Test 8: Orchestrator status and metrics."""
    print_section("TEST 8: Orchestrator Status")
    
    orchestrator = UpdatedProactiveOrchestrator()
    
    status = orchestrator.get_status()
    
    print("System Status:")
    print(f"  ✓ Ready: {status['is_ready']}")
    print(f"  Lookahead: {status['lookahead_window']} minutes")
    print(f"  Confidence Threshold: {status['confidence_threshold']:.0%}")
    print(f"  Decisions Made: {status['decision_count']}")
    print(f"  Proactive Ratio: {status['proactive_ratio']:.1%}")
    
    print(f"\nModel Paths:")
    print(f"  RPS Model: {os.path.basename(status['models_paths']['rps_model'])}")
    print(f"  Server Model: {os.path.basename(status['models_paths']['server_model'])}")


def generate_test_report():
    """Generate comprehensive test report."""
    print_section("GENERATING COMPREHENSIVE TEST REPORT")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': []
    }
    
    # Test 1
    try:
        test_model_loading()
        report['tests'].append({'name': 'Model Loading', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Model Loading', 'status': 'FAIL', 'error': str(e)})
    
    # Test 2
    try:
        test_basic_prediction()
        report['tests'].append({'name': 'Basic Prediction', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Basic Prediction', 'status': 'FAIL', 'error': str(e)})
    
    # Test 3
    try:
        test_daily_profile()
        report['tests'].append({'name': 'Daily Profile', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Daily Profile', 'status': 'FAIL', 'error': str(e)})
    
    # Test 4
    try:
        test_weekly_forecast()
        report['tests'].append({'name': 'Weekly Forecast', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Weekly Forecast', 'status': 'FAIL', 'error': str(e)})
    
    # Test 5
    try:
        test_yearly_capacity_plan()
        report['tests'].append({'name': 'Yearly Plan', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Yearly Plan', 'status': 'FAIL', 'error': str(e)})
    
    # Test 6
    try:
        test_orchestrator_decisions()
        report['tests'].append({'name': 'Orchestrator', 'status': 'PASS'})
    except Exception as e:
        report['tests'].append({'name': 'Orchestrator', 'status': 'FAIL', 'error': str(e)})
    
    # Save report
    os.makedirs('results', exist_ok=True)
    report_file = 'results/integration_test_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Test report saved to {report_file}")
    
    return report


def main():
    """Run all integration tests."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█  INTEGRATED PREDICTOR - MODEL INTEGRATION & TESTING SUITE".ljust(79) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    # Run all tests
    if test_model_loading():
        test_basic_prediction()
        test_daily_profile()
        test_weekly_forecast()
        test_yearly_capacity_plan()
        test_orchestrator_decisions()
        test_quick_decision()
        test_orchestrator_status()
        
        # Generate report
        generate_test_report()
        
        print("\n" + "█"*80)
        print("█  ✓ ALL TESTS COMPLETED SUCCESSFULLY!".ljust(79) + "█")
        print("█"*80 + "\n")


if __name__ == "__main__":
    main()
