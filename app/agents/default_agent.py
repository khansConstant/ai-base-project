"""
Default Agent - Handles general queries that don't fit into specialized agents.
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os

class DefaultAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="DefaultAgent", problem_domain="General HR and Organizational Support")
        self.llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

    def get_required_context_fields(self) -> List[str]:
        """Default agent doesn't require specific context fields."""
        return []

    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        """Generate general clarifying questions for better understanding."""
        questions = []
        if not context.get("problem_type"):
            questions.append("Can you help me understand what type of organizational or HR issue you're facing?")
        if not context.get("specific_details"):
            questions.append("Could you provide more specific details about your situation?")
        if not context.get("urgency"):
            questions.append("How urgent is this issue for your organization?")
        return questions

    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        """Handle general queries with basic AI assistance."""
        knowledge = "General HR support: employee relations, policy guidance, organizational development, workplace issues"

        # Check if this is a thank you message or simple acknowledgment
        thank_you_keywords = ["thank", "thanks", "appreciate", "grateful", "ty"]
        is_thank_you = any(keyword in user_query.lower() for keyword in thank_you_keywords)

        if is_thank_you:
            # For thank you messages, provide a polite response without requiring clarification
            return AgentResponse(
                action_plan="You're welcome! If you have any specific questions or need assistance with HR or organizational support, feel free to ask.",
                next_questions=[],  # No need for more questions
                updated_context=context,
                confidence=0.9,
                requires_clarification=False  # Don't require clarification for thank you
            )

        system_prompt = f"""{self.get_domain_specific_prompt()}
Context: {context}
Original Query: {original_user_query or user_query}
Current Query: {user_query}
Knowledge: {knowledge}

You are a helpful HR and organizational development assistant. Provide practical advice and guidance for general workplace issues.
If the query seems to fit a specialized area (like attrition, engagement, performance, culture, leadership, profitability, or DEI),
suggest that the user might want to rephrase their question to be more specific.

Provide: action_plan (string), next_questions (list), updated_context (dict), confidence (float), requires_clarification (bool)"""

        try:
            structured_llm = self.llm.with_structured_output(AgentResponse)
            print(system_prompt,'system_prompt_default')
            result = structured_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_query)])

            # Ensure the updated context is set
            if not result.updated_context:
                result.updated_context = context.copy()

            return result
        except Exception as e:
            self.logger.error(f"Error in DefaultAgent: {str(e)}")
            return AgentResponse(
                action_plan="I understand you're looking for general guidance. Could you tell me more about your specific situation so I can provide better assistance?",
                next_questions=self.generate_clarifying_questions(context),
                updated_context=context,
                confidence=0.6,
                requires_clarification=True
            )

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For DefaultAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
