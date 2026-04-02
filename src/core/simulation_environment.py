import simpy
import random
from src.core.event import Event
from src.core.server import Server
from configs.simulation_config import NUM_SERVERS, SIM_TIME

class SimulationEnvironment:

    def __init__(self, arrival_rate, routing_engine):
        self.arrival_rate = arrival_rate
        self.routing_engine = routing_engine
        self.logs = []

    def event_producer(self, env, queue):
        i = 0
        MAX_EVENTS = 200
        while True:
            yield env.timeout(random.expovariate(self.arrival_rate))

            event = Event(
                event_id=i,
                arrival_time=env.now,
                deadline=random.uniform(1,10),
                exec_time=random.uniform(1,5),
                resource=random.uniform(0.1,1),
                business=random.uniform(0,1)
            )

            queue.append(event)
            i += 1

    def run(self):

        env = simpy.Environment()
        queue = []
        servers = [Server(i) for i in range(NUM_SERVERS)]

        queue_history = []   # 🔥 NEW

        env.process(self.event_producer(env, queue))
        env.process(self.routing_engine.run(env, queue, servers, self.logs))

        while env.now < SIM_TIME:
            queue_history.append(len(queue))   # 🔥 TRACK QUEUE
            env.step()

        return self.logs, queue, queue_history   # 🔥 RETURN 3 VALUES