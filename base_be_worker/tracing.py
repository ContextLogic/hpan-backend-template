"""
provides a function to create a tracer and set the global tracer in opentracing
"""

from typing import Optional

from jaeger_client import Config as JaegerConfig, Tracer


class TracerFactory:
    """
    Tracer Factory class to create new tracer for each sub process
    """
    jaeger_config = JaegerConfig(
        config={},
        service_name="default",
        validate=True,
    )

    @classmethod
    def init(cls, jaeger_config: JaegerConfig) -> None:
        """
        init the Tracer Factory with given jaeger config
        """
        cls.jaeger_config = jaeger_config

    @classmethod
    def get_tracer(cls) -> Optional[Tracer]:
        """
        initialize the jaeger tracer and set to the opentracing global tracers.
        """
        return cls.jaeger_config.initialize_tracer()
