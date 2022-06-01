"""
unit test for app.transport
"""

import unittest

from kombu.transport.SQS import Transport, Channel

from app.transport import RatelimitChannel, ratelimittransport


class TestTransportClass(unittest.TestCase):
    def test_ratelimit_transport(self) -> None:
        self.assertTrue(ratelimittransport.Channel, RatelimitChannel)
        self.assertTrue(issubclass(ratelimittransport, Transport))

    def test_ratelimit_channel(self) -> None:
        self.assertTrue(issubclass(RatelimitChannel, Channel))
