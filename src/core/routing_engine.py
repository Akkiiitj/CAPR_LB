# import random
# from src.rl.q_learning_agent import QLearningAgent
# from src.utils.load_predictor import LoadPredictor
# from configs.simulation_config import FIXED_THRESHOLD

# class RoutingEngine:

#     def __init__(self, rearrangement_policy, balancer):
#         self.rearrangement_policy = rearrangement_policy
#         self.balancer = balancer
#         self.agent = QLearningAgent()
#         self.load_predictor = LoadPredictor(window=5)
#         self.load_threshold = FIXED_THRESHOLD

#     def run(self, env, queue, servers, log_store):

#         while True:
#             if queue:
#                 # STEP 4: Proactive load prediction
#                 predicted_load = self.load_predictor.predict()

#                 # --- AUTO SCALING POLICY ---
#                 max_servers = 6

#                 if predicted_load > self.load_threshold and len(servers) < max_servers:
#                     from src.core.server import Server
#                     new_server = Server(len(servers))
#                     servers.append(new_server)
#                     print(f"[AUTO SCALE] Added Server {new_server.id} at time {env.now}")
                    
#                 min_servers = 3

#                 if predicted_load < self.load_threshold / 2 and len(servers) > min_servers:
#                     removed = servers.pop()
#                     print(f"[SCALE DOWN] Removed Server {removed.id} at time {env.now}")   
                      
#                 # Rearrange if predicted load is high (proactive)
#                 if self.load_predictor.is_overloaded(self.load_threshold - 2):
#                     self.rearrangement_policy.rearrange(queue, env.now)
#                 else:
#                     # Still update waiting times even if not rearranging
#                     for event in queue:
#                         event.waiting_time = env.now - event.arrival_time

#                 event = queue.pop(0)
                
#                 # Hybrid server selection with QL agent
#                 queue_len = len(queue)
#                 loads = [len(s.jobs) for s in servers]
#                 imbalance = max(loads) - min(loads)
                
#                 state = self.agent.get_state(queue_len, imbalance)
#                 action = self.agent.choose_action(state)
                
#                 if action == 0:
#                     # Action 0: Use least-loaded balancer
#                     server = self.balancer.select_server(servers, event)
#                 else:
#                     # Action 1: Random server selection
#                     server = random.choice(servers)

#                 # STEP 3: Pass agent info to server for reward calculation
#                 env.process(server.process(env, event, log_store, 
#                                           agent=self.agent, 
#                                           state=state, 
#                                           action=action, 
#                                           queue=queue, 
#                                           servers=servers))
                
#                 # Update load history for prediction
#                 self.load_predictor.add_measurement(queue_len)

#             yield env.timeout(0.1)
import random
from src.rl.q_learning_agent import QLearningAgent
from src.utils.load_predictor import LoadPredictor
from configs.simulation_config import FIXED_THRESHOLD


class RoutingEngine:

    def __init__(self, rearrangement_policy, balancer, agent=None, mode="baseline"):
        self.rearrangement_policy = rearrangement_policy
        self.balancer = balancer
        self.mode = mode

        # RL agent only if needed
        if mode == "rl":
            self.agent = agent if agent else QLearningAgent()
        else:
            self.agent = None

        self.load_predictor = LoadPredictor(window=5)
        self.load_threshold = FIXED_THRESHOLD

    def run(self, env, queue, servers, log_store):

        # 🔥 ADD THESE (persistent across loop)
        if not hasattr(self, "last_scale_time"):
            self.last_scale_time = 0

        cooldown = 2.0   # time units (adjust if needed)

        # Hysteresis thresholds
        scale_up_threshold = self.load_threshold
        scale_down_threshold = self.load_threshold * 0.6

        max_servers = 6
        min_servers = 3

        while True:
            if queue:

                # -------- LOAD PREDICTION --------
                predicted_load = self.load_predictor.predict()

                # -------- AUTO SCALING (FIXED) --------
                if env.now - self.last_scale_time > cooldown:

                    # SCALE UP
                    if predicted_load > scale_up_threshold and len(servers) < max_servers:
                        from src.core.server import Server
                        new_server = Server(len(servers))
                        servers.append(new_server)
                        self.last_scale_time = env.now
                        print(f"[AUTO SCALE] Added Server {new_server.id} at time {env.now}")

                    # SCALE DOWN
                    elif predicted_load < scale_down_threshold and len(servers) > min_servers:
                        removed = servers.pop()
                        self.last_scale_time = env.now
                        print(f"[SCALE DOWN] Removed Server {removed.id} at time {env.now}")

                # -------- QUEUE HANDLING --------
                if self.mode in ["threshold", "rl"] and self.rearrangement_policy:
                    if self.load_predictor.is_overloaded(self.load_threshold - 2):
                        self.rearrangement_policy.rearrange(queue, env.now)
                    else:
                        for event in queue:
                            event.waiting_time = env.now - event.arrival_time
                else:
                    for event in queue:
                        event.waiting_time = env.now - event.arrival_time

                # -------- FETCH EVENT --------
                event = queue.pop(0)

                # -------- SERVER SELECTION --------
                if self.mode == "baseline":
                    server = self.balancer.select_server(servers, event)
                    state, action = None, None

                elif self.mode == "threshold":
                    server = self.balancer.select_server(servers, event)
                    state, action = None, None

                elif self.mode == "rl":
                    queue_len = len(queue)
                    loads = [len(s.jobs) for s in servers]
                    imbalance = max(loads) - min(loads)

                    state = self.agent.get_state(queue_len, imbalance)
                    action = self.agent.choose_action(state)

                    if action == 0:
                        server = self.balancer.select_server(servers, event)
                    else:
                        server = random.choice(servers)

                # -------- PROCESS --------
                env.process(server.process(
                    env,
                    event,
                    log_store,
                    agent=self.agent if self.mode == "rl" else None,
                    state=state if self.mode == "rl" else None,
                    action=action if self.mode == "rl" else None,
                    queue=queue,
                    servers=servers
                ))

                # -------- UPDATE LOAD HISTORY --------
                self.load_predictor.add_measurement(len(queue))

            # 🔥 Less aggressive stepping (IMPORTANT)
            yield env.timeout(0.5)