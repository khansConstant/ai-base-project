# Multi-Agent AI System Documentation

## Overview

This is a comprehensive multi-agent AI system built with **FastAPI**, **LangGraph**, **Celery**, and **OpenAI API** to solve workplace and manager-related problems.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Endpoints                           │
│  /workflow/execute  │  /workflow/continue  │  /chat_bot/*       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                          │
│                                                                   │
│  Input → Classifier → AgentManager → ContextCollector →         │
│  Knowledge → LLMResponse → Feedback → Output                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Agent Manager                              │
│              (Routes to Specialized Agents)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Attrition   │    │ Performance  │    │  Engagement  │
│    Agent     │    │    Agent     │    │    Agent     │
└──────────────┘    └──────────────┘    └──────────────┘
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Culture    │    │  Leadership  │    │  Execution   │
│    Agent     │    │    Agent     │    │    Agent     │
└──────────────┘    └──────────────┘    └──────────────┘
        ▼
┌──────────────┐
│     DEI      │
│    Agent     │
└──────────────┘
```

## Agent Classes

### Base Agent

All agents inherit from `BaseAgent` which provides:
- `run_agent(user_query, context)` - Main execution method
- `check_clarification_needed(context)` - Validates required context
- `generate_clarifying_questions(context)` - Creates questions for missing info
- `get_required_context_fields()` - Defines required context fields

### Specialized Agents

#### 1. **AttritionAgent**
- **Domain**: Employee Attrition and Retention
- **Required Context**: team_size, turnover_rate, department, time_period
- **Focus**: Analyzing turnover patterns, retention strategies

#### 2. **PerformanceAgent**
- **Domain**: Employee Performance Management
- **Required Context**: performance_metrics, team_role, performance_period, specific_issues
- **Focus**: Performance improvement plans, KPI tracking

#### 3. **EngagementAgent**
- **Domain**: Employee Engagement
- **Required Context**: engagement_score, team_size, recent_surveys, main_concerns
- **Focus**: Motivation, satisfaction, engagement initiatives

#### 4. **CultureAgent**
- **Domain**: Organizational Culture
- **Required Context**: company_size, culture_issues, values, desired_culture
- **Focus**: Culture transformation, values alignment

#### 5. **LeadershipAgent**
- **Domain**: Leadership Development
- **Required Context**: leadership_level, development_areas, succession_planning, timeline
- **Focus**: Leadership readiness, succession planning

#### 6. **ExecutionAgent**
- **Domain**: Profitability and Execution
- **Required Context**: business_goals, current_performance, obstacles, resources
- **Focus**: Goal achievement, execution strategies

#### 7. **DEIAgent**
- **Domain**: Diversity, Equity, and Inclusion
- **Required Context**: diversity_metrics, dei_initiatives, specific_concerns, organizational_commitment
- **Focus**: DEI programs, inclusive practices

## LangGraph Workflow

### Nodes

1. **InputNode**: Initializes workflow with user query
2. **ProblemClassifierNode**: Classifies problem type using OpenAI
3. **AgentManagerNode**: Routes to appropriate specialized agent
4. **ContextCollectorNode**: Handles clarifying questions
5. **KnowledgeRetrievalNode**: Queries knowledge base (placeholder)
6. **LLMResponseNode**: Generates final action plan
7. **FeedbackNode**: Collects user feedback

### Data Flow

```
User Query
    ↓
Input Node (initialize state)
    ↓
Problem Classifier (classify problem type)
    ↓
Agent Manager (route to correct agent)
    ↓
Context Collector (check if clarification needed)
    ↓
    ├─→ [If clarification needed] → Return to User
    │
    └─→ [If context complete] → Knowledge Retrieval
                                      ↓
                                LLM Response (enhance action plan)
                                      ↓
                                Feedback Node
                                      ↓
                                Return to User
```

### State Schema

```python
class WorkflowState(TypedDict):
    user_query: str
    problem_type: str
    suggested_agent: str
    confidence: float
    context: Dict[str, Any]
    action_plan: str
    next_questions: list
    requires_clarification: bool
    knowledge_insights: str
    feedback: str
    iteration_count: int
    messages: list
```

## API Endpoints

### 1. Execute Workflow

**POST** `/api/v1/workflow/execute`

Execute the complete multi-agent workflow.

**Request:**
```json
{
  "user_query": "Our team has high turnover and people keep leaving",
  "context": {},
  "user_id": "user123",
  "session_id": "session456"
}
```

**Response:**
```json
{
  "problem_type": "Attrition",
  "suggested_agent": "AttritionAgent",
  "confidence": 0.95,
  "action_plan": "Based on your attrition issue...",
  "next_questions": [
    "What is the size of your team?",
    "What is your current turnover rate?"
  ],
  "requires_clarification": true,
  "context": {},
  "iteration_count": 1
}
```

### 2. Continue Workflow

**POST** `/api/v1/workflow/continue`

Continue workflow with updated context after user answers questions.

**Request:**
```json
{
  "user_query": "Our team has high turnover",
  "context": {
    "team_size": "25",
    "turnover_rate": "30%",
    "department": "Engineering",
    "time_period": "Last 6 months"
  }
}
```

**Response:**
```json
{
  "problem_type": "Attrition",
  "suggested_agent": "AttritionAgent",
  "confidence": 0.95,
  "action_plan": "Comprehensive 5-step retention strategy...",
  "next_questions": [],
  "requires_clarification": false,
  "context": {...},
  "iteration_count": 2
}
```

### 3. List Available Agents

**GET** `/api/v1/workflow/agents`

Get list of all available agents.

**Response:**
```json
{
  "agents": [
    "Attrition",
    "Engagement",
    "Performance",
    "Culture",
    "Leadership Readiness",
    "Profitability/Execution",
    "DEI/Fairness"
  ],
  "count": 7
}
```

### 4. Classify Problem

**POST** `/api/v1/chat_bot/classify-problem`

Classify a workplace problem into categories.

**Request:**
```json
{
  "message": "Our employees seem unmotivated and disengaged",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "problem_type": "Engagement",
  "confidence": 0.92,
  "suggested_agent": "EngagementAgent"
}
```

## Agent Response Structure

All agents return a structured response:

```json
{
  "action_plan": "Detailed step-by-step action plan with specific recommendations",
  "next_questions": [
    "Question 1 for more context",
    "Question 2 for clarification"
  ],
  "updated_context": {
    "field1": "value1",
    "field2": "value2"
  },
  "confidence": 0.85,
  "requires_clarification": false
}
```

## Usage Examples

### Example 1: Simple Query (No Clarification Needed)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I improve team performance with clear KPIs?",
    "context": {
      "performance_metrics": "Sales targets, customer satisfaction",
      "team_role": "Sales team",
      "performance_period": "Q4 2024",
      "specific_issues": "Missing targets by 20%"
    }
  }'
```

### Example 2: Query Requiring Clarification

```bash
# First request
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "We have high employee turnover"
  }'

# Response will include next_questions and requires_clarification: true

# Second request with context
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "We have high employee turnover",
    "context": {
      "team_size": "50",
      "turnover_rate": "25%",
      "department": "Customer Support",
      "time_period": "Last year"
    }
  }'
```

## File Structure

```
app/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py           # Base agent class
│   ├── agent_manager.py        # Agent routing logic
│   ├── attrition_agent.py      # Attrition specialist
│   ├── performance_agent.py    # Performance specialist
│   ├── engagement_agent.py     # Engagement specialist
│   ├── culture_agent.py        # Culture specialist
│   ├── leadership_agent.py     # Leadership specialist
│   ├── execution_agent.py      # Execution specialist
│   └── dei_agent.py            # DEI specialist
├── graph/
│   ├── __init__.py
│   └── workflow.py             # LangGraph workflow
├── api/v1/endpoints/
│   ├── workflow.py             # Workflow API endpoints
│   └── chat_bot.py             # Classification endpoint
└── main.py                     # FastAPI app
```

## Environment Variables

Add to your `.env` file:

```bash
# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here

# Application
APP_NAME=Multi-Agent AI System
APP_ENV=development
DEBUG=True

# Celery & Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Testing the System

### 1. Start the services
```bash
docker-compose up -d --build
```

### 2. Check health
```bash
curl http://localhost:8000/health
```

### 3. List available agents
```bash
curl http://localhost:8000/api/v1/workflow/agents
```

### 4. Execute a workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I reduce employee attrition in my engineering team?"
  }'
```

### 5. View API docs
Visit: http://localhost:8000/docs

## Extending the System

### Adding a New Agent

1. Create a new agent file in `app/agents/`:

```python
from .base_agent import BaseAgent, AgentResponse

class NewAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="NewAgent", problem_domain="New Domain")
    
    def get_required_context_fields(self) -> List[str]:
        return ["field1", "field2"]
    
    def generate_clarifying_questions(self, context: Dict[str, Any]) -> List[str]:
        # Generate questions
        pass
    
    async def run_agent(self, user_query: str, context: Dict[str, Any]) -> AgentResponse:
        # Agent logic
        pass
```

2. Register in `agent_manager.py`:

```python
self.agents["NewProblemType"] = NewAgent()
```

3. Update the classifier to recognize the new problem type.

### Adding Knowledge Base Integration

Replace the placeholder in `knowledge_retrieval_node`:

```python
async def knowledge_retrieval_node(self, state: WorkflowState) -> WorkflowState:
    # Query vector database
    from your_vector_db import query_knowledge
    
    insights = await query_knowledge(
        query=state["user_query"],
        problem_type=state["problem_type"],
        top_k=5
    )
    
    state["knowledge_insights"] = insights
    return state
```

## Best Practices

1. **Context Management**: Always validate and update context through the workflow
2. **Error Handling**: Each node should handle errors gracefully
3. **Logging**: Use structured logging for debugging
4. **Iterative Refinement**: Support multiple clarification rounds
5. **Feedback Loop**: Collect and store user feedback for improvement

## Troubleshooting

### Issue: Agent not found
- Check that the problem_type matches an agent key in `agent_manager.py`
- Verify the classifier is returning valid problem types

### Issue: Clarification loop
- Ensure context fields are being properly updated
- Check `check_clarification_needed()` logic

### Issue: OpenAI API errors
- Verify OPENAI_API_KEY is set correctly
- Check API rate limits and quotas
- Review structured output schema compatibility

## Performance Considerations

- **Caching**: Cache agent responses for similar queries
- **Async Operations**: All nodes use async/await for non-blocking I/O
- **Rate Limiting**: Implement rate limiting for OpenAI API calls
- **Session Management**: Store context in Redis for multi-turn conversations

## Security

- Never expose OpenAI API keys in responses
- Validate and sanitize all user inputs
- Implement authentication for production use
- Use HTTPS in production
- Rate limit API endpoints

---

**System Status**: ✅ Fully Operational

For questions or issues, check the logs or API documentation at `/docs`.
