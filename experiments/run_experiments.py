import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from configs.simulation_config import ARRIVAL_RATES, WEIGHT_SETS, SIM_TIME
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.core.routing_engine import RoutingEngine
from src.core.simulation_environment import SimulationEnvironment

metrics_log = []

print("Running experiments...")
for rate in ARRIVAL_RATES:
    for weights in WEIGHT_SETS:

        rearranger = WeightedPriorityRearrangement(weights)
        balancer = LeastLoadedBalancer()
        router = RoutingEngine(rearranger, balancer)

        sim = SimulationEnvironment(rate, router)
        logs, remaining_queue = sim.run()

        df = pd.DataFrame([vars(e) for e in logs])
        df["response_time"] = df["finish_time"] - df["arrival_time"]

        crash_flag = 1 if len(remaining_queue) > 100 else 0
        p99 = np.percentile(df["response_time"], 99)

        metrics_log.append({
            "arrival_rate": rate,
            "weights": str(weights),
            "avg_response": df["response_time"].mean(),
            "p99_response": p99,
            "throughput": len(df) / SIM_TIME,
            "final_queue_size": len(remaining_queue),
            "crash": crash_flag
        })
        
        print(f"Completed: arrival_rate={rate}, weights={weights}")

results = pd.DataFrame(metrics_log)
results.to_csv("results/final_experiment_results.csv", index=False)
print("Results saved to results/final_experiment_results.csv")

# Generate graphs
print("Generating graphs...")

# Create results directory if it doesn't exist
os.makedirs("results", exist_ok=True)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Simulation Performance Metrics", fontsize=16)

# Graph 1: Average Response Time vs Arrival Rate
avg_response_by_rate = results.groupby("arrival_rate")["avg_response"].mean()
axes[0, 0].plot(avg_response_by_rate.index, avg_response_by_rate.values, marker='o', linewidth=2, label='Mean')
p99_response_by_rate = results.groupby("arrival_rate")["p99_response"].mean()
axes[0, 0].plot(p99_response_by_rate.index, p99_response_by_rate.values, marker='^', linewidth=2, linestyle='--', label='P99')
axes[0, 0].set_xlabel("Arrival Rate")
axes[0, 0].set_ylabel("Response Time")
axes[0, 0].set_title("Average vs P99 Response Time vs Arrival Rate")
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Graph 2: Throughput vs Arrival Rate
throughput_by_rate = results.groupby("arrival_rate")["throughput"].mean()
axes[0, 1].plot(throughput_by_rate.index, throughput_by_rate.values, marker='s', color='green', linewidth=2)
axes[0, 1].set_xlabel("Arrival Rate")
axes[0, 1].set_ylabel("Throughput (requests/time unit)")
axes[0, 1].set_title("Throughput vs Arrival Rate")
axes[0, 1].grid(True, alpha=0.3)

# Graph 3: Final Queue Size vs Arrival Rate
queue_size_by_rate = results.groupby("arrival_rate")["final_queue_size"].mean()
axes[1, 0].bar(queue_size_by_rate.index, queue_size_by_rate.values, color='orange', alpha=0.7)
axes[1, 0].set_xlabel("Arrival Rate")
axes[1, 0].set_ylabel("Final Queue Size")
axes[1, 0].set_title("Final Queue Size vs Arrival Rate")
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Graph 4: Crash Rate vs Arrival Rate
crash_rate_by_rate = results.groupby("arrival_rate")["crash"].mean() * 100
axes[1, 1].bar(crash_rate_by_rate.index, crash_rate_by_rate.values, color='red', alpha=0.7)
axes[1, 1].set_xlabel("Arrival Rate")
axes[1, 1].set_ylabel("Crash Rate (%)")
axes[1, 1].set_title("Crash Rate vs Arrival Rate")
axes[1, 1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("results/performance_metrics.png", dpi=300, bbox_inches='tight')
print("Graph saved to results/performance_metrics.png")

# Additional detailed graph: Response time by weight configuration
fig2, ax = plt.subplots(figsize=(12, 6))
weight_groups = results.groupby("weights")["avg_response"].mean().sort_values(ascending=False)
ax.barh(range(len(weight_groups)), weight_groups.values, color='steelblue', alpha=0.8)
ax.set_yticks(range(len(weight_groups)))
ax.set_yticklabels([w[:50] + "..." if len(w) > 50 else w for w in weight_groups.index], fontsize=9)
ax.set_xlabel("Average Response Time")
ax.set_title("Average Response Time by Weight Configuration")
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig("results/response_time_by_weights.png", dpi=300, bbox_inches='tight')
print("Graph saved to results/response_time_by_weights.png")

print("All experiments completed successfully!")
print(f"P99 Response Time added to metrics!")
print("\nFirst few results:")
print(results.head())