"""
provides a function to create a tracer and set the global tracer in opentracing
"""

from jaeger_client import Config as JaegerConfig, Tracer

from app.config import CONF


def new_tracer() -> Tracer:
    """
    create a jaeger tracer
    """
    jcfg = JaegerConfig(
        config={
            "sampler": {
                "type": CONF.jaeger_sampler_type,
                "param": 1,
            },
        },
        service_name=CONF.name,
        validate=True,
    )

    tracer = jcfg.initialize_tracer()
    return tracer
