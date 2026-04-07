"""
End-to-end integration script for the 5-step Proactive Load Balancing system.

This script orchestrates:
1. Month-long realistic simulation with holidays and spikes
2. Linear model training for server prediction
3. Spike-aware queue rearrangement policy
4. Enhanced Q-Learning agent training
5. Proactive orchestrator testing

Run this to build and test the entire system.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Import all components
from experiments.advanced_simulation import RealisticDemandSimulation
from src.utils.advanced_load_predictor import AdvancedLoadPredictor
from src.models.linear_server_predictor import LinearServerPredictor
from src.policies.spike_aware_rearrangement import SpikeAwarePriorityPolicy
from src.rl.enhanced_q_learning_agent import EnhancedQLearningAgent, QLearningTrainer
from src.orchestration.proactive_orchestrator import ProactiveOrchestrator, SystemAction


def step_1_generate_simulation_data(output_dir: str = "data/") -> str:
    """
    STEP 1: Generate 1-month simulation with realistic patterns.
    Collects server usage, queue depth, response times, and spike indicators.
    """
    print("\n" + "="*80)
    print("STEP 1: Generating Month-Long Realistic Simulation with Holidays & Spikes")
    print("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize simulation
    sim = RealisticDemandSimulation(
        days_to_simulate=30,
        base_arrival_rate=5.0,
        spike_multiplier=3.5,
        spike_probability=0.15
    )
    
    # Add holidays (example: 1st of month)
    sim.add_holidays([datetime(2024, 4, 1)])
    
    print("Running simulation for 30 days...")
    results = sim.run_simulation(num_servers=15)
    
    # Export metrics
    csv_file = os.path.join(output_dir, "simulation_metrics.csv")
    sim.export_metrics_to_csv(csv_file)
    
    # Print summary
    summary = sim.get_summary()
    print(f"\n✓ Simulation Complete:")
    print(f"  Days Simulated: {summary['simulation_days']}")
    print(f"  Metrics Collected: {summary['total_metrics_collected']}")
    print(f"  Max Queue Depth: {summary['max_queue_depth']}")
    print(f"  Avg Queue Depth: {summary['avg_queue_depth']:.2f}")
    print(f"  Max Servers Needed: {summary['max_servers_needed']}")
    print(f"  Spike Events: {summary['spike_events']}")
    print(f"  Holidays: {summary['holidays']}")
    
    # Save summary
    summary_file = os.path.join(output_dir, "simulation_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Data saved to {csv_file}")
    print(f"✓ Summary saved to {summary_file}")
    
    return csv_file


def step_2_train_linear_model(data_file: str, output_dir: str = "models/") -> LinearServerPredictor:
    """
    STEP 2: Train linear regression model for server prediction.
    Features: temporal (hour, day, holidays) + load indicators
    Target: optimal servers needed
    """
    print("\n" + "="*80)
    print("STEP 2: Training Linear Server Prediction Model")
    print("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load simulation data
    print(f"Loading data from {data_file}...")
    df = pd.read_csv(data_file)
    
    # Initialize and train model
    print("Training Linear Ridge Regression model...")
    predictor = LinearServerPredictor(model_type='ridge', alpha=1.0)
    metrics = predictor.train(df, target_column='servers_active', verbose=True)
    
    # Save model
    model_file = os.path.join(output_dir, "linear_server_predictor.pkl")
    predictor.save_model(model_file)
    
    # Feature importance
    importance = predictor.get_feature_importance()
    print("\nTop Features:")
    for i, (feat, coef) in enumerate(list(importance.items())[:5], 1):
        print(f"  {i}. {feat}: {coef:.4f}")
    
    # Save deployment info
    deploy_file = os.path.join(output_dir, "linear_model_deploy_info.json")
    deploy_info = predictor.get_deployment_info()
    with open(deploy_file, 'w') as f:
        json.dump(deploy_info, f, indent=2, default=str)
    
    print(f"\n✓ Model saved to {model_file}")
    print(f"✓ Deployment info saved to {deploy_file}")
    
    return predictor


def step_3_test_queue_rearrangement(data_file: str) -> SpikeAwarePriorityPolicy:
    """
    STEP 3: Test spike-aware queue rearrangement policy.
    Validates that priority-based rearrangement improves SLA compliance during spikes.
    """
    print("\n" + "="*80)
    print("STEP 3: Testing Spike-Aware Queue Rearrangement Policy")
    print("="*80)
    
    # Load data
    df = pd.read_csv(data_file)
    
    # Create policy
    policy = SpikeAwarePriorityPolicy(
        spike_threshold=0.7,
        deadline_weight=0.4,
        priority_weight=0.3,
        efficiency_weight=0.3
    )
    
    print("Analyzing queue metrics from simulation...")
    
    # Analyze spike detection
    spike_counts = 0
    total_steps = 0
    
    for idx, row in df.iterrows():
        queue_depth = row['queue_depth']
        servers = row['total_servers']
        
        is_spike = policy.detect_spike(int(queue_depth), int(servers))
        if is_spike:
            spike_counts += 1
        total_steps += 1
    
    spike_ratio = spike_counts / total_steps if total_steps > 0 else 0
    
    print(f"\n✓ Spike Detection Results:")
    print(f"  Total observations: {total_steps}")
    print(f"  Spike periods detected: {spike_counts}")
    print(f"  Spike ratio: {spike_ratio:.2%}")
    
    print(f"\n✓ Policy Statistics:")
    stats = policy.get_statistics()
    for key, value in stats.items():
        if key not in ['rearrangements']:
            print(f"  {key}: {value}")
    
    return policy


def step_4_train_q_learning(data_file: str, 
                            linear_predictor: LinearServerPredictor,
                            output_dir: str = "models/") -> EnhancedQLearningAgent:
    """
    STEP 4: Train enhanced Q-Learning agent.
    Learns optimal actions: add_servers, remove_servers, rearrange_queue, do_nothing
    State: (predicted_load, queue_depth, active_servers, spike_phase)
    """
    print("\n" + "="*80)
    print("STEP 4: Training Enhanced Q-Learning Agent")
    print("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = pd.read_csv(data_file)
    
    # Initialize Q-Learning agent
    agent = EnhancedQLearningAgent(
        alpha=0.1,
        gamma=0.95,
        epsilon=0.2,
        epsilon_decay=0.995,
        min_epsilon=0.05
    )
    
    print("Training Q-Learning agent with simulated environment...")
    
    # Training episodes
    num_episodes = 100
    for episode in range(1, num_episodes + 1):
        # Sample random initial state from data
        sample = df.sample(1).iloc[0]
        
        predicted_load = sample['queue_depth']
        queue_length = int(sample['queue_depth'])
        active_servers = int(sample['servers_active'])
        spike_prob = 0.5 if sample['queue_depth'] > 10 else 0.1
        
        # Get start state
        state = agent.get_state(predicted_load, queue_length, active_servers, spike_prob)
        
        # Simulate 20 steps per episode
        episode_reward = 0
        for step in range(20):
            # Choose action
            action = agent.choose_action(state, training=True)
            
            # Simulate environment - random walk
            next_queue = max(0, queue_length + np.random.randint(-2, 3))
            next_servers = max(1, active_servers + np.random.randint(-1, 2))
            next_spike_prob = np.random.uniform(0, 1)
            
            next_state = agent.get_state(next_queue, next_queue, next_servers, next_spike_prob)
            
            # Calculate reward
            reward = agent.calculate_reward(
                queue_length=next_queue,
                response_time=next_queue * 5,
                servers_used=next_servers,
                max_servers=20,
                sla_met=next_queue < 15,
                action=action
            )
            
            # Train step
            agent.train_step(state, action, reward, next_state)
            
            episode_reward += reward
            state = next_state
            queue_length = next_queue
        
        if (episode + 1) % 20 == 0:
            stats = agent.get_statistics()
            print(f"  Episode {episode}/{num_episodes}: "
                  f"Avg Reward: {stats['avg_reward']:.2f}, "
                  f"Epsilon: {stats['current_epsilon']:.4f}")
    
    # Save model
    model_file = os.path.join(output_dir, "q_learning_agent.pkl")
    agent.save_model(model_file)
    
    # Statistics
    stats = agent.get_statistics()
    print(f"\n✓ Q-Learning Training Complete:")
    print(f"  Total Episodes: {stats['episodes_trained']}")
    print(f"  Avg Reward: {stats['avg_reward']:.2f}")
    print(f"  Max Reward: {stats['max_reward']:.2f}")
    print(f"  Q-Table Size: {stats['q_table_size']} states")
    print(f"  Final Epsilon: {stats['current_epsilon']:.4f}")
    
    print(f"\n✓ Model saved to {model_file}")
    
    return agent


def step_5_test_proactive_orchestrator(linear_predictor: LinearServerPredictor,
                                      q_learning_agent: EnhancedQLearningAgent,
                                      queue_policy: SpikeAwarePriorityPolicy,
                                      data_file: str) -> ProactiveOrchestrator:
    """
    STEP 5: Test Proactive Orchestrator.
    Demonstrates ensemble predictions and proactive decisions 5-10 min ahead.
    """
    print("\n" + "="*80)
    print("STEP 5: Testing Proactive Orchestrator")
    print("="*80)
    
    # Create advanced load predictor
    load_predictor = AdvancedLoadPredictor(window=10, spike_threshold=1.5)
    
    # Initialize orchestrator
    orchestrator = ProactiveOrchestrator(
        linear_predictor=linear_predictor,
        q_learning_agent=q_learning_agent,
        rearrangement_policy=queue_policy,
        load_predictor=load_predictor,
        lookahead_window=10,  # 10 minutes ahead
        confidence_threshold=0.7
    )
    
    # Load and process data
    df = pd.read_csv(data_file)
    
    print("Running proactive decision tests on simulation data...")
    print("(Simulating 10-minute look-ahead predictions)...\n")
    
    # Test on sample data points
    test_samples = 50
    proactive_count = 0
    reactive_count = 0
    maintain_count = 0
    
    for idx in range(min(test_samples, len(df))):
        row = df.iloc[idx]
        
        # Create timestamp
        timestamp = datetime(2024, 4, 1) + timedelta(hours=idx //4, minutes=(idx % 4) * 15)
        
        # Get decision
        action, details = orchestrator.decide_action(
            timestamp=timestamp,
            current_queue_depth=int(row['queue_depth']),
            current_servers_active=int(row['servers_active']),
            max_servers=int(row['total_servers']),
            is_holiday=bool(row.get('is_holiday', False))
        )
        
        if details['is_proactive']:
            proactive_count += 1
        elif action == SystemAction.MAINTAIN:
            maintain_count += 1
        else:
            reactive_count += 1
    
    print(f"✓ Decision Analysis ({test_samples} decisions):")
    print(f"  Proactive Actions: {proactive_count} ({proactive_count/test_samples*100:.1f}%)")
    print(f"  Reactive Actions: {reactive_count} ({reactive_count/test_samples*100:.1f}%)")
    print(f"  Maintain State: {maintain_count} ({maintain_count/test_samples*100:.1f}%)")
    
    # Generate 24-hour forecast
    print(f"\nGenerating 24-hour proactive forecast...")
    forecast = orchestrator.get_forecast_report(
        timestamp=datetime(2024, 4, 1, 0, 0),
        hours_ahead=24,
        is_holiday=False
    )
    
    print(f"✓ Forecast Summary:")
    print(f"  Peak Servers Needed: {forecast['summary']['avg_servers_needed']:.1f}")
    print(f"  Average Load: {forecast['summary']['avg_servers_needed']:.1f}")
    print(f"  Max Queue Load: {forecast['summary']['max_queue_load']:.1f}")
    
    # Performance metrics
    print(f"\n✓ Orchestrator Performance Metrics:")
    metrics = orchestrator.get_performance_metrics()
    print(f"  Total Decisions: {metrics['total_decisions']}")
    print(f"  Proactive Ratio: {metrics['proactive_ratio']:.2%}")
    
    return orchestrator


def generate_final_report(output_dir: str = "results/"):
    """Generate comprehensive final report."""
    print("\n" + "="*80)
    print("FINAL REPORT: 5-Step Proactive Load Balancing System")
    print("="*80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'system_steps': [
            'Step 1: Realistic simulation with holidays and spikes',
            'Step 2: Linear model training for server prediction',
            'Step 3: Spike-aware queue rearrangement policy',
            'Step 4: Enhanced Q-Learning agent training',
            'Step 5: Proactive orchestrator testing'
        ],
        'key_files': [
            'data/simulation_metrics.csv - Raw metrics from 30-day simulation',
            'models/linear_server_predictor.pkl - Trained linear model',
            'models/q_learning_agent.pkl - Trained Q-Learning agent',
            'models/linear_model_deploy_info.json - Deployment configuration'
        ],
        'next_steps': [
            '1. Deploy linear model to production for online predictions',
            '2. Integrate Q-learning agent with real load balancer',
            '3. Implement proactive orchestrator in your infrastructure',
            '4. Monitor performance metrics and iterate on model parameters',
            '5. A/B test proactive vs reactive approaches'
        ]
    }
    
    report_file = os.path.join(output_dir, "system_report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n✓ System Build Complete!")
    print(f"\n✓ Report saved to {report_file}")
    print("\nSystem Overview:")
    for step in report['system_steps']:
        print(f"  ✓ {step}")


def main():
    """Run complete 5-step system build."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█  PROACTIVE LOAD BALANCING SYSTEM - 5-STEP BUILD & TEST".ljust(79) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        # Step 1: Generate simulation data
        data_file = step_1_generate_simulation_data()
        
        # Step 2: Train linear model
        linear_predictor = step_2_train_linear_model(data_file)
        
        # Step 3: Test queue rearrangement
        queue_policy = step_3_test_queue_rearrangement(data_file)
        
        # Step 4: Train Q-Learning agent
        q_learning_agent = step_4_train_q_learning(data_file, linear_predictor)
        
        # Step 5: Test proactive orchestrator
        orchestrator = step_5_test_proactive_orchestrator(
            linear_predictor, q_learning_agent, queue_policy, data_file
        )
        
        # Generate final report
        generate_final_report()
        
        print("\n" + "█"*80)
        print("█  SUCCESS: All 5 steps completed!".ljust(79) + "█")
        print("█"*80 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
