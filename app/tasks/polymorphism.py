"""
tasks.polymorphism contains an example of processing polymorphed event.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Type

from celery import Task, current_app

from app.utils.fluent import FluentLogger

logger = FluentLogger.get_logger("Event")


class EventType(Enum):
    """
    enum class for event types
    """

    PAYMENT = 0
    REFUND = 1


class BaseEvent(ABC):
    """
    Base event class
    """

    def __init__(self, event_id: str) -> None:
        self.event_id = event_id

    @classmethod
    def event_cls(cls, event_type: EventType) -> Optional[Type["BaseEvent"]]:
        """
        get event class given an event type
        """
        cls_map = {
            EventType.PAYMENT: PaymentEvent,
            EventType.REFUND: RefundEvent,
        }
        if event_type not in cls_map:
            raise Exception("event type not found")
        return cls_map.get(event_type)

    @abstractmethod
    def process(self) -> str:
        """
        abstract method
        """
        # pylint: disable=unnecessary-pass
        pass

    def __json__(self) -> dict:
        """
        for json encoding and decoding.
        """
        return {"event_id": self.event_id}


class PaymentEvent(BaseEvent):
    """
    PaymentEvent Type inherited from BaseEvent
    """

    event_type = EventType.PAYMENT

    def process(self) -> str:
        """
        payment specific event processing
        """
        logger.info("processing payment event...")
        print(self.event_id)
        return self.event_id


class RefundEvent(BaseEvent):
    """
    RefundEvent Type inherited from BaseEvent
    """

    event_type = EventType.REFUND

    def process(self) -> str:
        """
        refund specific event processing
        """
        logger.info("processing refund event...")
        print(self.event_id)
        return self.event_id


class PolymorphismTaskClass(Task, ABC):
    """
    A demo task class for polymorphism purpose
    """

    name = "PolymorphismTask"
    serializer = "pickle"


@current_app.task(
    name="polymorphism_task",
)
def polymorphism_task(event: BaseEvent) -> None:
    """
    task execution
    """
    event.process()
