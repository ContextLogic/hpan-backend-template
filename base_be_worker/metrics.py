"""
metrics module initializes two prometheus registry
worker_registry: metrics registry for individual sub worker process
consumer_registry: metrics registry for the main process.

also defines all kinds of metrics.
"""

import logging
import os
from pathlib import Path

from prometheus_client import multiprocess, CollectorRegistry, Counter, Histogram, Gauge


class PrometheusMetrics:
    """
    singleton class with some default metrics
    """

    # metrics prefix, recommended to be the same with your worker name
    METRICS_PREFIX = "default"

    # worker_registry used as multi process registry,
    # any metrics emitted from subprocess should use this registry
    WORKER_REGISTRY = CollectorRegistry()

    # consumer_registry used as the main process registry,
    # any metrics emitted from main app or main process should use this registry
    CONSUMER_REGISTRY = CollectorRegistry()

    # default metrics definition
    WORKER_TASKS_COUNT = None
    CONSUMER_TASKS_COUNT = None
    TASKS_RUNTIME_SECONDS = None
    TASKS_LATENCY_SECONDS = None

    @classmethod
    def _build_metric_name(cls, metric_name: str) -> str:
        """
        prepend metrics prefix to the given metric name,
        replace " " and "-" to "_" in the name, this validate the
        prometheus metric name.
        """
        return f"{cls.METRICS_PREFIX}_{metric_name}".replace("-", "_").replace(" ", "_")

    @classmethod
    def init(cls, **kwargs: dict) -> None:
        """
        initialize the prom metrics singleton

        keyword args: metrics_prefix, task_runtime_bucket, tasks_latency_bucket
        """
        cls.METRICS_PREFIX = kwargs.get(
            "metrics_prefix", cls.METRICS_PREFIX  # type: ignore[assignment]
        )
        cls.WORKER_TASKS_COUNT = Counter(
            cls._build_metric_name("worker_tasks_count"),
            "total count of tasks by name, queue and state, emitted by worker",
            ("name", "queue", "state"),
            registry=cls.WORKER_REGISTRY,
        )
        cls.CONSUMER_TASKS_COUNT = Counter(
            cls._build_metric_name("consumer_tasks_count"),
            "total count of tasks by name, queue and state, emitted by consumer",
            ("name", "queue", "state"),
            registry=cls.CONSUMER_REGISTRY,
        )
        cls.TASKS_RUNTIME_SECONDS = Histogram(
            cls._build_metric_name("tasks_runtime_seconds"),
            "Task runtime (seconds), from prerun to postrun",
            ("name", "queue"),
            buckets=kwargs.get(
                "task_runtime_bucket",
                (
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
            ),
            registry=cls.WORKER_REGISTRY,
        )
        cls.TASKS_LATENCY_SECONDS = Histogram(
            cls._build_metric_name("tasks_latency_seconds"),
            "Task latency (seconds), from received to prerun",
            ("name", "queue"),
            buckets=kwargs.get(
                "tasks_latency_bucket",
                (
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
            ),
            registry=cls.WORKER_REGISTRY,
        )

        try:
            dir_path = os.environ["prometheus_multiproc_dir"]
            Path(dir_path).mkdir(exist_ok=True)
            multiprocess.MultiProcessCollector(cls.WORKER_REGISTRY)
        except (TypeError, KeyError) as err:
            raise Exception("environment variable: "
                            "prometheus_multiproc_dir is not set") from err

    @classmethod
    # pylint: disable=too-many-arguments
    def counter_inc(
        cls,
        metric_name: str,
        doc: str,
        label_dict: dict = None,
        value: int = 1,
        registry: CollectorRegistry = None,
    ) -> None:
        """
        counter metrics
        """
        if not registry:
            registry = CollectorRegistry(auto_describe=True)

        metric = cls._build_metric_name(metric_name)
        counter = None
        if label_dict:
            label_list = label_dict.keys()
            counter = Counter(
                metric,
                doc,
                labelnames=label_list,
                labelvalues=label_dict.values(),
                registry=registry,
            )
        else:
            counter = Counter(metric, doc, registry=registry)
        counter.inc(value)

    @classmethod
    # pylint: disable=too-many-arguments
    def gauge_set(
        cls,
        metric_name: str,
        doc: str,
        label_dict: dict = None,
        value: int = 1,
        registry: CollectorRegistry = None,
    ) -> None:
        """
        gauge metric
        """
        if not registry:
            registry = CollectorRegistry(auto_describe=True)

        metric = cls._build_metric_name(metric_name)
        gauge = None
        if label_dict:
            label_list = label_dict.keys()
            gauge = Gauge(
                metric,
                doc,
                labelnames=label_list,
                labelvalues=label_dict.values(),
                registry=registry,
            )
        else:
            gauge = Gauge(metric, doc, registry=registry)
        gauge.set(value)

    @classmethod
    # pylint: disable=too-many-arguments
    def histogram_observe(
        cls,
        metric_name: str,
        doc: str,
        label_dict: dict = None,
        val: float = 1.0,
        buckets_tuple: tuple = None,
        registry: CollectorRegistry = None,
    ) -> None:
        """
        histogram metrics
        """
        if not registry:
            registry = cls.WORKER_REGISTRY

        metric = cls._build_metric_name(metric_name)
        hist = None
        if label_dict is not None:
            label_list = list(label_dict.keys())
            if buckets_tuple is None:
                hist = Histogram(
                    metric,
                    doc,
                    labelnames=label_list,
                    labelvalues=label_dict.values(),
                    registry=registry,
                )
            else:
                hist = Histogram(
                    metric,
                    doc,
                    labelnames=label_list,
                    labelvalues=label_dict.values(),
                    buckets=buckets_tuple,
                    registry=registry,
                )
        else:
            if buckets_tuple is None:
                hist = Histogram(metric, doc, registry=registry)
            else:
                hist = Histogram(metric, doc, buckets=buckets_tuple, registry=registry)
        hist.observe(val)
