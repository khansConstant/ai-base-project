# Multi-Agent System - Quick Start Guide

## 🚀 Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### 2. Setup

```bash
# 1. Set environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Start all services
docker-compose up -d --build

# 3. Check health
curl http://localhost:8000/health
```

### 3. Test the System

#### Test Problem Classification
```bash
curl -X POST http://localhost:8000/api/v1/chat_bot/classify-problem \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Our team has high turnover and people keep leaving"
  }'
```

**Expected Response:**
```json
{
  "problem_type": "Attrition",
  "confidence": 0.95,
  "suggested_agent": "AttritionAgent"
}
```

#### Execute Complete Workflow
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I reduce employee attrition in my engineering team?"
  }'
```

**Expected Response:**
```json
{
  "problem_type": "Attrition",
  "suggested_agent": "AttritionAgent",
  "confidence": 0.95,
  "action_plan": "I need more information to provide a comprehensive attrition analysis.",
  "next_questions": [
    "What is the size of your team or department?",
    "What is your current turnover rate or how many people have left recently?",
    "Which department or team is experiencing attrition?",
    "Over what time period has this attrition occurred?"
  ],
  "requires_clarification": true,
  "context": {},
  "iteration_count": 1
}
```

#### Continue with Context
```bash
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I reduce employee attrition?",
    "context": {
      "team_size": "25",
      "turnover_rate": "30%",
      "department": "Engineering",
      "time_period": "Last 6 months"
    }
  }'
```

## 📊 Available Agents

| Agent | Problem Domain | Use Case |
|-------|---------------|----------|
| **AttritionAgent** | Employee Retention | High turnover, retention strategies |
| **PerformanceAgent** | Performance Management | Low productivity, KPI tracking |
| **EngagementAgent** | Employee Engagement | Low morale, motivation issues |
| **CultureAgent** | Organizational Culture | Culture transformation, values |
| **LeadershipAgent** | Leadership Development | Succession planning, leadership gaps |
| **ExecutionAgent** | Profitability/Execution | Goal achievement, execution issues |
| **DEIAgent** | Diversity & Inclusion | DEI initiatives, fairness concerns |

## 🔄 Workflow Flow

```
1. User submits query
   ↓
2. System classifies problem type
   ↓
3. Routes to appropriate agent
   ↓
4. Agent checks if context is sufficient
   ↓
   ├─→ [Insufficient] → Returns clarifying questions
   │
   └─→ [Sufficient] → Retrieves knowledge
                      ↓
                   Generates action plan
                      ↓
                   Returns to user
```

## 💡 Example Use Cases

### Use Case 1: Attrition Problem

**Query:** "We're losing engineers at an alarming rate"

**Flow:**
1. Classified as "Attrition"
2. AttritionAgent asks for: team_size, turnover_rate, department, time_period
3. User provides context
4. Agent generates retention strategy with specific action items

### Use Case 2: Performance Issue

**Query:** "My team is not meeting their sales targets"

**Flow:**
1. Classified as "Performance"
2. PerformanceAgent asks for: metrics, roles, period, specific issues
3. User provides context
4. Agent creates performance improvement plan

### Use Case 3: Engagement Problem

**Query:** "Employees seem unmotivated and disengaged"

**Flow:**
1. Classified as "Engagement"
2. EngagementAgent asks for: engagement scores, surveys, concerns
3. User provides context
4. Agent recommends engagement initiatives

## 🛠️ Testing Each Agent

### Test AttritionAgent
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "High employee turnover in sales team",
    "context": {
      "team_size": "15",
      "turnover_rate": "40%",
      "department": "Sales",
      "time_period": "Q1 2024"
    }
  }'
```

### Test PerformanceAgent
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Team missing performance targets",
    "context": {
      "performance_metrics": "Sales quota, customer satisfaction",
      "team_role": "Account Executives",
      "performance_period": "Last quarter",
      "specific_issues": "20% below target"
    }
  }'
```

### Test EngagementAgent
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Low employee engagement scores",
    "context": {
      "engagement_score": "3.2/5",
      "team_size": "50",
      "recent_surveys": "Annual survey completed",
      "main_concerns": "Work-life balance, recognition"
    }
  }'
```

### Test LeadershipAgent
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Need to develop future leaders",
    "context": {
      "leadership_level": "Middle management",
      "development_areas": "Strategic thinking, communication",
      "succession_planning": "Yes, for VP role",
      "timeline": "12 months"
    }
  }'
```

## 📚 API Documentation

Visit the interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Debugging

### Check Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
```

### Check Agent List
```bash
curl http://localhost:8000/api/v1/workflow/agents
```

### Verify Classification
```bash
curl -X POST http://localhost:8000/api/v1/chat_bot/classify-problem \
  -H "Content-Type: application/json" \
  -d '{"message": "Your test query here"}'
```

## 🎯 Key Features

✅ **Automatic Problem Classification** - AI classifies workplace issues  
✅ **Dynamic Agent Routing** - Routes to specialized domain experts  
✅ **Context-Aware** - Asks clarifying questions when needed  
✅ **Structured Outputs** - Consistent JSON responses  
✅ **Iterative Refinement** - Supports multi-turn conversations  
✅ **Knowledge Integration** - Placeholder for vector DB integration  
✅ **Modular Design** - Easy to add new agents  

## 📝 Response Structure

Every agent returns:
```json
{
  "action_plan": "Detailed recommendations",
  "next_questions": ["Question 1", "Question 2"],
  "updated_context": {"key": "value"},
  "confidence": 0.85,
  "requires_clarification": false
}
```

## 🚨 Common Issues

**Issue**: "OpenAI API error"  
**Solution**: Check your OPENAI_API_KEY in .env file

**Issue**: "Agent not found"  
**Solution**: Verify problem_type matches available agents

**Issue**: "Clarification loop"  
**Solution**: Ensure you're providing all required context fields

## 📖 Full Documentation

For complete documentation, see:
- `MULTI_AGENT_SYSTEM.md` - Complete system documentation
- `GETTING_STARTED.md` - General FastAPI setup
- `/docs` - Interactive API documentation

## 🎉 You're Ready!

Your multi-agent AI system is now running. Start by:
1. Testing the classification endpoint
2. Executing a simple workflow
3. Trying different problem types
4. Exploring the interactive docs at `/docs`

Happy building! 🚀
