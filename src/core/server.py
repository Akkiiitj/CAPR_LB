import random
from configs.simulation_config import SERVICE_TIME

class Server:

    def __init__(self, server_id):
        self.id = server_id
        self.jobs = []

    def process(self, env, event, log_store):
        event.start_time = env.now
        self.jobs.append(event)

        yield env.timeout(random.uniform(*SERVICE_TIME))

        event.finish_time = env.now
        self.jobs.remove(event)
        log_store.append(event)