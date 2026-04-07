# 📚 COMPLETE PROJECT FILES REFERENCE - All Functions & Functionality

**Generated:** April 7, 2026  
**Project:** CAPR Load Balancing System  
**Total Files:** 30 Python files

---

## 🗂️ TABLE OF CONTENTS

1. [CORE Module](#core-module)
2. [BALANCING Module](#balancing-module)
3. [MODELS Module](#models-module)
4. [POLICIES Module](#policies-module)
5. [RL Module](#rl-module)
6. [ORCHESTRATION Module](#orchestration-module)
7. [UTILS Module](#utils-module)
8. [EXPERIMENTS Module](#experiments-module)
9. [TESTS Module](#tests-module)
10. [CONFIGS Module](#configs-module)

---

## CORE MODULE
**Location:** `src/core/`  
**Purpose:** Basic simulation entities, servers, events, routing engine, and main simulation loop

### 1️⃣ `event.py` - Event Class
```
CLASS: Event
├─ __init__(event_id, arrival_time, deadline, exec_time, resource, business)
│   └─ Creates event with all attributes
├─ is_deadline_violated() → bool
│   └─ Checks if deadline exceeded
├─ get_priority_score(metric) → float
│   └─ Calculates priority based on deadline/business value
└─ __repr__() → str
    └─ String representation
```
**Fields:**
- `id`, `arrival_time`, `deadline_remaining`, `estimated_execution_time`
- `resource_requirement`, `business_priority_level`, `waiting_time`
- `start_time`, `finish_time`

---

### 2️⃣ `server.py` - Server Class
```
CLASS: Server
├─ __init__(server_id, capacity)
│   └─ Initialize server with ID and capacity
├─ add_job(event) → None
│   └─ Add event to server queue
├─ process() → bool
│   └─ Process current event, return if finished
├─ is_available() → bool
│   └─ Check if server is free
├─ get_queue_depth() → int
│   └─ Return number of events waiting
├─ get_utilization() → float
│   └─ Return CPU utilization percentage
└─ reset() → None
    └─ Clear all jobs and reset state
```
**Fields:**
- `id`, `capacity`, `jobs` (queue), `current_job`, `time_busy`

---

### 3️⃣ `routing_engine.py` - RoutingEngine Class
```
CLASS: RoutingEngine
├─ __init__(balancer, policy)
│   └─ Initialize with balancing strategy and rearrangement policy
├─ route_event(event, servers) → Server
│   └─ Route event to best server using balancer
├─ handle_spike(queue, load_predictor) → list
│   └─ Rearrange queue during demand spike
├─ get_routing_decisions() → dict
│   └─ Return routing statistics
├─ reset_stats() → None
│   └─ Clear routing metrics
└─ get_load_per_server(servers) → list
    └─ Return load on each server
```
**Integrates:** Balancer + Policy for intelligent routing

---

### 4️⃣ `simulation_environment.py` - SimulationEnvironment Class
```
CLASS: SimulationEnvironment
├─ __init__(num_servers=10, max_queue_size=100)
│   └─ Initialize simulation with servers and queue
├─ add_event(event) → bool
│   └─ Add event to queue, return success
├─ get_server_by_id(id) → Server
│   └─ Find server by ID
├─ get_queue_depth() → int
│   └─ Return total queue size
├─ advance_time(delta) → dict
│   └─ Process events for time delta, return metrics
├─ get_metrics() → dict
│   └─ Return all current metrics
├─ scale_servers(count) → None
│   └─ Add/remove servers dynamically
└─ reset() → None
    └─ Reset all metrics and state
```
**Simulates:** Queue, servers, time progression, event processing

---

## BALANCING MODULE
**Location:** `src/balancing/`  
**Purpose:** Load balancer strategies for routing events to servers

### 1️⃣ `base_balancer.py` - BaseBalancer Class
```
CLASS: BaseBalancer (ABSTRACT)
├─ __init__() - Constructor
├─ select_server(event, servers) → Server [ABSTRACT]
│   └─ Must be implemented by subclasses
├─ name() → str
│   └─ Return balancer name
└─ get_stats() → dict
    └─ Return balancer statistics
```
**Interface:** Base class for all balancer strategies

---

### 2️⃣ `least_loaded_balancer.py` - LeastLoadedBalancer Class
```
CLASS: LeastLoadedBalancer(BaseBalancer)
├─ __init__()
│   └─ Initialize balancer
├─ select_server(event, servers) → Server [OVERRIDE]
│   └─ Return server with lowest queue depth
├─ name() → str
│   └─ Return "LeastLoadedBalancer"
└─ get_stats() → dict
    └─ Return balancing statistics
```
**Strategy:** Always pick server with least queue

---

## MODELS MODULE
**Location:** `src/models/`  
**Purpose:** Machine learning models for predictions

### 1️⃣ `linear_server_predictor.py` - LinearServerPredictor Class
```
CLASS: LinearServerPredictor
├─ __init__(model_type='ridge')
│   └─ Initialize with Ridge regression
├─ train(X_train, y_train, X_test, y_test) → dict
│   └─ Train model, return metrics
├─ predict_servers(features) → int
│   └─ Predict servers needed (0-15)
├─ predict_servers_batch(features_list) → list
│   └─ Batch prediction
├─ save_model(filepath) → None
│   └─ Save to pickle
├─ load_model(filepath) → bool
│   └─ Load from pickle
├─ get_feature_importance() → list
│   └─ Return top 10 features
└─ get_model_metrics() → dict
    └─ Return R², RMSE, MAE
```
**Predicts:** Number of servers needed based on features

---

### 2️⃣ `integrated_predictor.py` - IntegratedPredictor Class
```
CLASS: IntegratedPredictor
├─ __init__(rps_model_path, server_model_path)
│   └─ Load both RPS and Server models
├─ predict_rps(hour, day_of_year, day_of_week, is_weekend, is_holiday) → float
│   └─ Predict requests/second
├─ predict_servers(features) → int
│   └─ Predict servers needed
├─ forecast_24_hours(start_hour=0) → list
│   └─ 24-hour prediction with hourly breakdown
├─ forecast_7_days() → dict
│   └─ Weekly forecast
├─ get_prediction_confidence(prediction) → float
│   └─ Return confidence score
└─ get_model_info() → dict
    └─ Return model metadata
```
**Two-Stage:** RPS → Servers pipeline

---

## POLICIES MODULE
**Location:** `src/policies/`  
**Purpose:** Queue management and task prioritization strategies

### 1️⃣ `base_rearrangement_policy.py` - BaseRearrangementPolicy Class
```
CLASS: BaseRearrangementPolicy (ABSTRACT)
├─ __init__()
├─ should_rearrange(queue) → bool [ABSTRACT]
│   └─ Decision to rearrange queue
├─ rearrange_queue(queue, current_time) → list [ABSTRACT]
│   └─ Return reordered queue
└─ get_policy_metrics() → dict
    └─ Return policy statistics
```
**Interface:** Base class for all policies

---

### 2️⃣ `spike_aware_rearrangement.py` - SpikeAwarePriorityPolicy Class
```
CLASS: SpikeAwarePriorityPolicy(BaseRearrangementPolicy)
├─ __init__(spike_threshold=0.7)
│   └─ Initialize with spike detection threshold
├─ detect_spike(queue_depth, max_servers, load_prediction=None) → bool
│   └─ Detect if demand spike occurring
├─ calculate_priority_score(event, time_since_arrival, queue_position) → float
│   └─ Calculate priority: 40% deadline + 30% business + 30% efficiency
├─ should_rearrange(queue) → bool [OVERRIDE]
│   └─ Return True if spike detected
├─ rearrange_queue(queue, current_time, max_servers=10) → list [OVERRIDE]
│   └─ Sort queue by priority score
├─ get_spike_metrics() → dict
│   └─ Return spike detection stats
└─ get_policy_metrics() → dict
    └─ Return all policy metrics
```
**Formula:** Priority = 0.4×deadline_urgency + 0.3×business_value + 0.3×execution_efficiency

---

### 3️⃣ `weighted_priority_rearrangement.py` - WeightedPriorityRearrangement Class
```
CLASS: WeightedPriorityRearrangement(BaseRearrangementPolicy)
├─ __init__(deadline_weight=0.5, business_weight=0.3, efficiency_weight=0.2)
│   └─ Initialize weights (sum must = 1.0)
├─ set_weights(deadline_w, business_w, efficiency_w) → bool
│   └─ Update weights
├─ calculate_priority(event, time_info, queue_position) → float
│   └─ Weighted priority calculation
├─ should_rearrange(queue) → bool [OVERRIDE]
│   └─ Check if rearrangement needed
├─ rearrange_queue(queue, current_time) → list [OVERRIDE]
│   └─ Sort by weighted priority
└─ get_policy_metrics() → dict
    └─ Return metrics
```
**Flexible:** Configurable weights for priorities

---

## RL MODULE
**Location:** `src/rl/`  
**Purpose:** Reinforcement Learning agents for adaptive decisions

### 1️⃣ `simple_q_learning_agent.py` - SimpleQLearningAgent Class
```
CLASS: SimpleQLearningAgent
├─ __init__(learning_rate=0.1, discount_factor=0.9, epsilon=0.1)
│   └─ Initialize Q-Learning parameters
├─ discretize_state(queue_length) → int
│   └─ Convert queue (0-100+) to 5 states (0-4)
├─ select_action(state) → int (EPSILON-GREEDY)
│   └─ Choose ADD(0) or REMOVE(1) server action
├─ learn(state, action, reward, next_state) → None
│   └─ Update Q-table using Bellman equation
├─ get_q_value(state, action) → float
│   └─ Return Q(s,a)
├─ save_model(filepath) → None
│   └─ Save Q-table to pickle
├─ load_model(filepath) → bool
│   └─ Load Q-table
├─ get_policy() → dict
│   └─ Return learned policy (state → best action)
└─ reset() → None
    └─ Clear Q-table
```
**State Space:** 5 states (queue: empty, low, medium, high, very high)  
**Action Space:** 2 actions (ADD_SERVER, REMOVE_SERVER)

---

### 2️⃣ `q_learning_agent.py` - QLearningAgent Class
```
CLASS: QLearningAgent(SimpleQLearningAgent)
├─ __init__(learning_rate, discount_factor, epsilon, decay_rate=0.995)
│   └─ Add epsilon decay
├─ discretize_state(queue_length) → int
│   └─ 10 states instead of 5
├─ select_action(state) → int [OVERRIDE]
│   └─ Epsilon-greedy with decay
├─ decay_epsilon() → None
│   └─ Reduce exploration rate
├─ train_episode(env, steps=100) → float
│   └─ Run one training episode, return total reward
└─ get_stats() → dict
    └─ Return training statistics
```
**Enhanced:** More states, epsilon decay, episode training

---

### 3️⃣ `enhanced_q_learning_agent.py` - EnhancedQLearningAgent Class
```
CLASS: EnhancedQLearningAgent
├─ __init__(lr=0.01, gamma=0.95, epsilon=0.2, decay=0.995)
│   └─ Initialize enhanced Q-Learning
├─ discretize_state(load, queue, servers, spike_prob) → tuple
│   └─ Multi-dimensional: (load_bucket, queue_bucket, server_bucket, spike_bucket)
│   └─ Creates 10×10×10×4 = 4000+ possible states
├─ get_recommended_action(predicted_load, queue_length, active_servers, 
│                         max_servers, spike_probability) → (int, float)
│   └─ Return action + confidence score
├─ select_action(state) → int
│   └─ Choose from 4 actions: ADD, REMOVE, REARRANGE, IDLE
├─ learn(state, action, reward, next_state, done) → None
│   └─ Q-Learning update
├─ train(env, episodes=100, max_steps=500) → dict
│   └─ Train agent, return training history
├─ get_q_table() → dict
│   └─ Return learned Q-values
├─ save_model(filepath) → None
│   └─ Save to pickle
├─ load_model(filepath) → bool
│   └─ Load from pickle
└─ get_stats() → dict
    └─ Return training/deployment stats
```
**Advanced:**
- **State Space:** 4000+ states (10×10×10×4)
- **Action Space:** 4 actions (ADD, REMOVE, REARRANGE, IDLE)
- **State Discretization:**
  - Load: 10 buckets (0-100)
  - Queue: 10 buckets (0-50)
  - Servers: 10 buckets (0-20)
  - Spike Probability: 4 buckets (0-3)

---

## ORCHESTRATION MODULE
**Location:** `src/orchestration/`  
**Purpose:** Master controllers combining all components

### 1️⃣ `proactive_orchestrator.py` - ProactiveOrchestrator Class
```
CLASS: ProactiveOrchestrator
├─ __init__(load_predictor, queue_policy, rl_agent=None)
│   └─ Initialize with all decision components
├─ make_decision(current_state, prediction_window=10) → dict
│   └─ Return: {action, confidence, is_proactive, reasoning}
├─ predict_future_load(minutes_ahead=10) → float
│   └─ Predict load in N minutes
├─ should_scale_up(current_servers, predicted_load, queue) → bool
│   └─ Determine if need to add servers
├─ should_scale_down(current_servers, predicted_load, queue) → bool
│   └─ Determine if can remove servers
├─ should_rearrange_queue(queue, load_prediction) → bool
│   └─ Determine if queue rearrangement needed
├─ get_decision_confidence(decision) → float
│   └─ Calculate confidence (0-1)
├─ forecast_24_hours() → list
│   └─ 24-hour proactive forecast
├─ get_orchestrator_metrics() → dict
│   └─ Return decision statistics and ratios
├─ save_checkpoint(filepath) → None
│   └─ Save decision history
└─ reset_metrics() → None
    └─ Clear all tracking
```
**Combines:** Load Predictor (30%) + RL Agent (20%) + Policy (50%)  
**Lookahead:** 5-10 minute prediction window  
**Decision Types:** ADD, REMOVE, REARRANGE, MAINTAIN, SCALE_DOWN, EMERGENCY_SCALE

---

### 2️⃣ `updated_orchestrator.py` - UpdatedOrchestrator Class
```
CLASS: UpdatedOrchestrator(ProactiveOrchestrator)
├─ __init__(integrated_predictor, policy, rl_agent=None)
│   └─ Uses IntegratedPredictor (2-stage: RPS → Servers)
├─ make_recommendation(hour, day_of_year, day_of_week, 
│                      is_weekend, is_holiday, 
│                      current_servers, queue_depth) → dict
│   └─ Integrated prediction-based recommendation
├─ get_daily_schedule() → list
│   └─ 24 recommended server counts
├─ predict_peak_times() → list
│   └─ Return hours with highest predicted load
├─ get_cost_analysis(schedule) → dict
│   └─ Analyze cost of given schedule
└─ optimize_schedule() → list
    └─ Find optimal 24-hour schedule
```
**Enhanced:** Uses trained RPS and Server models  
**Output:** Specific server count recommendations

---

### 3️⃣ `multi_horizon_orchestrator.py` - MultiHorizonOrchestrator Class
```
CLASS: MultiHorizonOrchestrator
├─ __init__(load_predictor, rl_agent, policy)
│   └─ Multi-level prediction system
├─ make_multi_horizon_decision(current_state) → dict
│   └─ Combines 3-layer approach
├─ get_daily_recommendation(hour, day_of_year) → dict
│   └─ Daily (24-hour) planning, executed at 6 AM
├─ get_hourly_checkpoint(current_time) → dict
│   └─ Hourly verification, executed at :00
├─ get_tactical_decision(predicted_load, queue, servers) → dict
│   └─ Tactical 5-10 min lookahead, every 5 min
├─ get_layer_weights() → dict
│   └─ Return: {daily: 0.4, hourly: 0.35, tactical: 0.25}
├─ calculate_proactivity_score() → float
│   └─ Overall proactivity percentage (40-60%)
└─ get_multi_horizon_metrics() → dict
    └─ Return all 3-layer metrics
```
**3-Layer Approach:**
1. **Daily** (6 AM): Plan entire day
2. **Hourly** (every :00): Verify & adjust
3. **Tactical** (every 5 min): Real-time 5-10 min decisions

---

## UTILS MODULE
**Location:** `src/utils/`  
**Purpose:** Utility functions and helper classes

### 1️⃣ `load_predictor.py` - LoadPredictor Class
```
CLASS: LoadPredictor
├─ __init__()
│   └─ Initialize predictor
├─ predict_load(timestamp, is_holiday=False) → float
│   └─ Predict requests/sec at timestamp
├─ get_time_of_day_load(hour) → float
│   └─ Return load multiplier (0.4-1.3) by hour
├─ get_day_of_week_load(day_of_week) → float
│   └─ Return load multiplier (0.4-1.3) by day
├─ get_holiday_load(timestamp) → float
│   └─ Return load multiplier (0.5 for holidays)
├─ predict_hourly_trends() → list
│   └─ Return 24 hourly load predictions
└─ get_predictor_stats() → dict
    └─ Return predictor metrics
```
**Patterns:** Time-of-day, day-of-week, holidays

---

### 2️⃣ `advanced_load_predictor.py` - AdvancedLoadPredictor Class
```
CLASS: AdvancedLoadPredictor(LoadPredictor)
├─ __init__()
│   └─ Enhanced predictor with spike detection
├─ predict_load(timestamp, is_holiday=False) → float [OVERRIDE]
│   └─ Base prediction
├─ predict_spike_probability(lookahead_minutes=10) → float
│   └─ Return spike probability (0-1)
├─ detect_spike_pattern(historical_data) → bool
│   └─ Detect recurring spikes
├─ get_spike_multiplier() → float
│   └─ Return spike load multiplier (3.0-5.0)
├─ forecast_24_hours() → list
│   └─ 24-hour forecasts with spike probabilities
├─ get_anomaly_score(current_load, predicted_load) → float
│   └─ Detect if current load is anomalous
└─ get_advanced_stats() → dict
    └─ Return spike and anomaly stats
```
**Advanced:** Spike detection + anomaly scoring

---

### 3️⃣ `priority_utils.py` - Priority Utility Functions
```
FUNCTION: calculate_deadline_urgency(event, current_time) → float
└─ How urgent is deadline? (0-1)

FUNCTION: calculate_business_value(event) → float
└─ Business value of event (0-1)

FUNCTION: calculate_execution_efficiency(event) → float
└─ How quickly can we execute? (0-1)

FUNCTION: combine_priority_signals(urgency, business, efficiency, weights) → float
└─ Weighted combination (0-1)

FUNCTION: get_priority_metrics(queue, weights) → dict
└─ Return priority distribution stats

FUNCTION: is_priority_violation(event, current_time, sla_deadline) → bool
└─ Check if priority SLA violated

FUNCTION: rank_events_by_priority(events, weights) → list
└─ Sort events by priority
```

---

## EXPERIMENTS MODULE
**Location:** `experiments/`  
**Purpose:** Testing, validation, and comparison scripts

### 1️⃣ `run_full_system_build.py` - Complete 5-Step Build
```
FUNCTION: step_1_generate_simulation_data() → str
└─ Generate 30-day realistic simulation with spikes

FUNCTION: step_2_train_server_predictor() → str
└─ Train Linear Ridge regression for server prediction

FUNCTION: step_3_test_spike_aware_policy() → dict
└─ Test queue rearrangement during spikes

FUNCTION: step_4_train_q_learning_agent() → dict
└─ Train QL agent with simulated environment

FUNCTION: step_5_test_proactive_orchestrator() → dict
└─ Test orchestrator with lookahead predictions

FUNCTION: main() → None
└─ Run all 5 steps sequentially

GENERATES: Models, metrics, comparison plots
```

---

### 2️⃣ `advanced_simulation.py` - RealisticDemandSimulation Class
```
CLASS: RealisticDemandSimulation
├─ __init__(days_to_simulate=30, base_arrival_rate=5.0, spike_multiplier=3.0)
│   └─ Initialize 30-day simulation
├─ get_time_of_day_multiplier(hour) → float
│   └─ Peak business hours (9-17): 1.3×
├─ get_day_of_week_multiplier(day) → float
│   └─ Mon-Thu: 1.0, Fri: 0.85, Sat-Sun: 0.4
├─ is_holiday(timestamp) → bool
│   └─ Check if holiday (50% load reduction)
├─ should_generate_spike() → bool
│   └─ Random spike generator (15% per hour)
├─ get_arrival_rate_for_time(timestamp) → float
│   └─ Combined rate = base × time × day × holiday × spike
├─ run_simulation(num_servers=15) → dict
│   └─ Run full 30-day simulation
├─ event_producer(env, queue, start_time) → None
│   └─ Generate events with realistic patterns
├─ routing_logic(env, queue, servers, logs) → None
│   └─ Route events to servers
└─ metrics_collector(env, queue, servers, start_time) → None
    └─ Collect metrics every 5 minutes
```

---

### 3️⃣ `test_integration.py` - Integration Tests
```
TEST: test_model_loading()
└─ Verify LinearServerPredictor loads

TEST: test_basic_prediction()
└─ Verify basic load prediction works

TEST: test_daily_profile()
└─ Verify time-of-day patterns

TEST: test_orchestrator_decisions()
└─ Verify orchestrator makes good decisions

TEST: test_spike_detection()
└─ Verify spike detection works

TEST: test_queue_rearrangement()
└─ Verify policy rearranges correctly

TEST: test_24_hour_forecast()
└─ Verify 24-hour forecasting

TEST: test_ensemble_prediction()
└─ Verify combining multiple predictions

GENERATES: integration_test_report.json
```

---

### 4️⃣ `compare_ql_models.py` - QL Model Comparison
```
FUNCTION: compare_simple_vs_enhanced() → dict
└─ Compare SimpleQLearningAgent vs EnhancedQLearningAgent

FUNCTION: benchmark_decision_quality() → dict
└─ Measure decision accuracy of each model

FUNCTION: benchmark_training_speed() → dict
└─ Measure training time of each model

FUNCTION: generate_comparison_report() → None
└─ Create comparison plots and metrics
```

---

### 5️⃣ `generate_new_comparisons.py` - New Comparison Plots
```
CLASS: ComparisonGenerator
├─ run_comparisons(load_levels=[2,4,6,8,10,12]) → DataFrame
│   └─ Generate comparison at each load level
├─ plot_response_time_comparison() → None
│   └─ Create response time plot
├─ plot_efficiency_comparison() → None
│   └─ Create queue & CPU utilization plot
├─ plot_throughput_comparison() → None
│   └─ Create throughput + improvement plot
├─ plot_comprehensive_dashboard() → None
│   └─ All metrics in one dashboard
├─ save_comparison_csv() → None
│   └─ Export comparison data
└─ generate_all_plots() → None
    └─ Generate all visualizations

OUTPUTS: 6 PNG charts + CSV + JSON summary
```

---

## TESTS MODULE
**Location:** `tests/`  
**Purpose:** Comprehensive testing suite

### Unit Tests (`tests/unit/`)
```
test_load_predictor.py
├─ test_prediction_range()
├─ test_time_patterns()
└─ test_holiday_effects()

test_q_learning_agent.py
├─ test_state_discretization()
├─ test_action_selection()
├─ test_q_value_update()
└─ test_policy_convergence()

test_routing_engine.py
├─ test_routing_selection()
├─ test_spike_handling()
└─ test_stats_tracking()

test_priority_policy.py
├─ test_priority_scoring()
├─ test_queue_rearrangement()
└─ test_deadline_handling()

test_overload_system.py
├─ test_overload_detection()
├─ test_emergency_scaling()
└─ test_crash_avoidance()
```

### System Tests (`tests/system/`)
```
test_sla.py
├─ test_deadline_compliance()
├─ test_p99_latency()
└─ test_business_priority_sla()

test_stability.py
├─ test_system_stability()
├─ test_metrics_consistency()
└─ test_long_running()

test_scaling_behavior.py
├─ test_auto_scaling()
├─ test_scale_up_decisions()
└─ test_scale_down_decisions()

test_priority_violation.py
├─ test_violation_detection()
├─ test_violation_prevention()
└─ test_recovery()

test_breaking_point.py
├─ test_max_load()
├─ test_queue_capacity()
└─ test_graceful_degradation()
```

### Performance Tests (`tests/performance/`)
```
test_rl_learning_curve.py
├─ test_ql_convergence()
├─ test_learning_speed()
└─ test_final_policy_quality()

test_mode_comparison.py
├─ test_baseline_vs_proactive()
├─ test_baseline_vs_threshold()
├─ test_baseline_vs_rl()
└─ test_all_modes_metrics()

test_scalability.py
├─ test_load_2_requests_per_sec()
├─ test_load_10_requests_per_sec()
├─ test_load_12_requests_per_sec()
└─ test_system_throughput()

test_thrashing.py
├─ test_no_thrashing_oscillation()
├─ test_scaling_stability()
└─ test_decision_consistency()
```

---

## CONFIGS MODULE
**Location:** `configs/`  
**Purpose:** Configuration parameters

### `simulation_config.py`
```
CONSTANTS:
├─ SIMULATION_DAYS = 30
├─ BASE_ARRIVAL_RATE = 5.0 requests/sec
├─ MAX_SERVERS = 15
├─ SPIKE_MULTIPLIER = 3.0-5.0
├─ SPIKE_PROBABILITY = 0.15 per hour
│
├─ RL_LEARNING_RATE = 0.01-0.1
├─ RL_DISCOUNT_FACTOR = 0.9-0.95
├─ RL_EPSILON = 0.2 (exploration rate)
├─ RL_EPISODES = 100
│
├─ PRIORITY_WEIGHTS = {
│      deadline: 0.4-0.5,
│      business: 0.3,
│      efficiency: 0.2-0.3
│   }
├─ SPIKE_THRESHOLD = 0.7
│
├─ PREDICTION_LOOKAHEAD = 10 minutes
├─ SCALE_DOWN_THRESHOLD = 0.3 (queue)
├─ SCALE_UP_THRESHOLD = 0.8 (queue)
│
└─ OUTPUT_PATHS = {
       models/, data/, results/
   }
```

---

## 📊 QUICK REFERENCE TABLE

| Component | File | Main Class | Purpose |
|-----------|------|-----------|---------|
| **Events** | event.py | Event | Task representation |
| **Servers** | server.py | Server | Compute resources |
| **Routing** | routing_engine.py | RoutingEngine | Task → Server mapping |
| **Simulation** | simulation_environment.py | SimulationEnvironment | Main simulation loop |
| **Balancer** | least_loaded_balancer.py | LeastLoadedBalancer | Baseline strategy |
| **Prediction** | linear_server_predictor.py | LinearServerPredictor | ML model for capacity |
| **Integration** | integrated_predictor.py | IntegratedPredictor | 2-stage RPS→Servers |
| **Queue Policy** | spike_aware_rearrangement.py | SpikeAwarePriorityPolicy | Smart queue management |
| **Simple QL** | simple_q_learning_agent.py | SimpleQLearningAgent | Basic Q-Learning |
| **Enhanced QL** | enhanced_q_learning_agent.py | EnhancedQLearningAgent | Advanced multi-state QL |
| **Orchestrator** | proactive_orchestrator.py | ProactiveOrchestrator | Main decision engine |
| **Multi-Layer** | multi_horizon_orchestrator.py | MultiHorizonOrchestrator | 3-layer decision making |
| **Load Utils** | advanced_load_predictor.py | AdvancedLoadPredictor | Spike detection & forecasting |

---

## 🔄 DATA FLOW EXAMPLES

### ➡️ BASELINE MODE (LeastLoadedBalancer)
```
Event → Route Engine → Least Loaded Balancer → Pick Server → Execute
              ↓ (deterministic, reactive)
```

### ➡️ PROACTIVE MODE (Full System)
```
Event → Prediction (load in 10 min?) → Route Engine → Policy (rearrange?) 
          → Orchestrator (scale servers?) → Execute
```

### ➡️ RL MODE (Learning)
```
Event + State → QL Agent (learned policy) → Action (add/remove/rearrange) 
         → Reward → Update Q-table
```

### ➡️ MULTI-HORIZON MODE
```
Daily (6 AM) → Plan 24-hour schedule
Hourly (:00) → Verify & adjust
Every 5 min  → Tactical 10-min lookahead decisions
```

---

## 🎯 KEY METRICS TRACKED

### Queue Metrics
- Queue depth (current, max, average)
- Queue wait time (min, max, avg)
- Tasks rearranged per spike

### Server Metrics
- Active servers, utilization%, efficiency
- Scale-up/down events
- Server capacity used

### Performance Metrics
- Response time (avg, p99, p95)
- Throughput (tasks/sec)
- SLA violations
- Deadline misses

### RL Metrics
- Episode rewards
- Policy convergence
- Exploration vs exploitation ratio

### Cost Metrics
- Resource hours (servers × hours)
- Cost efficiency (throughput per server)
- Spike handling cost

---

## 📁 FILE ORGANIZATION SUMMARY

```
CAPR_LB/
├── src/
│   ├── core/              [4 files] Basic simulation
│   ├── balancing/         [2 files] Load balancers
│   ├── models/            [2 files] ML predictors
│   ├── policies/          [3 files] Queue management
│   ├── rl/                [3 files] Q-Learning agents
│   ├── orchestration/     [3 files] Decision engines
│   └── utils/             [3 files] Helpers
├── experiments/           [5 files] Testing & validation
├── tests/                 [13 files] Unit/system/perf tests
├── configs/               [1 file] Configuration
├── models/                [Saved ML models]
├── data/                  [Simulation data]
└── results/               [Metrics, plots, reports]

TOTAL: 30 Python files
```

---

**End of Complete Project Reference**  
Generated: April 7, 2026
