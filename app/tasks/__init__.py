"""
tasks module provides a function to register all tasks to celery app.
"""


def register_tasks() -> None:
    """
    register tasks to the current celery app
    """
    # pylint: disable=import-outside-toplevel,unused-import
    from .function_based_tasks import retry_demo, add
    from .polymorphism import polymorphism_task
