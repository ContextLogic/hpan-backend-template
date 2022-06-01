"""
unit test for app.tasks.polymorphism
"""
# pylint: disable=abstract-class-instantiated
import unittest

from app.tasks.polymorphism import EventType, BaseEvent, PaymentEvent, RefundEvent


class TestEventType(unittest.TestCase):
    def test_event_type(self) -> None:
        self.assertTrue(EventType.PAYMENT.value == 0)
        self.assertTrue(EventType.REFUND.value == 1)


class TestBaseEvent(unittest.TestCase):
    def test_base_event(self) -> None:
        payment_cls = BaseEvent.event_cls(EventType.PAYMENT)
        self.assertEqual(payment_cls, PaymentEvent)

        refund_cls = BaseEvent.event_cls(EventType.REFUND)
        self.assertEqual(refund_cls, RefundEvent)

        self.assertRaises(Exception, BaseEvent.event_cls, "something else")

    def test_abstract_class(self) -> None:
        try:
            BaseEvent("test").process()  # type: ignore[abstract]
        except TypeError:
            pass
        else:
            self.fail("abstract class should not be instantiated")

    def test_event_json(self) -> None:
        payment_event = PaymentEvent("payment_id")
        self.assertEqual(payment_event.__json__(), {"event_id": "payment_id"})

        refund_event = PaymentEvent("refund_id")
        self.assertEqual(refund_event.__json__(), {"event_id": "refund_id"})


class TestPaymentEvent(unittest.TestCase):
    payment_event = PaymentEvent("payment_id")

    def test_payment_type(self) -> None:
        self.assertEqual(self.payment_event.event_type, EventType.PAYMENT)

    def test_payment_process(self) -> None:
        self.assertEqual(self.payment_event.process(), "payment_id")


class TestRefundEvent(unittest.TestCase):
    refund_event = RefundEvent("refund_id")

    def test_payment_type(self) -> None:
        self.assertEqual(self.refund_event.event_type, EventType.REFUND)

    def test_payment_process(self) -> None:
        self.assertEqual(self.refund_event.process(), "refund_id")
