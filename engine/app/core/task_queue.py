"""
task_queue.py — Celery application singleton for FluxKernel async task dispatch.

Workers are started separately via:
    celery -A app.core.task_queue.celery_app worker --loglevel=info

The broker and result backend both default to localhost Redis but are
overridable via CELERY_BROKER_URL / CELERY_RESULT_BACKEND in the environment.
"""

import os
from typing import Any

try:
    from celery import Celery

    HAS_CELERY = True
except ImportError:
    Celery = None
    HAS_CELERY = False

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

if HAS_CELERY and Celery is not None:
    celery_app = Celery(
        "fluxkernel",
        broker=BROKER_URL,
        backend=RESULT_BACKEND,
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        # Tasks results expire after 1 hour to keep Redis lean
        result_expires=3600,
        # Prevent tasks from running forever
        task_time_limit=600,  # hard kill at 10 min
        task_soft_time_limit=540,  # SIGTERM at 9 min (allows cleanup)
        # Auto-discover tasks in the tools package
        imports=["app.tools.code_executor"],
    )
else:

    class _MockTaskResult:
        id = "mock-task-id"
        state = "SUCCESS"
        result: dict[str, Any] = {}

    class _MockTask:
        def __init__(self, func: Any):
            self.func = func

        def apply_async(self, args: Any = None, kwargs: Any = None) -> _MockTaskResult:
            return _MockTaskResult()

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self.func(*args, **kwargs)

    class _MockCelery:
        conf: dict[str, Any] = {}

        def task(self, *args: Any, **kwargs: Any) -> Any:
            def decorator(func: Any) -> _MockTask:
                return _MockTask(func)

            return decorator

    celery_app = _MockCelery()  # type: ignore
