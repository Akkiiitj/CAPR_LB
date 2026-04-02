import pandas as pd
import numpy as np


# -------- BASIC METRICS --------

def compute_response_times(logs):
    df = pd.DataFrame([vars(e) for e in logs])

    if df.empty:
        return df

    df["response_time"] = df["finish_time"] - df["arrival_time"]
    return df


def avg_response_time(logs):
    df = compute_response_times(logs)
    return df["response_time"].mean() if not df.empty else 0


def p99_response_time(logs):
    df = compute_response_times(logs)
    return np.percentile(df["response_time"], 99) if not df.empty else 0


def throughput(logs, sim_time):
    return len(logs) / sim_time if sim_time > 0 else 0


# -------- QUEUE METRICS --------

def max_queue_size(queue_history):
    return max(queue_history) if queue_history else 0


def avg_queue_size(queue_history):
    return sum(queue_history) / len(queue_history) if queue_history else 0


def is_unstable(queue_history, threshold=200):
    return max_queue_size(queue_history) > threshold


# -------- SLA / NFR CHECKS --------

def check_sla(logs, queue_history,
              max_avg=50,
              max_p99=100,
              max_queue=100):

    avg = avg_response_time(logs)
    p99 = p99_response_time(logs)
    max_q = max_queue_size(queue_history)

    return {
        "avg_ok": avg < max_avg,
        "p99_ok": p99 < max_p99,
        "queue_ok": max_q < max_queue,
        "avg": avg,
        "p99": p99,
        "max_queue": max_q
    }


# -------- TASK CONSISTENCY --------

def check_task_loss(total_created, logs, remaining_queue):
    processed = len(logs)
    remaining = len(remaining_queue)

    return total_created == processed + remaining


# -------- PRIORITY VALIDATION --------

def count_priority_violations(logs, threshold=50):
    violations = 0

    for e in logs:
        if hasattr(e, "business") and e.business > 0.8:
            response_time = e.finish_time - e.arrival_time
            if response_time > threshold:
                violations += 1

    return violations


# -------- RL METRICS --------

def q_table_size(agent):
    return len(agent.q_table)


def q_value_variance(agent):
    values = []

    for state in agent.q_table:
        values.extend(agent.q_table[state])

    return np.var(values) if values else 0