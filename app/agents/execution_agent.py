"""Execution Agent - Handles profitability and execution issues."""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os

class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="ExecutionAgent", problem_domain="Profitability and Execution")
        self.llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        return ["business_goals", "current_performance", "obstacles", "resources"]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        questions = []
        if "business_goals" not in context:
            questions.append("What are your key business goals or targets?")
        if "current_performance" not in context:
            questions.append("What is your current performance against these goals?")
        if "obstacles" not in context:
            questions.append("What obstacles are preventing successful execution?")
        if "resources" not in context:
            questions.append("What resources (people, budget, tools) are available?")
        return questions
    
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        if self.check_clarification_needed(context):
            return AgentResponse(action_plan="Need execution context.", next_questions=self.generate_clarifying_questions(context), updated_context=context, requires_clarification=True, confidence=0.5)
        knowledge = "Execution: clear goals, accountability, resource allocation, metrics, regular reviews"
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
            return AgentResponse(action_plan="Error. Provide details.", next_questions=["What execution challenges exist?"], updated_context=context, confidence=0.3)

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For ExecutionAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
