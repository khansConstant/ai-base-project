from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Union, Optional
from pydantic import BaseModel
import logging
import json
import os
from langchain.chat_models import init_chat_model
from langchain.schema import HumanMessage, SystemMessage

llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat_bot", tags=["chat_bot"])

# --- OpenAI Setup --)

# --- Problem categories ---
PROBLEM_TYPES = [
    "Attrition",
    "Engagement",
    "Performance",
    "Culture",
    "Leadership Readiness",
    "Profitability/Execution",
    "DEI/Fairness"
]

# --- Pydantic Models ---
class ClassifyProblemRequest(BaseModel):
    """User input message for classification - supports both string and dict formats"""
    message: Union[str, Dict[str, Any]]
    user_id: Optional[str] = None

    class Config:
        """Allow extra fields and flexible input parsing"""
        extra = "allow"
        validate_assignment = True


class OpenAIClassification(BaseModel):
    """OpenAI classification output (internal)"""
    problem_type: str
    confidence: float


class ClassifyProblemResponse(BaseModel):
    """Structured classification response"""
    problem_type: str
    confidence: float
    suggested_agent: str



# --- Helper Function ---
async def classify_problem_with_openai(message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uses OpenAI to classify a workplace problem into a predefined category.
    Handles both string and dictionary input formats.
    """
    # Extract the actual message content
    if isinstance(message, str):
        actual_message = message.strip()
    elif isinstance(message, dict):
        # If it's a dict, try to extract common message fields
        actual_message = (
            message.get("message") or
            message.get("text") or
            message.get("content") or
            message.get("question") or
            str(message)  # fallback to string representation
        ).strip()
    else:
        actual_message = str(message).strip()

    # Validate that we have actual content to classify
    if not actual_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty or invalid message provided for classification"
        )

    logger.info(f"Processing message: {actual_message[:100]}...")  # Log first 100 chars for debugging

    system_prompt = (
        "You are an expert in organizational psychology and workplace issues. "
        "Your task is to classify workplace-related problems into specific categories. "
        "Analyze the following text and determine which category it best fits into. "
        ""
        "Categories: " + ", ".join(PROBLEM_TYPES) + ". "
        ""
        "If the text describes a workplace problem, issue, or challenge related to one of these categories, classify it accordingly. "
        "If the text is a clarifying question from an AI assistant, classify it as 'Other'. "
        "If the text is a response to a clarifying question, try to determine the underlying workplace issue. "
        "If the text doesn't clearly fit any category or appears to be general conversation, classify it as 'Other'. "
        ""
        "Return your answer strictly as a JSON object with two keys: "
        "'problem_type' for the category name, and 'confidence' as a number between 0 and 1. "
        "Do not include any text outside the JSON."
    )

    try:
        # Create structured output LLM using the internal classification model
        structured_llm = llm.with_structured_output(OpenAIClassification)

        # Invoke with messages list directly (not as keyword argument)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=actual_message)
        ]

        # The structured output will return a Pydantic model instance
        result = structured_llm.invoke(messages)

        logger.info(f"Classification result: {result}")

        # Convert Pydantic model to dict
        return {
            "problem_type": result.problem_type,
            "confidence": result.confidence
        }

    except Exception as e:
        logger.error(f"OpenAI classification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during classification: {str(e)}"
        )


# --- Endpoint ---
@router.post(
    "/classify-problem",
    summary="Classify a workplace problem",
    description="Analyzes a user message and classifies it into one of the predefined problem categories.",
    response_model=ClassifyProblemResponse
)
async def classify_problem_endpoint(request: ClassifyProblemRequest):
    """
    Takes user input and returns a classified problem type.
    """
    try:
        # Log what we're receiving for debugging
        logger.info(f"Received request: message_type={type(request.message)}, user_id={request.user_id}")

        # Validate that we have a meaningful message to classify
        if not request.message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message is required for classification"
            )

        result = await classify_problem_with_openai(request.message)

        problem_type = result.get("problem_type", "Unknown")
        confidence = float(result.get("confidence", 0.5))

        # Handle Unknown or Other classifications
        if problem_type in ["Unknown", "Other"]:
            problem_type = "Other"
            confidence = 0.3  # Lower confidence for unclassified content

        agent_map = {
            "Attrition": "AttritionAgent",
            "Engagement": "EngagementAgent",
            "Performance": "PerformanceAgent",
            "Culture": "CultureAgent",
            "Leadership Readiness": "LeadershipAgent",
            "Profitability/Execution": "ExecutionAgent",
            "DEI/Fairness": "DEIAgent",
            "Other": "DefaultAgent"  # Fallback for unclassified problems
        }

        response = ClassifyProblemResponse(
            problem_type=problem_type,
            confidence=confidence,
            suggested_agent=agent_map.get(problem_type, "DefaultAgent")
        )

        logger.info(f"Classified message: {problem_type} (confidence: {confidence})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in classify_problem_endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to classify problem: {str(e)}"
        )
