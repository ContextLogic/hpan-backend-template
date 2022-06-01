from prometheus_client import multiprocess, CollectorRegistry, Counter, Histogram

METRICS_PREFIX = "python_backend_worker_template"

worker_registry = CollectorRegistry()
multiprocess.MultiProcessCollector(worker_registry)

consumer_registry = CollectorRegistry()

WORKER_TASKS_COUNT = Counter('{prefix}_worker_tasks_count'.format(prefix=METRICS_PREFIX),
                            'total count of tasks by name, queue and state, emitted by worker', ('name', 'queue', 'state'),
                            registry=worker_registry)

CONSUMER_TASKS_COUNT = Counter('{prefix}_consumer_tasks_count'.format(prefix=METRICS_PREFIX),
                            'total count of tasks by name, queue and state, emitted by consumer', ('name', 'queue', 'state'),
                            registry=consumer_registry)

TASKS_RUNTIME_SECONDS = Histogram('{prefix}_tasks_runtime_seconds'.format(prefix=METRICS_PREFIX),
                                  'Task runtime (seconds), from prerun to postrun', ('name', 'queue'),
                                buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0),
                                  registry=worker_registry)

TASKS_LATENCY_SECONDS = Histogram('{prefix}_tasks_latency_seconds'.format(prefix=METRICS_PREFIX),
                                  'Task latency (seconds), from received to prerun', ('name', 'queue'),
                                buckets=(.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0),
                                  registry=worker_registry)
