from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import json
from pydantic import BaseModel, Field


def create_message_pair(system_prompt: str, user_prompt: str) -> list[Dict[str, Any]]:
    """
    Create a standardized message pair for LLM interactions.


    Args:
        system_prompt: The system message content
        user_prompt: The user message content


    Returns:
        List containing system and user message dictionaries
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]