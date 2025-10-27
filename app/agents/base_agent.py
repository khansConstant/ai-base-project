"""
Base Agent class for all specialized agents in the multi-agent system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class AgentResponse(BaseModel):
    """Structured response from an agent"""
    action_plan: str
    next_questions: List[Dict[str, str]] = []  # Change this to a list of dictionaries
    updated_context: Dict[str, Any] = {}
    confidence: float = 0.8
    requires_clarification: bool = False


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    Each agent handles a specific problem domain.
    """
    
    def __init__(self, agent_name: str, problem_domain: str):
        self.agent_name = agent_name
        self.problem_domain = problem_domain
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    @abstractmethod
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        """
        Main method to execute the agent logic.
        
        Args:
            user_query: The user's question or problem statement
            context: Current conversation context and collected information
            original_user_query: The original user query (optional)
            
        Returns:
            AgentResponse with action plan, questions, and updated context
        """
        pass

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """
        Update context with user input and continue the conversation.

        Args:
            user_query: The current user query or response
            context: Current conversation context
            answer: User's answer to the clarifying question
            question_index: Index of the current question being answered
            original_user_query: The original user query (optional)

        Returns:
            AgentResponse with updated context and next steps
        """
        # Default implementation: just run the agent with updated context
        return await self.run_agent(user_query, context, original_user_query)

    # def check_clarification_needed(self, context: Dict[str, Any]) -> bool:
    #     """
    #     Check if clarifying questions are needed based on context.
        
    #     Args:
    #         context: Current context dictionary
            
    #     Returns:
    #         True if clarification is needed, False otherwise
    #     """
    #     required_fields = self.get_required_context_fields()
    #     missing_fields = [field for field in required_fields if field not in context or not context[field]]
        
    #     self.logger.info(f"Missing context fields: {missing_fields}")
    #     return len(missing_fields) > 0
    def check_clarification_needed(self, context: Dict[str, Any]) -> int:
        """Return the index of the next missing context field, or -1 if all filled."""
        required_fields = self.get_required_context_fields()
        for i, field in enumerate(required_fields):
            if field not in context or not context[field]:
                return i  # next missing question index
        return -1  # no clarification needed

    
    @abstractmethod
    def get_required_context_fields(self) -> List[str]:
        """
        Define what context fields are required for this agent.
        
        Returns:
            List of required field names
        """
        pass
    
    @abstractmethod
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate clarifying questions based on missing context.
        
        Args:
            context: Current context
            
        Returns:
            List of clarifying questions
        """
        pass
    
    def get_domain_specific_prompt(self) -> str:
        """
        Get the domain-specific system prompt for this agent.
        
        Returns:
            System prompt string
        """
        return f"You are an expert in {self.problem_domain}."
