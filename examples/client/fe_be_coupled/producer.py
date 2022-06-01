from celery import Celery

from app.tasks.polymorphism import BaseEvent, EventType

celery_app = Celery()
celery_app.config_from_object("worker_config")

PaymentEventCls = BaseEvent.event_cls(EventType.PAYMENT)
RefundEventCls = BaseEvent.event_cls(EventType.REFUND)

event1 = PaymentEventCls("id_payment")  # type: ignore[misc]
event2 = RefundEventCls("id_refund")  # type: ignore[misc]
for i in range(0, 10):
    celery_app.send_task("polymorphism_task", args=(event1,), serializer="pickle")
    celery_app.send_task("polymorphism_task", args=(event2,), serializer="pickle")
