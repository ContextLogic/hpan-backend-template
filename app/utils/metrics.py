"""
utils.metrics initialized two prometheus registry
worker_registry: metrics registry for individual sub worker process
consumer_registry: metrics registry for the main process.

also defines all kinds of metrics.
"""

import logging
import os
from pathlib import Path

from prometheus_client import multiprocess, CollectorRegistry, Counter, Histogram

try:
    dir_path = os.environ["prometheus_multiproc_dir"]
    Path(dir_path).mkdir(exist_ok=True)
except (TypeError, KeyError) as err:
    logging.error("environment variable: prometheus_multiproc_dir is not set")

# metrics prefix, recommended to be the same with your worker name
METRICS_PREFIX = "python_backend_worker_template"

# worker_registry used as multi process registry, any metrics emitted from subprocess should use this registry
worker_registry = CollectorRegistry()
multiprocess.MultiProcessCollector(worker_registry)

# consumer_registry used as the main process registry, any metrics emitted from main app or main process should use this
# registry
consumer_registry = CollectorRegistry()

# metrics definition
WORKER_TASKS_COUNT = Counter(
    f"{METRICS_PREFIX}_worker_tasks_count",
    "total count of tasks by name, queue and state, emitted by worker",
    ("name", "queue", "state"),
    registry=worker_registry,
)

CONSUMER_TASKS_COUNT = Counter(
    f"{METRICS_PREFIX}_consumer_tasks_count",
    "total count of tasks by name, queue and state, emitted by consumer",
    ("name", "queue", "state"),
    registry=consumer_registry,
)

TASKS_RUNTIME_SECONDS = Histogram(
    f"{METRICS_PREFIX}_tasks_runtime_seconds",
    "Task runtime (seconds), from prerun to postrun",
    ("name", "queue"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ),
    registry=worker_registry,
)

TASKS_LATENCY_SECONDS = Histogram(
    f"{METRICS_PREFIX}_tasks_latency_seconds",
    "Task latency (seconds), from received to prerun",
    ("name", "queue"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ),
    registry=worker_registry,
)
