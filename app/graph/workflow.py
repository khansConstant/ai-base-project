"""
LangGraph Workflow for Multi-Agent System
"""
from typing import Dict, Any, TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import logging
import httpx
from app.agents.agent_manager import AgentManager
from app.agents.base_agent import AgentResponse

logger = logging.getLogger(__name__)


# Define the state schema
class WorkflowState(TypedDict):
    """State that flows through the graph"""
    user_query: str
    original_user_query: str  # Preserve the original user query
    problem_type: str
    suggested_agent: str
    confidence: float
    context: Dict[str, Any]
    action_plan: str
    response_text: str  # For intermediate responses before final action plan
    next_questions: list
    requires_clarification: bool
    knowledge_insights: str
    user_feedback: str
    iteration_count: int
    messages: Annotated[list, add_messages]


class MultiAgentWorkflow:
    """
    LangGraph workflow orchestrating the multi-agent system.
    """
    
    def __init__(self):
        self.agent_manager = AgentManager()
        self.graph = self._build_graph()
        self.logger = logging.getLogger("MultiAgentWorkflow")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("input", self.input_node)
        workflow.add_node("problem_classifier", self.problem_classifier_node)
        workflow.add_node("agent_manager", self.agent_manager_node)
        workflow.add_node("context_collector", self.context_collector_node)
        workflow.add_node("knowledge_retrieval", self.knowledge_retrieval_node)
        workflow.add_node("llm_response", self.llm_response_node)
        workflow.add_node("feedback", self.feedback_node)
        
        # Define edges
        workflow.set_entry_point("input")
        
        workflow.add_edge("input", "problem_classifier")
        workflow.add_edge("problem_classifier", "agent_manager")
        workflow.add_edge("agent_manager", "context_collector")
        
        # Conditional edge: if clarification needed, loop back; otherwise continue
        workflow.add_conditional_edges(
            "context_collector",
            self.should_continue_or_clarify,
            {
                "continue": "knowledge_retrieval",
                "clarify": END,  # Return to user for clarification
                "complete": "feedback"
            }
        )
        
        workflow.add_edge("knowledge_retrieval", "llm_response")
        workflow.add_edge("llm_response", "feedback")
        workflow.add_edge("feedback", END)
        
        return workflow.compile()
    
    # ==================== NODE IMPLEMENTATIONS ====================
    
    async def input_node(self, state: WorkflowState) -> WorkflowState:
        """
        Input Node: Initialize the workflow with user query.
        """
        self.logger.info(f"Input Node: Processing query: {state['user_query']}")

        # Preserve the original user query for the entire conversation
        if "original_user_query" not in state:
            # original_user_query should already be set in the execute method
            # No need to derive it from context or other fields
            pass

        # Initialize context if not present
        if "context" not in state or state["context"] is None:
            state["context"] = {}

        if "iteration_count" not in state:
            state["iteration_count"] = 0

        if "messages" not in state:
            state["messages"] = []

        return state
    
    async def problem_classifier_node(self, state: WorkflowState) -> WorkflowState:
        """
        Problem Classifier Node: Calls the classification API to determine problem type.
        Uses original_user_query for consistent classification regardless of follow-up interactions.
        Skips classification if already completed in previous requests.
        """
        self.logger.info("Problem Classifier Node: Checking if classification needed")

        # Check if classification has already been completed
        context = state.get("context", {})
        existing_problem_type = context.get("problem_type", "")
        existing_suggested_agent = context.get("suggested_agent", "")
        existing_confidence = context.get("confidence", 0.0)

        # If we already have classification results from context, use them
        if existing_problem_type and existing_suggested_agent and existing_confidence > 0:
            self.logger.info(f"🔄 Using existing classification: {existing_problem_type} -> {existing_suggested_agent} (confidence: {existing_confidence})")
            self.logger.info(f"🚫 Skipping API call - using cached classification results from context")
            state["problem_type"] = existing_problem_type
            state["suggested_agent"] = existing_suggested_agent
            state["confidence"] = existing_confidence
            return state

        # NEW: Additional check - if we have suggested_agent in state but no classification in context,
        # this means classification was done but not properly stored in context
        if state.get("suggested_agent") and state.get("problem_type"):
            self.logger.info(f"⚠️ Found partial classification in state - storing in context for consistency")
            state["context"] = state.get("context", {})
            return state

        # Otherwise, perform new classification
        self.logger.info("🔍 Problem Classifier Node: Classifying problem for the first time")

        # Use original_user_query for classification to ensure consistent routing
        # This prevents misclassification when user_query contains follow-up responses or clarifying answers
        classification_query = state.get("original_user_query", state["user_query"])
        self.logger.info(f"📝 Classifying based on: {classification_query[:100]}...")

        try:
            # Call the classification endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/chat_bot/classify-problem",
                    json={"message": classification_query},  # Use original query for classification
                    timeout=30.0
                )

                if response.status_code == 200:
                    result = response.json()
                    state["problem_type"] = result["problem_type"]
                    state["suggested_agent"] = result["suggested_agent"]
                    state["confidence"] = result["confidence"]

                    # Store classification results in context for future requests
                    state["context"] = state.get("context", {})

                    self.logger.info(f"✅ Classified as: {result['problem_type']} -> {result['suggested_agent']} (confidence: {result['confidence']})")
                else:
                    self.logger.error(f"❌ Classification failed: {response.status_code}")
                    state["problem_type"] = "Other"
                    state["suggested_agent"] = "DefaultAgent"
                    state["confidence"] = 0.3

                    # Still store in context to prevent re-classification attempts
                    state["context"] = state.get("context", {})

        except Exception as e:
            self.logger.error(f"❌ Error in classification: {str(e)}")
            state["problem_type"] = "Other"
            state["suggested_agent"] = "DefaultAgent"
            state["confidence"] = 0.3

            # Still store in context to prevent re-classification attempts
            state["context"] = state.get("context", {})

        return state
    
    async def agent_manager_node(self, state: WorkflowState) -> WorkflowState:
        """
        Agent Manager Node: Routes to the appropriate agent.
        """
        # Get the originally selected agent from context to prevent agent switching
        context = state.get("context", {})
        original_agent = context.get("suggested_agent", "")
        original_problem_type = context.get("problem_type", "")

        # Always use the originally selected agent if available
        if original_agent and original_problem_type:
            self.logger.info(f"🔄 Using originally selected agent: {original_problem_type} -> {original_agent}")
            state["suggested_agent"] = original_agent
            state["problem_type"] = original_problem_type
        else:
            self.logger.info(f"⚠️ No original agent found in context, using current state: {state.get('suggested_agent', 'DefaultAgent')}")

        self.logger.info(f"🚀 Agent Manager Node: Routing to {state['suggested_agent']}")

        try:
            # Route to the appropriate agent
            agent_response: AgentResponse = await self.agent_manager.route_to_agent(
                problem_type=state["problem_type"],
                user_query=state["user_query"],
                context=state["context"],
                suggested_agent=state["suggested_agent"],
                original_user_query=state["original_user_query"]
            )
            
            # Update state with agent response
            # Check if this is a final action plan or needs more clarification
            existing_action_plan = state.get("context", {}).get("final_action_plan", "")

            if agent_response.requires_clarification:
                # Agent needs more context - use response_text for intermediate response
                state["response_text"] = agent_response.action_plan  # The "response" goes here
                state["action_plan"] = ""  # Keep action_plan empty until final
                self.logger.info("Agent needs clarification - using response_text")
            elif (agent_response.action_plan and
                  agent_response.action_plan.strip() and
                  not agent_response.requires_clarification and
                  len(agent_response.action_plan.strip()) > 50 and  # Reasonable length
                  state.get("suggested_agent") in ["CultureAgent", "AttritionAgent", "EngagementAgent", "PerformanceAgent", "LeadershipAgent", "ExecutionAgent", "DEIAgent"] and  # Specialized agent only
                  any(keyword in agent_response.action_plan.lower() for keyword in ["##", "###", "**plan", "plan**", "**action", "action**", "**step", "step**"]) and  # Has clear structured plan indicators
                  "thank" not in agent_response.action_plan.lower() and  # Not a thank you
                  not any(keyword in agent_response.action_plan.lower() for keyword in ["understand", "question", "elaborate", "timing"])):  # Not a general response
                # Agent has comprehensive final action plan from specialized agent - use action_plan
                state["action_plan"] = agent_response.action_plan
                state["response_text"] = ""  # Clear response_text

                # Store final action plan in context for future reference
                state["context"] = state.get("context", {})

                self.logger.info("Specialized agent completed with comprehensive action plan - using action_plan")
            elif (agent_response.action_plan and
                  agent_response.action_plan.strip() and
                  len(agent_response.action_plan.strip()) > 50 and
                  state.get("suggested_agent") in ["CultureAgent", "AttritionAgent", "EngagementAgent", "PerformanceAgent", "LeadershipAgent", "ExecutionAgent", "DEIAgent"] and
                  len(state.get("context", {})) >= 3):  # Has substantial context collected
                # Fallback: If specialized agent has substantial context and content, treat as final plan
                state["action_plan"] = agent_response.action_plan
                state["response_text"] = ""

                # Store final action plan in context for future reference
                state["context"] = state.get("context", {})
                state["context"]["final_action_plan"] = agent_response.action_plan

                self.logger.info("Fallback: Specialized agent with substantial context - treating as final action plan")
            else:
                # General response, thank you, or follow-up - use response_text
                state["response_text"] = agent_response.action_plan or "I understand. Is there anything specific you'd like help with?"
                state["action_plan"] = existing_action_plan  # Preserve existing action plan
                self.logger.info("General response or follow-up - using response_text, preserving action_plan")

            state["next_questions"] = agent_response.next_questions
            state["requires_clarification"] = agent_response.requires_clarification
            state["context"] = agent_response.updated_context
            
            self.logger.info(f"Agent response received: clarification_needed={agent_response.requires_clarification}")
        
        except Exception as e:
            self.logger.error(f"Error in agent manager: {str(e)}")
            state["action_plan"] = "An error occurred. Please try again."
            state["next_questions"] = []
            state["requires_clarification"] = False
        
        return state
    
    async def context_collector_node(self, state: WorkflowState) -> WorkflowState:
        """
        Context Collector Node: Handles clarifying questions and context updates.
        """
        self.logger.info("Context Collector Node: Processing context")
        
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        # If clarification is needed, prepare questions for user
        if state.get("requires_clarification", False):
            self.logger.info(f"Clarification needed. Questions: {state['next_questions']}")
        else:
            self.logger.info("No clarification needed, proceeding to knowledge retrieval")
        
        return state
    
    async def knowledge_retrieval_node(self, state: WorkflowState) -> WorkflowState:
        """
        Knowledge Retrieval Node: Fetches relevant information from knowledge base.
        """
        self.logger.info("Knowledge Retrieval Node: Fetching insights")
        
        # TODO: Implement actual vector database query
        # For now, return placeholder insights
        knowledge_insights = f"""
        Retrieved knowledge for {state['problem_type']}:
        - Best practices and industry standards
        - Similar case studies and solutions
        - Relevant research and data
        - Recommended frameworks and methodologies
        """
        
        state["knowledge_insights"] = knowledge_insights
        
        return state
    
    async def llm_response_node(self, state: WorkflowState) -> WorkflowState:
        """
        LLM Response Node: Generates final comprehensive response.
        """
        self.logger.info("LLM Response Node: Generating final response")

        # Check if we have content in action_plan or response_text
        if state.get("action_plan"):
            # The action plan is already generated by the agent
            # This node can enhance or format it if needed

            # Add knowledge insights to the action plan if available
            if state.get("knowledge_insights"):
                enhanced_plan = f"""
{state['action_plan']}
"""
                state["action_plan"] = enhanced_plan
                self.logger.info("Enhanced action_plan with knowledge insights")
            else:
                self.logger.info("Using action_plan as-is (no knowledge insights available)")

        elif state.get("response_text"):
            # We have an intermediate response - enhance it with knowledge insights
            if state.get("knowledge_insights"):
                enhanced_response = f"""
{state['response_text']}
"""
                state["response_text"] = enhanced_response
                self.logger.info("Enhanced response_text with knowledge insights")
            else:
                self.logger.info("Using response_text as-is (no knowledge insights available)")

        else:
            self.logger.info("No content to enhance")

        return state
    
    async def feedback_node(self, state: WorkflowState) -> WorkflowState:
        """
        Feedback Node: Stores user feedback for continuous improvement.
        """
        self.logger.info("Feedback Node: Ready to collect feedback")
        
        # TODO: Implement feedback storage (database, analytics, etc.)
        # For now, just log that we're ready for feedback
        
        state["user_feedback"] = "Feedback collection ready"
        
        return state

    # ==================== CONDITIONAL LOGIC ====================

    def should_continue_or_clarify(self, state: WorkflowState) -> str:
        """
        Determine if we should continue to knowledge retrieval, return for clarification, or complete the conversation.
        """
        # If clarification is needed, return to user
        if state.get("requires_clarification", False):
            self.logger.info("Returning for clarification")
            return "clarify"

        # If we have an action plan and sufficient context, we can continue the conversation
        # but still allow for more interaction before finalizing
        if state.get("action_plan") and state.get("iteration_count", 0) >= 1:
            # Check if we should complete or continue based on context completeness
            required_context_keys = self._get_required_context_for_agent(state.get("suggested_agent", ""))
            current_context_keys = set(state.get("context", {}).keys())

            # If we have most of the required context, continue to allow more conversation
            if len(current_context_keys) >= len(required_context_keys) * 0.7:  # 70% threshold
                self.logger.info("Sufficient context gathered, allowing continued conversation")
                return "continue"

        # If we have a complete action plan but need more context, continue
        if state.get("action_plan") and not state.get("requires_clarification"):
            self.logger.info("Action plan available, continuing conversation")
            return "continue"

        # Otherwise continue to knowledge retrieval
        self.logger.info("Continuing to knowledge retrieval")
        return "continue"

    def _get_required_context_for_agent(self, agent_name: str) -> List[str]:
        """Get required context fields for a specific agent"""
        agent_map = {
            "AttritionAgent": ["team_size", "turnover_rate", "department", "time_period"],
            "EngagementAgent": ["engagement_score", "team_size", "recent_surveys", "main_concerns"],
            "PerformanceAgent": ["performance_metrics", "team_role", "performance_period", "specific_issues"],
            "CultureAgent": ["company_size", "culture_issues", "values", "desired_culture"],
            "LeadershipAgent": ["leadership_level", "development_areas", "succession_planning", "timeline"],
            "ExecutionAgent": ["business_goals", "current_performance", "obstacles", "resources"],
            "DEIAgent": ["diversity_metrics", "dei_initiatives", "specific_concerns", "organizational_commitment"],
            "DefaultAgent": ["problem_type", "specific_details", "urgency"]
        }
        return agent_map.get(agent_name, [])

    # ==================== EXECUTION ====================

    async def execute(self, user_query: str, context: Dict[str, Any] = None, original_query: str = None) -> Dict[str, Any]:
        """
        Execute the workflow with a user query.

        Args:
            user_query: The user's question or problem
            context: Optional existing context
            original_query: The original user query for consistent classification

        Returns:
            Final state with action plan and next steps
        """
        self.logger.info(f"Executing workflow for query: {user_query}")
        self.logger.info(f"Original query: {original_query}")

        # Initialize state
        initial_state: WorkflowState = {
            "user_query": user_query,
            "original_user_query": original_query,  # Use provided original_query or fallback to user_query
            "problem_type": "",
            "suggested_agent": "",
            "confidence": 0.0,
            "context": context or {},
            "action_plan": "",
            "response_text": "",  # Initialize response_text for intermediate responses
            "next_questions": [],
            "requires_clarification": False,
            "knowledge_insights": "",
            "user_feedback": "",
            "iteration_count": 0,
            "messages": []
        }

        if original_query:
            initial_state["original_user_query"] = original_query
            self.logger.info(f"🆕 New conversation - using provided original query: {original_query}")
        else:
            initial_state["original_user_query"] = user_query  # First time execution
            self.logger.info(f"🆕 New conversation - no original query provided, using user query: {user_query}")

        # IMPORTANT: Ensure existing classification is preserved from context
        if context and "suggested_agent" in context and "problem_type" in context:
            initial_state["suggested_agent"] = context["suggested_agent"]
            initial_state["problem_type"] = context["problem_type"]
            initial_state["confidence"] = context.get("confidence", 0.5)
            self.logger.info(f"🔄 Preserving existing classification: {context['problem_type']} -> {context['suggested_agent']}")

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        self.logger.info("Workflow execution complete")

        return final_state


# Singleton instance
_workflow_instance = None

def get_workflow() -> MultiAgentWorkflow:
    """Get or create the workflow singleton"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = MultiAgentWorkflow()
    return _workflow_instance
