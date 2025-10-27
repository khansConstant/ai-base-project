import time
import logging
from ..celery_config import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="example_task")
def example_task(a: int, b: int) -> int:
    """
    Example Celery task that adds two numbers.
    Replace this with your own background task logic.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of a and b
    """
    logger.info(f"Example task started with a={a}, b={b}")
    
    # Simulate some work
    time.sleep(2)
    result = a + b
    
    logger.info(f"Example task completed with result={result}")
    return result