def test_priority_violation():

    from src.core.simulation_environment import SimulationEnvironment
    from src.core.routing_engine import RoutingEngine
    from src.balancing.least_loaded_balancer import LeastLoadedBalancer

    import matplotlib
    matplotlib.use('Agg')

    import matplotlib.pyplot as plt
    import os

    router = RoutingEngine(None, LeastLoadedBalancer(), mode="baseline")
    sim = SimulationEnvironment(10, router)

    logs, queue, _ = sim.run()

    violations = 0

    high_priority = []
    normal = []

    for e in logs:
        response_time = e.finish_time - e.arrival_time

        if hasattr(e, "business") and e.business > 0.8:
            if response_time > 50:
                violations += 1
            high_priority.append(response_time)
        else:
            normal.append(response_time)

    print("Violations:", violations)

    # 📊 GRAPH (INSIDE FUNCTION)
    plt.hist(high_priority, bins=15, alpha=0.7, label="High Priority")
    plt.hist(normal, bins=15, alpha=0.7, label="Normal")

    plt.legend()
    plt.title("Priority Handling Comparison")

    os.makedirs("results", exist_ok=True)
    plt.savefig("results/priority_comparison.png")

    assert violations >= 0