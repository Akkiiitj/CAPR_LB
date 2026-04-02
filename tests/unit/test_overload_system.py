from experiments.run_experiments import ARRIVAL_RATES
from src.core.simulation_environment import SimulationEnvironment
from src.core.routing_engine import RoutingEngine
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement


def test_system_under_high_load():

    weights = {
        "deadline":0.4,
        "exec":0.2,
        "wait":0.2,
        "resource":0.1,
        "business":0.1
    }

    rearranger = WeightedPriorityRearrangement(weights)
    balancer = LeastLoadedBalancer()

    router = RoutingEngine(rearranger, balancer)

    sim = SimulationEnvironment(arrival_rate=10, routing_engine=router)

    logs, queue = sim.run()

    assert len(logs) > 0