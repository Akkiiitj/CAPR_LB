import pandas as pd
import matplotlib.pyplot as plt

from configs.simulation_config import ARRIVAL_RATES, WEIGHT_SETS, SIM_TIME
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.core.routing_engine import RoutingEngine
from src.core.simulation_environment import SimulationEnvironment

metrics_log = []

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

        metrics_log.append({
            "arrival_rate": rate,
            "weights": str(weights),
            "avg_response": df["response_time"].mean(),
            "throughput": len(df) / SIM_TIME,
            "final_queue_size": len(remaining_queue),
            "crash": crash_flag
        })

results = pd.DataFrame(metrics_log)
results.to_csv("results/final_experiment_results.csv", index=False)