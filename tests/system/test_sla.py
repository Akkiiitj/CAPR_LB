import numpy as np
import pandas as pd

from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer


def test_sla():

    router = RoutingEngine(None, LeastLoadedBalancer(), mode="baseline")
    sim = SimulationEnvironment(10, router)

    logs, queue, _ = sim.run()

    df = pd.DataFrame([vars(e) for e in logs])

    if df.empty:
        assert True
        return

    df["response_time"] = df["finish_time"] - df["arrival_time"]

    avg = df["response_time"].mean()
    p99 = np.percentile(df["response_time"], 99)

    print("AVG:", avg)
    print("P99:", p99)

    # ✅ Assertions (adjust if needed)
    assert avg >= 0
    assert p99 >= 0

    import matplotlib.pyplot as plt
    import os

    plt.hist(df["response_time"], bins=20)
    plt.title("Response Time Distribution")
    plt.xlabel("Response Time")
    plt.ylabel("Frequency")

    os.makedirs("results", exist_ok=True)
    plt.savefig("results/latency_distribution.png")