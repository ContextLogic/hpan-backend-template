from prometheus_client import Gauge
from prometheus_client import Counter
from prometheus_client import Histogram

METRIC_PREFIX = "python_backend_worker_template"

class PrometheusMetric(object):

    @classmethod
    def _base_name(cls):
        return cls.METRICS_NAME

    @classmethod
    def _fix_metric_name(cls, metric_name):
        """
        Args:
            metric_name (string): metric name
        Returns:
            string: metric name where space and dash char are replaced
        """
        metric_name = metric_name.replace(" ", "_")
        metric_name = metric_name.replace("-", "_")
        return "_" + metric_name

    @classmethod
    def _build_metric_name(cls, metric_name):
        if not metric_name:
            raise RuntimeError("metric_name cannot be empty")

        fixed_metric_name = cls._fix_metric_name(metric_name)
        result = cls._base_name() + fixed_metric_name
        return result

    @classmethod
    def counter_inc(cls, metric_name, doc, label_dict=None, value=1):
        metric = cls._build_metric_name(metric_name)
        if label_dict:
            label_list = label_dict.keys()
            counter = Counter(metric, doc, labelnames=label_list, labelvalues=label_dict.values())
        else:
            counter = Counter(metric, doc)
        counter.inc(value)

    @classmethod
    def gauge_set(cls, metric_name, doc, label_dict=None, value=1):
        metric = cls._build_metric_name(metric_name)
        if label_dict:
            label_list = label_dict.keys()
            gauge = Gauge(metric, doc, labelnames=label_list, labelvalues=label_dict.values())
        else:
            gauge = Gauge(metric, doc)
        gauge.set(value)

    @classmethod
    def histogram_observe(cls, metric_name, doc, label_dict=None, val=1.0, buckets_tuple=None):
        metric = cls._build_metric_name(metric_name)
        if label_dict is not None:
            label_list = list(label_dict.keys())
            if buckets_tuple is None:
                hist = Histogram(
                    metric,
                    doc,
                    labelnames=label_list,
                    labelvalues=label_dict.values(),
                )
            else:
                hist = Histogram(
                    metric,
                    doc,
                    labelnames=label_list,
                    labelvalues=label_dict.values(),
                    buckets=buckets_tuple,
                )
        else:
            if buckets_tuple is None:
                hist = Histogram(metric, doc)
            else:
                hist = Histogram(metric, doc, buckets=buckets_tuple)
        hist.observe(val)


