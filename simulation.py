import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
NUM_SERVERS = 3
SERVICE_TIME = (2, 5)
SIM_TIME = 200
FIXED_THRESHOLD = 10

ARRIVAL_RATES = [2,4,6,8,10,12]

WEIGHT_SETS = [
    {"deadline":0.5, "exec":0.2, "wait":0.1, "resource":0.1, "business":0.1},
    {"deadline":0.3, "exec":0.3, "wait":0.2, "resource":0.1, "business":0.1},
    {"deadline":0.25, "exec":0.25, "wait":0.25, "resource":0.15, "business":0.10},
    {"deadline":0.2, "exec":0.35, "wait":0.2, "resource":0.15, "business":0.10},
]

metrics_log = []

# -----------------------------
# EVENT PRODUCER
# -----------------------------
def event_producer(env, queue, arrival_rate):
    i = 0
    while True:
        yield env.timeout(random.expovariate(arrival_rate))
        request = {
            "id": i,
            "arrival_time": env.now,
            "deadline_remaining": random.uniform(1,10),
            "estimated_execution_time": random.uniform(1,5),
            "waiting_time": 0,
            "resource_requirement": random.uniform(0.1,1),
            "business_priority_level": random.uniform(0,1)
        }
        queue.append(request)
        i += 1

# -----------------------------
# PRIORITY
# -----------------------------
def compute_priority(event, w):
    return (
        w["deadline"]*(1/event["deadline_remaining"])
        + w["exec"]*event["estimated_execution_time"]
        + w["wait"]*event["waiting_time"]
        + w["resource"]*event["resource_requirement"]
        + w["business"]*event["business_priority_level"]
    )

# -----------------------------
# ROUTER
# -----------------------------
def routing_engine(env, queue, servers, weights):
    while True:
        if len(queue) > 0:

            for r in queue:
                r["waiting_time"] = env.now - r["arrival_time"]

            if len(queue) >= FIXED_THRESHOLD:
                queue.sort(key=lambda x: compute_priority(x, weights), reverse=True)

            request = queue.pop(0)
            server = min(servers, key=lambda s: len(s["jobs"]))
            env.process(server_process(env, request, server))

        yield env.timeout(0.1)

# -----------------------------
# SERVER
# -----------------------------
def server_process(env, request, server):
    request["start_time"] = env.now
    server["jobs"].append(request)

    yield env.timeout(random.uniform(*SERVICE_TIME))

    request["finish_time"] = env.now
    server["jobs"].remove(request)
    logs.append(request)

# -----------------------------
# RUN
# -----------------------------
def run(arrival_rate, weights):

    global logs
    logs = []

    env = simpy.Environment()
    queue = []
    servers = [{"id":i,"jobs":[]} for i in range(NUM_SERVERS)]

    env.process(event_producer(env, queue, arrival_rate))
    env.process(routing_engine(env, queue, servers, weights))
    env.run(until=SIM_TIME)

    df = pd.DataFrame(logs)
    df["response_time"] = df["finish_time"] - df["arrival_time"]

    crash_flag = 1 if len(queue) > 100 else 0   # queue explosion detection

    metrics_log.append({
        "arrival_rate":arrival_rate,
        "weights":str(weights),
        "avg_response":df["response_time"].mean(),
        "throughput":len(df)/SIM_TIME,
        "final_queue_size":len(queue),
        "crash":crash_flag
    })

# -----------------------------
# EXPERIMENT LOOP
# -----------------------------
for rate in ARRIVAL_RATES:
    for w in WEIGHT_SETS:
        run(rate, w)

results = pd.DataFrame(metrics_log)
results.to_csv("final_experiment_results.csv", index=False)

# -----------------------------
# GRAPH 1: Arrival rate vs Response
# -----------------------------
plt.figure()

for w in results["weights"].unique():
    subset = results[results["weights"]==w]
    plt.plot(subset["arrival_rate"], subset["avg_response"], label=w)

plt.xlabel("Arrival Rate")
plt.ylabel("Average Response Time")
plt.legend()
plt.show()

# -----------------------------
# GRAPH 2: Crash detection graph
# -----------------------------
plt.figure()

for w in results["weights"].unique():
    subset = results[results["weights"]==w]
    plt.plot(subset["arrival_rate"], subset["final_queue_size"], label=w)

plt.xlabel("Arrival Rate")
plt.ylabel("Queue Size (Crash indicator)")
plt.legend()
plt.show()
