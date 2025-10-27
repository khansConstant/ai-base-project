"""
Performance Agent - Handles employee performance and productivity issues.
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
import os
import logging

logger = logging.getLogger(__name__)


class PerformanceAgent(BaseAgent):
    """Specialized agent for performance management issues."""
    
    def __init__(self):
        super().__init__(agent_name="PerformanceAgent", problem_domain="Employee Performance Management")
        self.llm = init_chat_model("gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        return ["performance_metrics", "team_role", "performance_period", "specific_issues"]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        questions = []
        if "performance_metrics" not in context:
            questions.append("What specific performance metrics or KPIs are you tracking?")
        if "team_role" not in context:
            questions.append("What is the role or position of the employee(s) in question?")
        if "performance_period" not in context:
            questions.append("Over what time period have you observed these performance issues?")
        if "specific_issues" not in context:
            questions.append("What specific performance issues have you noticed?")
        return questions
    
    async def run_agent(self, user_query: str, context: Dict[str, Any], original_user_query: str = None) -> AgentResponse:
        print(f"🚀 PerformanceAgent started with query: {user_query}")
        self.logger.info(f"Running PerformanceAgent with query: {user_query}")
        
        if self.check_clarification_needed(context):
            return AgentResponse(
                action_plan="I need more information to provide performance improvement recommendations.",
                next_questions=self.generate_clarifying_questions(context),
                updated_context=context,
                requires_clarification=True,
                confidence=0.5
            )
        
        knowledge_insights = await self._fetch_knowledge_insights(context)
        return await self._generate_action_plan(user_query, context, knowledge_insights, original_user_query)
    
    async def _fetch_knowledge_insights(self, context: Dict[str, Any]) -> str:
        return f"""
        Performance management insights:
        - Align six subsystems of performance — expectations, skills, motivation, rewards, capacity, and environment — before defaulting to training.
        - Use performance support tools (job aids, checklists, prompts) as the first-line solution; reserve training only for unmastered skills.
        - Build context-intensive training that mirrors how exemplary performers work, using real examples and simulations for transferability.
        - Focus training on procedural knowledge (“knowing how”), not just declarative knowledge (“knowing what”).
        - Capture and model expert heuristics and mental models to accelerate learning and problem-solving in others.
        - Base design decisions on data from the actual work context, not assumptions — this ensures relevance and cost-effectiveness.
        - Use profiles of exemplary performance to reduce ramp-up time for new hires by 30%+ and training time by 20–40%.
        - Continuously update performance support materials as processes change to maintain accuracy and reduce retraining costs.
        - **Mission-first leadership:** High-performance teams anchor every action to a clear, shared mission (“Return with Honor”). The mission outlasts leaders and unites individuals across adversity.
        - **Shared accountability:** The ethos “You are your brother’s keeper” builds mutual trust, second chances, and collective responsibility — leaders protect, challenge, and care for their people.
        - **Simplicity in systems:** Rules and processes are minimal and purpose-driven (“Think Big and Basically”), empowering individuals with autonomy and clarity of purpose.
        - **Focus on controllables:** “Don’t Piss Off the Turnkey” teaches discipline in controlling reactions, conserving energy, and focusing only on what can be influenced — the Stoic foundation of resilience.
        - **Optimism through realism:** “Keeping the Faith” emphasizes hard-nosed optimism — viewing setbacks as temporary and external, using failures as learning moments.
        - **Collective meaning:** “The Power of We” defines culture as shared purpose and values — individuals find identity through contribution to a cause larger than themselves.
        - **Resilience as learnable:** The POWs demonstrated that resilience is cultivated through belief systems, discipline, and perspective — not innate luck (“Lucky or Learned”).
        - **Virtual leadership:** Great leaders inspire through purpose, consistency, and values even when physically absent — leadership is a system, not a person.
        - **Social network as culture:** Communication (like the POWs’ “tap code”) sustains belonging, morale, and alignment — connection is the backbone of performance.
        - **No-excuse execution:** Sustainable excellence comes from discipline, self-regulation, and shared commitment rather than external motivation or oversight.
        """
    
    async def _generate_action_plan(self, user_query: str, context: Dict[str, Any], knowledge_insights: str, original_user_query: str = None) -> AgentResponse:
        system_prompt = f"""
        {self.get_domain_specific_prompt()}

        Analyze this performance issue and provide actionable recommendations.
        Context: {context}
        Original Query: {original_user_query or user_query}
        Current Query: {user_query}
        Knowledge: {knowledge_insights}

        Provide a structured response with:
        1. action_plan: Detailed action plan with specific steps, timelines, and success metrics (string)
        2. next_questions: Follow-up questions if needed (list, can be empty)
        3. updated_context: Original context with your analysis added (dict)
        4. confidence: Your confidence level (0.0 to 1.0)
        5. requires_clarification: Whether you need more info (boolean)
        """
        
        # Log the system prompt (using both print and logger for visibility)
        separator = "=" * 80
        print(separator)
        print("PERFORMANCE AGENT - SYSTEM PROMPT")
        print(separator)
        print(f"\n{system_prompt}\n")
        print(separator)
        print(f"USER QUERY: {user_query}")
        print(separator)
        
        
        try:
            structured_llm = self.llm.with_structured_output(AgentResponse)
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]
            
            # Log the complete messages being sent to OpenAI
            print("Messages being sent to OpenAI:")
            for i, msg in enumerate(messages):
                print(f"Message {i+1} ({type(msg).__name__}): {msg.content[:200]}...")
            
            self.logger.info("Messages being sent to OpenAI:")
            for i, msg in enumerate(messages):
                self.logger.info(f"Message {i+1} ({type(msg).__name__}): {msg.content[:200]}...")
            
            result = structured_llm.invoke(messages)
            if not result.updated_context:
                result.updated_context = context.copy()
            self.logger.info(f"Generated performance action plan")
            return result
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            return AgentResponse(
                action_plan="Error generating plan. Please provide more details.",
                next_questions=["What are the main performance concerns?"],
                updated_context=context,
                confidence=0.3
            )

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the conversation."""
        # For PerformanceAgent, use the default implementation from base class
        return await super().update_context_and_continue(user_query, context, answer, question_index, original_user_query)
