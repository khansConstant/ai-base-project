import time
from typing import Dict, Any
import logging
from ..celery_config import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="create_task")
def create_task(a: int, b: int) -> int:
    """Simple example task."""
    print("Task is running...")
    time.sleep(10)
    return a + b