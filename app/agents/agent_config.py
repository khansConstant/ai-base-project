"""
Agent Configuration - Centralized configuration for all agents in the system.
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Information about a specific agent"""
    name: str
    description: str
    context_keys: List[str]
    agent_class: str


class AgentConfiguration:
    """
    Centralized configuration class that contains all agent information including
    names, descriptions, and required context keys.
    """

    def __init__(self):
        self.agent_configs = {
            "Attrition": AgentInfo(
                name="Attrition",
                description="Employee Attrition and Retention",
                context_keys=["team_size", "turnover_rate", "department", "time_period"],
                agent_class="AttritionAgent"
            ),
            "Engagement": AgentInfo(
                name="Engagement",
                description="Employee Engagement",
                context_keys=["engagement_score", "team_size", "recent_surveys", "main_concerns"],
                agent_class="EngagementAgent"
            ),
            "Performance": AgentInfo(
                name="Performance",
                description="Employee Performance Management",
                context_keys=["performance_metrics", "team_role", "performance_period", "specific_issues"],
                agent_class="PerformanceAgent"
            ),
            "Culture": AgentInfo(
                name="Culture",
                description="Organizational Culture",
                context_keys=["company_size", "culture_issues", "values", "desired_culture"],
                agent_class="CultureAgent"
            ),
            "Leadership Readiness": AgentInfo(
                name="Leadership Readiness",
                description="Leadership Development",
                context_keys=["leadership_level", "development_areas", "succession_planning", "timeline"],
                agent_class="LeadershipAgent"
            ),
            "Profitability/Execution": AgentInfo(
                name="Profitability/Execution",
                description="Profitability and Execution",
                context_keys=["business_goals", "current_performance", "obstacles", "resources"],
                agent_class="ExecutionAgent"
            ),
            "DEI/Fairness": AgentInfo(
                name="DEI/Fairness",
                description="Diversity, Equity, and Inclusion",
                context_keys=["diversity_metrics", "dei_initiatives", "specific_concerns", "organizational_commitment"],
                agent_class="DEIAgent"
            ),
            "Default": AgentInfo(
                name="Default",
                description="General HR and Organizational Support",
                context_keys=["problem_type", "specific_details", "urgency"],
                agent_class="DefaultAgent"
            )
        }

    def get_agent_info(self, agent_name: str) -> AgentInfo:
        """Get information about a specific agent"""
        return self.agent_configs.get(agent_name)

    def get_all_agents(self) -> Dict[str, AgentInfo]:
        """Get information about all agents"""
        return self.agent_configs.copy()

    def get_agent_names(self) -> List[str]:
        """Get list of all agent names"""
        return list(self.agent_configs.keys())

    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get dictionary mapping agent names to descriptions"""
        return {name: info.description for name, info in self.agent_configs.items()}

    def get_all_context_keys(self) -> Dict[str, List[str]]:
        """Get dictionary mapping agent names to their required context keys"""
        return {name: info.context_keys for name, info in self.agent_configs.items()}

    def get_context_keys_for_agent(self, agent_name: str) -> List[str]:
        """Get required context keys for a specific agent"""
        agent_info = self.get_agent_info(agent_name)
        return agent_info.context_keys if agent_info else []

    def get_agents_requiring_context_key(self, context_key: str) -> List[str]:
        """Get list of agents that require a specific context key"""
        return [name for name, info in self.agent_configs.items()
                if context_key in info.context_keys]


# Global instance for easy access
agent_config = AgentConfiguration()


def get_agent_config() -> AgentConfiguration:
    """Get the global agent configuration instance"""
    return agent_config
