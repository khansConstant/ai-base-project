"""DEI Agent - Handles diversity, equity, and inclusion issues."""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os

class DEIAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="DEIAgent", problem_domain="Diversity, Equity, and Inclusion")
        self.llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        return ["diversity_metrics", "dei_initiatives", "specific_concerns", "organizational_commitment"]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        questions = []
        if "diversity_metrics" not in context:
            questions.append("What are your current diversity metrics or demographics?")
        if "dei_initiatives" not in context:
            questions.append("What DEI initiatives do you currently have in place?")
        if "specific_concerns" not in context:
            questions.append("What specific DEI concerns or incidents have occurred?")
        if "organizational_commitment" not in context:
            questions.append("What is the leadership's commitment level to DEI?")
        return questions
    
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        if self.check_clarification_needed(context):
            return AgentResponse(action_plan="Need DEI context.", next_questions=self.generate_clarifying_questions(context), updated_context=context, requires_clarification=True, confidence=0.5)
        knowledge = "DEI: inclusive hiring, bias training, ERGs, equitable policies, psychological safety"
        system_prompt = f"""{self.get_domain_specific_prompt()}
Context: {context}
Knowledge: {knowledge}

Provide: action_plan (string), next_questions (list), updated_context (dict), confidence (float), requires_clarification (bool)"""
        try:
            structured_llm = self.llm.with_structured_output(AgentResponse)
            result = structured_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_query)])
            if not result.updated_context:
                result.updated_context = context.copy()
            return result
        except Exception:
            return AgentResponse(action_plan="Error. Provide details.", next_questions=["What DEI challenges exist?"], updated_context=context, confidence=0.3)

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For DEIAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
