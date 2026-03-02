NUM_SERVERS = 3
SERVICE_TIME = (2, 5)
SIM_TIME = 200
FIXED_THRESHOLD = 10

ARRIVAL_RATES = [2, 4, 6, 8, 10, 12]

WEIGHT_SETS = [
    {"deadline":0.5, "exec":0.2, "wait":0.1, "resource":0.1, "business":0.1},
    {"deadline":0.3, "exec":0.3, "wait":0.2, "resource":0.1, "business":0.1},
    {"deadline":0.25, "exec":0.25, "wait":0.25, "resource":0.15, "business":0.10},
    {"deadline":0.2, "exec":0.35, "wait":0.2, "resource":0.15, "business":0.10},
]