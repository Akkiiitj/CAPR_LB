

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from configs.simulation_config import WEIGHT_SETS, SIM_TIME
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.core.routing_engine import RoutingEngine
from src.core.simulation_environment import SimulationEnvironment
from src.rl.q_learning_agent import QLearningAgent

# 🔥 Borderline + full range
ARRIVAL_RATES = [2, 4, 6, 8, 9, 10, 11, 12]

SYSTEM_MODES = ["baseline", "threshold", "rl"]

metrics_log = []

print("Running experiments...")

for mode in SYSTEM_MODES:
    for rate in ARRIVAL_RATES:
        for weights in WEIGHT_SETS:

            balancer = LeastLoadedBalancer()

            if mode == "baseline":
                rearranger = None
                agent = None

            elif mode == "threshold":
                rearranger = WeightedPriorityRearrangement(weights)
                agent = None

            elif mode == "rl":
                rearranger = WeightedPriorityRearrangement(weights)
                agent = QLearningAgent()

            router = RoutingEngine(
                rearrangement_policy=rearranger,
                balancer=balancer,
                agent=agent,
                mode=mode
            )

            sim = SimulationEnvironment(rate, router)
            logs, remaining_queue, queue_history = sim.run()

            df = pd.DataFrame([vars(e) for e in logs])
            df["response_time"] = df["finish_time"] - df["arrival_time"]

            crash_flag = 1 if len(remaining_queue) > 100 else 0
            p99 = np.percentile(df["response_time"], 99)

            metrics_log.append({
                "system": mode,
                "arrival_rate": rate,
                "weights": str(weights),
                "avg_response": df["response_time"].mean(),
                "p99_response": p99,
                "throughput": len(df) / SIM_TIME,
                "final_queue_size": len(remaining_queue),
                "crash": crash_flag
            })

            print(f"Completed: mode={mode}, arrival_rate={rate}")

results = pd.DataFrame(metrics_log)

os.makedirs("results", exist_ok=True)
results.to_csv("results/final_comparison.csv", index=False)

print("Generating graphs...")

# -------- MAIN COMPARISON GRAPH --------
plt.figure(figsize=(10,6))

for system in results["system"].unique():
    subset = results[results["system"] == system]
    grouped = subset.groupby("arrival_rate")["avg_response"].mean()
    plt.plot(grouped.index, grouped.values, marker='o', label=system)

plt.title("Avg Response Time: Baseline vs Threshold vs RL")
plt.xlabel("Arrival Rate")
plt.ylabel("Avg Response Time")
plt.legend()
plt.grid(True)
plt.savefig("results/comparison_avg_response.png", dpi=300)
#plt.show()

# -------- P99 --------
plt.figure(figsize=(10,6))

for system in results["system"].unique():
    subset = results[results["system"] == system]
    grouped = subset.groupby("arrival_rate")["p99_response"].mean()
    plt.plot(grouped.index, grouped.values, marker='^', linestyle='--', label=system)

plt.title("P99 Latency Comparison")
plt.xlabel("Arrival Rate")
plt.ylabel("P99 Response Time")
plt.legend()
plt.grid(True)
plt.savefig("results/comparison_p99.png", dpi=300)
plt.show()

# -------- QUEUE --------
plt.figure(figsize=(10,6))

for system in results["system"].unique():
    subset = results[results["system"] == system]
    grouped = subset.groupby("arrival_rate")["final_queue_size"].mean()
    plt.plot(grouped.index, grouped.values, marker='s', label=system)

plt.title("Queue Size Comparison")
plt.xlabel("Arrival Rate")
plt.ylabel("Final Queue Size")
plt.legend()
plt.grid(True)
plt.savefig("results/comparison_queue.png", dpi=300)
plt.show()

# -------- BORDERLINE ANALYSIS --------
plt.figure(figsize=(10,6))

border = results[results["arrival_rate"].isin([8,9,10,11])]

for system in border["system"].unique():
    subset = border[border["system"] == system]
    grouped = subset.groupby("arrival_rate")["avg_response"].mean()
    plt.plot(grouped.index, grouped.values, marker='o', label=system)

plt.title("Borderline Behavior Near Threshold")
plt.xlabel("Arrival Rate")
plt.ylabel("Avg Response Time")
plt.legend()
plt.grid(True)
plt.savefig("results/borderline_analysis.png", dpi=300)
plt.show()

print("All experiments completed successfully!")