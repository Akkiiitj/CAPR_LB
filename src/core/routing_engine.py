import random
from src.rl.q_learning_agent import QLearningAgent
from src.utils.load_predictor import LoadPredictor
from configs.simulation_config import FIXED_THRESHOLD

class RoutingEngine:

    def __init__(self, rearrangement_policy, balancer):
        self.rearrangement_policy = rearrangement_policy
        self.balancer = balancer
        self.agent = QLearningAgent()
        self.load_predictor = LoadPredictor(window=5)
        self.load_threshold = FIXED_THRESHOLD

    def run(self, env, queue, servers, log_store):

        while True:
            if queue:
                # STEP 4: Proactive load prediction
                predicted_load = self.load_predictor.predict()
                
                # Rearrange if predicted load is high (proactive)
                if self.load_predictor.is_overloaded(self.load_threshold - 2):
                    self.rearrangement_policy.rearrange(queue, env.now)
                else:
                    # Still update waiting times even if not rearranging
                    for event in queue:
                        event.waiting_time = env.now - event.arrival_time

                event = queue.pop(0)
                
                # Hybrid server selection with QL agent
                queue_len = len(queue)
                loads = [len(s.jobs) for s in servers]
                imbalance = max(loads) - min(loads)
                
                state = self.agent.get_state(queue_len, imbalance)
                action = self.agent.choose_action(state)
                
                if action == 0:
                    # Action 0: Use least-loaded balancer
                    server = self.balancer.select_server(servers, event)
                else:
                    # Action 1: Random server selection
                    server = random.choice(servers)

                # STEP 3: Pass agent info to server for reward calculation
                env.process(server.process(env, event, log_store, 
                                          agent=self.agent, 
                                          state=state, 
                                          action=action, 
                                          queue=queue, 
                                          servers=servers))
                
                # Update load history for prediction
                self.load_predictor.add_measurement(queue_len)

            yield env.timeout(0.1)