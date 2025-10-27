import os
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse
from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage

class CultureAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="CultureAgent", problem_domain="Organizational Culture")
        self.llm = init_chat_model("gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_required_context_fields(self) -> List[str]:
        """Returns the required context fields that need to be filled."""
        return ["company_size", "culture_issues", "values", "desired_culture"]

    def _question_bank(self) -> List[Dict[str, str]]:
        """Centralized question definitions, in required-field order."""
        return [
            {"question": "**I'd love to help you transform your organizational culture!** ✨\n\nTo give you the *best guidance*, could you tell me about the size of your organization?", "key": "company_size"},
            {"question": "**I see you're looking to improve your workplace culture - that's fantastic!** 🎉\n\nWhat specific challenges are you facing right now?", "key": "culture_issues"},
            {"question": "**Core values are the heart of great company culture!** 💙\n\nWhat values drive your organization forward?", "key": "values"},
            {"question": "**I'm excited to help you build something amazing!** 🚀\n\nWhat kind of culture are you envisioning for your team?", "key": "desired_culture"},
        ]

    def generate_clarifying_questions(
        self,
        context: Dict[str, Any],
        question_index: int
    ) -> List[Dict[str, str]]:
        """Returns the next clarifying question based on the index."""
        questions = self._question_bank()
        missing = set(self.check_missing_context(context))

        # Skip already-filled questions and proceed to the next missing field.
        if 0 <= question_index < len(questions):
            q = questions[question_index]
            if q["key"] in missing:
                return [q]

        # Otherwise, ask the first missing question in order.
        for q in questions:
            if q["key"] in missing:
                return [q]
        return []

    
    def check_missing_context(self, context: Dict[str, Any]) -> List[str]:
        """Check which required context fields are missing or effectively empty."""
        missing_fields: List[str] = []
        for field_name in self.get_required_context_fields():
            value = context.get(field_name, None)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing_fields.append(field_name)
        return missing_fields

    def get_domain_specific_prompt(self) -> str:
        """Returns the domain-specific system prompt with a warm, supportive personality."""
        return """You are Alex, a passionate organizational culture expert who loves helping teams create amazing workplaces!

                You're warm, enthusiastic, and genuinely excited about transforming company culture. You believe every organization has incredible potential, and you love celebrating small wins along the way.

                When providing guidance:
                - Start with positive affirmations and encouragement
                - Use conversational, friendly language
                - Show genuine excitement about their goals
                - Offer specific, actionable advice
                - End with motivation and support
                - **Always format responses in Markdown** for beautiful frontend rendering

                Remember: Culture change is a journey, and you're their biggest cheerleader! 🎉
                """

    async def run_agent(self, user_query: str, context: Dict[str, Any], question_index: int = 0, original_user_query: str = None) -> AgentResponse:
        """Handle conversation and respond accordingly."""

        # Check if there are any missing fields in the context
        missing_fields = self.check_missing_context(context)
        action_plan = context.get("action_plan", "")

        # If missing fields exist, continue gathering context
        if missing_fields:
            next_question = self.generate_clarifying_questions(context, question_index)
            return AgentResponse(
                action_plan="Thanks for sharing that with me! I'm gathering all the details I need to help you create an **amazing workplace culture**. Could you help me understand a bit more? ✨",
                next_questions=next_question,
                updated_context=context,
                requires_clarification=True,
                confidence=0.5,
                missing_fields=missing_fields
            )

        # If context is fully gathered, process the user query in a more conversational way
        system_prompt = f"""{self.get_domain_specific_prompt()}
            Context: {context}
            Original User Query: {original_user_query or 'Not provided'}
            Current Interaction: {user_query}
            Action Plan: {action_plan}
            Knowledge: Culture transformation: leadership alignment, communication, behaviors, rituals, recognition, employee engagement, team building, positive work environment, growth mindset, psychological safety, celebration of wins, feedback culture, inclusive practices, work-life balance, professional development, transparent communication, trust building, collaborative environment, innovation encouragement, employee well-being, performance management, change management

            You're here to help the user transform their workplace culture. Provide **positive and supportive** guidance. 

            If the user asks questions about the action plan, feel free to refer back to it. But for general conversation, answer in a **friendly, engaging, and supportive tone**. 

            Encourage their progress and celebrate their initiative to improve the culture. 🎉
        """

        try:
            structured_llm = self.llm.with_structured_output(AgentResponse)

            # Check for positive feedback like "thank you" or "looks good"
            if any(phrase in user_query.lower() for phrase in ["thank you", "thanks", "great", "appreciate", "awesome"]):
                return AgentResponse(
                    action_plan="You're so welcome! 🎉 I'm thrilled you're feeling good about the action plan. If you need any more details or have more questions, I’m here to help!",
                    next_questions=[],
                    updated_context=context,
                    requires_clarification=False,
                    confidence=0.9
                )

            # Generate a conversational response if the user is asking for something else
            final_prompt = f"""{system_prompt}

            Generate a friendly, conversational response to the user’s query. 
            If they ask for the action plan, provide details on how to move forward.
            Otherwise, engage in the conversation and offer supportive insights.
        """

            result = structured_llm.invoke([SystemMessage(content=final_prompt), HumanMessage(content=user_query)])

            # Update the context if needed
            if not result.updated_context:
                result.updated_context = context.copy()

            return result
        except Exception as e:
            return AgentResponse(
                action_plan="I'm so excited you're taking steps to improve your workplace culture! Could you share a bit more about your situation so I can give you the best guidance? 🚀",
                next_questions=[{"question": "What specific challenges are you facing right now?", "key": "culture_issues"}],
                updated_context=context,
                confidence=0.3
            )

    async def update_context_and_continue(self, user_query: str, context: Dict[str, Any], answer: str, question_index: int, original_user_query: str = None) -> AgentResponse:
        """Update context with user input and continue the next question."""
        
        updated_context = context.copy()
        
        # Update the context field with the answer
        next_question = self.generate_clarifying_questions(context, question_index)
        
        if next_question:
            key = next_question[0]["key"]  # Get the key associated with this question
            updated_context[key] = answer  # Update the context field with the answer
        
        if all(field in updated_context for field in self.get_required_context_fields()):
            return await self.run_agent(user_query, updated_context, question_index, original_user_query)

        # Otherwise, continue with the next question
        next_question = self.generate_clarifying_questions(updated_context, question_index + 1)
        return AgentResponse(
            action_plan="Great insights! I'm building a complete picture to help you create the perfect culture transformation plan. What's one more detail you'd like to share? 💡",
            next_questions=next_question,
            updated_context=updated_context,
            requires_clarification=True,
            confidence=0.6,
            question_index=question_index + 1  # Increment question index to ask the next question
        )
