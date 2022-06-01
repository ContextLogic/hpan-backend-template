"""
unit test for app.tasks.function_based_tasks
"""
# pylint: disable=no-value-for-parameter
import unittest

from app.tasks import register_tasks
from app.tasks.function_based_tasks import RetryBaseTask, add, retry_demo


class TestRetryBaseTask(unittest.TestCase):
    task = RetryBaseTask()

    def test_retry_base_task(self) -> None:
        self.assertTrue(isinstance(self.task, RetryBaseTask))
        self.assertEqual(self.task.autoretry_for, (ZeroDivisionError,))
        self.assertEqual(self.task.retry_kwargs, {"max_retries": 3})
        self.assertEqual(self.task.retry_backoff, 1)
        self.assertEqual(self.task.retry_backoff_max, 600)
        self.assertTrue(self.task.retry_jitter)


class TestAdd(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(1, 2), 3)


class TestRetryDemo(unittest.TestCase):
    def test_retry_demo(self) -> None:
        self.assertEqual(retry_demo(1), 1)
        self.assertRaises(ZeroDivisionError, retry_demo, 0)


class TestRegisterTask(unittest.TestCase):
    def test_register_task(self) -> None:
        try:
            register_tasks()
        except Exception:
            self.fail("failed register tasks")
