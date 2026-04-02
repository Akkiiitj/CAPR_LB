import simpy

from src.core.server import Server
from src.core.routing_engine import RoutingEngine
from src.policies.weighted_priority_rearrangement import WeightedPriorityRearrangement
from src.balancing.least_loaded_balancer import LeastLoadedBalancer
from src.core.event import Event


def test_routing_engine_basic():

    env = simpy.Environment()

    queue = []
    log_store = []

    servers = [Server(0), Server(1)]

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

    queue.append(Event(1,0,5,2,0.2,0.3))

    env.process(router.run(env, queue, servers, log_store))

    env.run(until=20)

    assert len(log_store) >= 1