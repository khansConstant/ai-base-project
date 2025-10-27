"""
Agent Manager - Routes queries to the appropriate specialized agent.
"""
from typing import Dict, Any

from app.agents.dei_agent import DEIAgent
from .base_agent import BaseAgent, AgentResponse
from .attrition_agent import AttritionAgent
from .engagement_agent import EngagementAgent
from .performance_agent import PerformanceAgent
from .culture_agent import CultureAgent
from .leadership_agent import LeadershipAgent
from .execution_agent import ExecutionAgent
from .default_agent import DefaultAgent
from .agent_config import agent_config
import logging

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages routing of queries to specialized agents based on problem type.
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "Attrition": AttritionAgent(),
            "Engagement": EngagementAgent(),
            "Performance": PerformanceAgent(),
            "Culture": CultureAgent(),
            "Leadership Readiness": LeadershipAgent(),
            "Profitability/Execution": ExecutionAgent(),
            "DEI/Fairness": DEIAgent(),
            "Default": DefaultAgent(),  # Default agent for unmatched queries
        }
        self.logger = logging.getLogger("AgentManager")

        # Mapping from agent class names to problem types for routing
        self.agent_class_to_problem_type = {
            "AttritionAgent": "Attrition",
            "EngagementAgent": "Engagement",
            "PerformanceAgent": "Performance",
            "CultureAgent": "Culture",
            "LeadershipAgent": "Leadership Readiness",
            "ExecutionAgent": "Profitability/Execution",
            "DEIAgent": "DEI/Fairness",
            "DefaultAgent": "Default"
        }
    
    async def route_to_agent(
        self,
        problem_type: str,
        user_query: str,
        context: Dict[str, Any],
        suggested_agent: str = None,
        original_user_query: str = None
    ) -> AgentResponse:
        """
        Route the query to the appropriate agent based on problem type.

        Args:
            problem_type: The classified problem category
            user_query: User's question or problem statement
            context: Current conversation context
            suggested_agent: The suggested agent class name (optional)
            original_user_query: The original user query (optional)

        Returns:
            AgentResponse from the selected agent
        """
        self.logger.info(f"Routing to agent for problem type: {problem_type}")

        # Determine which agent to use
        # PRIORITY: Always use suggested_agent if provided (prevents agent switching)
        if suggested_agent:
            self.logger.info(f"🔄 Using suggested_agent: {suggested_agent}")
            # Map the suggested_agent to its problem type
            agent_problem_type = self.agent_class_to_problem_type.get(suggested_agent, problem_type)
        else:
            self.logger.info(f"📋 Using problem_type: {problem_type}")
            # Use problem_type directly
            agent_problem_type = problem_type

        # Get the appropriate agent
        agent = self.agents.get(agent_problem_type)

        if not agent:
            self.logger.warning(f"No specific agent found for: {agent_problem_type}. Routing to DefaultAgent.")
            # Route to DefaultAgent for unmatched queries
            agent = self.agents.get("Default")

        if not agent:
            # Final fallback if DefaultAgent is also not available
            self.logger.error("DefaultAgent not available. Returning error response.")
            return AgentResponse(
                action_plan=f"I'm not sure how to handle '{problem_type}' problems yet. Please contact support.",
                next_questions=["Can you rephrase your question or provide more context?"],
                updated_context=context,
                confidence=0.2
            )

        # Execute the agent
        try:
            response = await agent.run_agent(user_query, context, original_user_query=original_user_query)
            self.logger.info(f"Agent {agent.agent_name} completed successfully")
            return response
        except Exception as e:
            self.logger.error(f"Error executing agent {agent.agent_name}: {str(e)}")
            return AgentResponse(
                action_plan="An error occurred while processing your request. Please try again.",
                next_questions=["Could you provide more details about your issue?"],
                updated_context=context,
                confidence=0.3
            )
    
    def get_available_agents(self) -> list[dict]:
        """
        Get list of available agents with their names, descriptions, context keys, and agent classes.

        Returns:
            List of dictionaries containing agent names, descriptions, context keys, and agent classes
        """
        agents_info = []
        for name in self.agents.keys():
            agent_info = agent_config.get_agent_info(name)
            if agent_info:
                agents_info.append({
                    "name": agent_info.name,
                    "description": agent_info.description,
                    "context_keys": agent_info.context_keys,
                    "agent_class": agent_info.agent_class
                })

        return agents_info
