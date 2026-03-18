import random
from configs.simulation_config import SERVICE_TIME

class Server:

    def __init__(self, server_id):
        self.id = server_id
        self.jobs = []

    def process(self, env, event, log_store, agent=None, state=None, action=None, queue=None, servers=None):
        event.start_time = env.now
        self.jobs.append(event)

        yield env.timeout(random.uniform(*SERVICE_TIME))

        event.finish_time = env.now
        self.jobs.remove(event)
        log_store.append(event)
        
        # STEP 3: Calculate reward and update agent
        if agent is not None and state is not None and action is not None:
            response_time = event.finish_time - event.arrival_time
            reward = -response_time  # minimize latency
            
            # Get next state
            queue_len = len(queue) if queue is not None else 0
            loads = [len(s.jobs) for s in servers] if servers is not None else [0]
            imbalance = max(loads) - min(loads) if loads else 0
            next_state = agent.get_state(queue_len, imbalance)
            
            # Update agent
            agent.update(state, action, reward, next_state)