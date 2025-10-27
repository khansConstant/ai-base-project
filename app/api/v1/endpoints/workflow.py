"""
Workflow API Endpoint - Execute the multi-agent workflow
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from app.graph.workflow import get_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])


# ==================== REQUEST/RESPONSE MODELS ====================

class WorkflowRequest(BaseModel):
    """Request model for workflow execution"""
    user_query: str
    original_query: Optional[str] = None  # The original user query for consistent classification
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response model for workflow execution"""
    problem_type: str
    suggested_agent: str
    confidence: float
    action_plan: str
    response_text: str  # For intermediate responses, empty when action_plan is populated
    user_query: str
    next_questions: list
    requires_clarification: bool
    context: Dict[str, Any]
    iteration_count: int


# ==================== ENDPOINTS ====================

@router.post(
    "/execute",
    summary="Execute Multi-Agent Workflow",
    description="""
    Execute the complete multi-agent workflow:
    1. Classify the problem
    2. Route to appropriate agent
    3. Collect context and clarifying questions
    4. Retrieve knowledge insights
    5. Generate action plan
    6. Collect feedback

    Returns a structured action plan with next steps.

    Request body should include:
    - user_query: Current user message
    - original_query: Original user query for consistent classification (optional)
    - context: Existing conversation context (optional)
    """,
    response_model=WorkflowResponse
)
async def execute_workflow(request: WorkflowRequest):
    """
    Execute the multi-agent workflow for a user query.
    """
    try:
        logger.info(f"Executing workflow for query: {request.user_query}")
        
        # Get the workflow instance
        workflow = get_workflow()
        
        # Execute the workflow
        result = await workflow.execute(
            user_query=request.user_query,
            context=request.context,
            original_query=request.original_query
        )
        
        # Format the response
        response = WorkflowResponse(
            problem_type=result.get("problem_type", "Other"),
            user_query=request.user_query,
            suggested_agent=result.get("suggested_agent", "DefaultAgent"),
            confidence=result.get("confidence", 0.5),
            action_plan=result.get("action_plan", ""),
            response_text=result.get("response_text", ""),  # Use response_text for intermediate responses
            next_questions=result.get("next_questions", []),
            requires_clarification=result.get("requires_clarification", False),
            context=result.get("context", {}),
            iteration_count=result.get("iteration_count", 0)
        )

        # Ensure original_query is in the response context for follow-up requests
        # if request.original_query and "original_user_query" not in response.context:
        #     response.context["original_user_query"] = request.original_query
        
        logger.info(f"Workflow completed successfully. Clarification needed: {response.requires_clarification}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute workflow: {str(e)}"
        )


@router.post(
    "/continue",
    summary="Continue Workflow with Context",
    description="""
    Continue an existing workflow session with updated context.
    Use this endpoint when the user has answered clarifying questions.
    """,
    response_model=WorkflowResponse
)
async def continue_workflow(request: WorkflowRequest):
    """
    Continue the workflow with updated context from user responses.
    """
    try:
        logger.info(f"Continuing workflow with updated context")
        
        if not request.context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Context is required to continue the workflow"
            )
        
        # Get the workflow instance
        workflow = get_workflow()
        
        # Execute the workflow with updated context
        result = await workflow.execute(
            user_query=request.user_query,
            context=request.context,
            original_query=request.original_query
        )
        
        # Format the response
        response = WorkflowResponse(
            problem_type=result.get("problem_type", "Other"),
            suggested_agent=result.get("suggested_agent", "DefaultAgent"),
            confidence=result.get("confidence", 0.5),
            action_plan=result.get("action_plan", ""),
            response_text=result.get("response_text", ""),  # Use response_text for intermediate responses
            next_questions=result.get("next_questions", []),
            requires_clarification=result.get("requires_clarification", False),
            context=result.get("context", {}),
            iteration_count=result.get("iteration_count", 0)
        )

        # Ensure original_query is in the response context for follow-up requests
        # if request.original_query and "original_user_query" not in response.context:
        #     response.context["original_user_query"] = request.original_query
        
        logger.info(f"Workflow continuation completed")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error continuing workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to continue workflow: {str(e)}"
        )


@router.get(
    "/agents",
    summary="List Available Agents",
    description="Get a list of all available specialized agents in the system."
)
async def list_agents():
    """
    List all available agents and their problem domains.
    """
    try:
        workflow = get_workflow()
        agents = workflow.agent_manager.get_available_agents()
        
        return {
            "agents": agents,
            "count": len(agents)
        }
    
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list agents: {str(e)}"
        )
