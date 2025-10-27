"""Engagement Agent - Handles employee engagement and motivation issues."""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os

class EngagementAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="EngagementAgent", problem_domain="Employee Engagement")
        self.llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        return ["engagement_score", "team_size", "recent_surveys", "main_concerns"]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        questions = []
        if "engagement_score" not in context:
            questions.append("What is your current employee engagement score or level?")
        if "team_size" not in context:
            questions.append("How large is the team experiencing engagement issues?")
        if "recent_surveys" not in context:
            questions.append("Have you conducted any recent engagement surveys? What were the findings?")
        if "main_concerns" not in context:
            questions.append("What are the main engagement concerns raised by employees?")
        return questions
    
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        if self.check_clarification_needed(context):
            return AgentResponse(
                action_plan="I need more information about engagement levels.",
                next_questions=self.generate_clarifying_questions(context),
                updated_context=context,
                requires_clarification=True,
                confidence=0.5
            )
        knowledge = "Engagement drivers: purpose, autonomy, mastery, recognition, work-life balance"
        system_prompt = f"""{self.get_domain_specific_prompt()}
Context: {context}
Original Query: {original_user_query or user_query}
Current Query: {user_query}
Knowledge: {knowledge}

Provide: action_plan (string), next_questions (list), updated_context (dict), confidence (float), requires_clarification (bool)"""
        try:
            structured_llm = self.llm.with_structured_output(AgentResponse)
            result = structured_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_query)])
            if not result.updated_context:
                result.updated_context = context.copy()
            return result
        except Exception:
            return AgentResponse(action_plan="Error. Please provide more details.", next_questions=["What engagement issues are you facing?"], updated_context=context, confidence=0.3)

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For EngagementAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
