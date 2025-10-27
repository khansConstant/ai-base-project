"""
Attrition Agent - Handles employee turnover and retention issues.
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os
import logging

logger = logging.getLogger(__name__)


class AttritionAgent(BaseAgent):
    """
    Specialized agent for handling attrition and retention problems.
    """
    
    def __init__(self):
        super().__init__(agent_name="AttritionAgent", problem_domain="Employee Attrition and Retention")
        self.llm = init_chat_model("gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        """Required context for attrition analysis"""
        return [
            "team_size",
            "turnover_rate",
            "department",
            "time_period"
        ]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        """Generate questions to gather missing attrition context"""
        questions = []
        
        if "team_size" not in context:
            questions.append("What is the size of your team or department?")
        if "turnover_rate" not in context:
            questions.append("What is your current turnover rate or how many people have left recently?")
        if "department" not in context:
            questions.append("Which department or team is experiencing attrition?")
        if "time_period" not in context:
            questions.append("Over what time period has this attrition occurred?")
        
        return questions
    
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        """
        Execute attrition agent logic.
        """
        self.logger.info(f"Running AttritionAgent with query: {user_query}")
        
        # Check if clarification is needed
        needs_clarification = self.check_clarification_needed(context)
        
        if needs_clarification:
            clarifying_questions = self.generate_clarifying_questions(context)
            return AgentResponse(
                action_plan="I need more information to provide a comprehensive attrition analysis.",
                next_questions=clarifying_questions,
                updated_context=context,
                requires_clarification=True,
                confidence=0.5
            )
        
        # Fetch insights from knowledge base (placeholder)
        knowledge_insights = await self._fetch_knowledge_insights(context)

        print(knowledge_insights,'knowledge_insights')
        
        # Generate structured response using OpenAI
        response = await self._generate_action_plan(user_query, context, knowledge_insights, original_user_query)
        
        return response
    
    async def _fetch_knowledge_insights(self, context: Dict[str, Any]) -> str:
        """
        Placeholder for knowledge base retrieval.
        In production, this would query a vector database.
        """
        # TODO: Implement actual knowledge base retrieval
        insights = f"""
        Relevant insights for attrition in {context.get('department', 'the organization')}:
        - Industry benchmark turnover rate: 15-20% annually
        - Common attrition drivers: compensation, career growth, work-life balance, management
        - Retention strategies: competitive pay, development opportunities, recognition programs
        """
        return insights
    
    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For AttritionAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
    
    async def _generate_action_plan(
        self,
        user_query: str,
        context: Dict[str, Any],
        knowledge_insights: str,
        original_user_query: str = None
    ) -> AgentResponse:
        """
        Generate action plan using OpenAI API.
        """
        system_prompt = f"""
        {self.get_domain_specific_prompt()}

        You are analyzing an employee attrition problem. Use the provided context and knowledge insights
        to create a comprehensive action plan.

        Context: {context}
        Original Query: {original_user_query or user_query}
        Current Query: {user_query}
        Knowledge Insights: {knowledge_insights}

        Provide a structured response with:
        1. action_plan: A detailed action plan with specific, actionable steps (string)
        2. next_questions: Any follow-up questions if more information would be helpful (list of strings, can be empty)
        3. updated_context: The original context with any additional insights or analysis you've added (dict)
        4. confidence: Your confidence in this recommendation (0.0 to 1.0)
        5. requires_clarification: Whether you need more information (boolean)

        Be specific, practical, and data-driven in your recommendations.
        """
        
        try:
            # Create structured output
            structured_llm = self.llm.with_structured_output(AgentResponse)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]

            print(messages,'messages')
            
            result = structured_llm.invoke(messages)
            
            # Ensure updated_context is populated with at least the original context
            if not result.updated_context:
                result.updated_context = context.copy()
            
            self.logger.info(f"Generated action plan: {result.action_plan[:100]}...")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating action plan: {str(e)}")
            # Fallback response
            return AgentResponse(
                action_plan="I encountered an error generating the action plan. Please try again.",
                next_questions=["Could you provide more details about the attrition issue?"],
                updated_context=context,
                confidence=0.3
            )
