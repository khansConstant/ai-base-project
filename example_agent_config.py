#!/usr/bin/env python3
"""
Example usage of the AgentConfiguration class.
This script demonstrates how to use the centralized agent configuration.
"""

from app.agents.agent_config import agent_config


def main():
    """Demonstrate the AgentConfiguration class functionality"""

    print("=== Agent Configuration Demo ===\n")

    # Get all agents
    all_agents = agent_config.get_all_agents()
    print(f"Total agents: {len(all_agents)}")
    print("Available agents:")
    for name, info in all_agents.items():
        print(f"  - {name}: {info.description}")
    print()

    # Get agent descriptions
    descriptions = agent_config.get_agent_descriptions()
    print("Agent descriptions:")
    for name, desc in descriptions.items():
        print(f"  {name}: {desc}")
    print()

    # Get context keys for all agents
    all_context_keys = agent_config.get_all_context_keys()
    print("Required context keys for each agent:")
    for name, keys in all_context_keys.items():
        print(f"  {name}: {', '.join(keys)}")
    print()

    # Get context keys for a specific agent
    attrition_keys = agent_config.get_context_keys_for_agent("Attrition")
    print(f"Context keys for Attrition agent: {', '.join(attrition_keys)}")

    # Find agents that require a specific context key
    agents_needing_team_size = agent_config.get_agents_requiring_context_key("team_size")
    print(f"Agents requiring 'team_size': {', '.join(agents_needing_team_size)}")

    # Get specific agent info
    engagement_info = agent_config.get_agent_info("Engagement")
    print("Engagement agent info:")
    print(f"  Name: {engagement_info.name}")
    print(f"  Description: {engagement_info.description}")
    print(f"  Context keys: {', '.join(engagement_info.context_keys)}")
    print(f"  Agent class: {engagement_info.agent_class}")


if __name__ == "__main__":
    main()
