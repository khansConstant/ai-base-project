# API Request Examples - Multi-Agent System

## 🎯 Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/workflow/execute` | POST | Start a new workflow |
| `/api/v1/workflow/continue` | POST | Continue with updated context |
| `/api/v1/workflow/agents` | GET | List available agents |
| `/api/v1/chat_bot/classify-problem` | POST | Classify problem only |

---

## 1️⃣ Execute Workflow (Main Endpoint)

**Endpoint:** `POST /api/v1/workflow/execute`

**Use this when:** You want to start a new conversation or problem-solving session.

### Request Format

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Your question here",
    "context": {},
    "user_id": "optional_user_id",
    "session_id": "optional_session_id"
  }'
```

### Example 1: Simple Query (No Context)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Our team has high employee turnover"
  }'
```

**Response:**
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

### Example 2: Query with Complete Context

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
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

**Response:**
```json
{
  "problem_type": "Attrition",
  "suggested_agent": "AttritionAgent",
  "confidence": 0.95,
  "action_plan": "Based on your 30% turnover rate in Engineering...\n\n1. Conduct exit interviews...\n2. Review compensation...\n3. Implement retention programs...",
  "next_questions": [],
  "requires_clarification": false,
  "context": {
    "team_size": "25",
    "turnover_rate": "30%",
    "department": "Engineering",
    "time_period": "Last 6 months"
  },
  "iteration_count": 1
}
```

### Python Example

```python
import requests

url = "http://localhost:8000/api/v1/workflow/execute"

payload = {
    "user_query": "Our team has high employee turnover",
    "context": {
        "team_size": "25",
        "turnover_rate": "30%",
        "department": "Engineering",
        "time_period": "Last 6 months"
    },
    "user_id": "user123"
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Problem Type: {result['problem_type']}")
print(f"Action Plan: {result['action_plan']}")
print(f"Needs Clarification: {result['requires_clarification']}")
```

### JavaScript Example

```javascript
const response = await fetch('http://localhost:8000/api/v1/workflow/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    user_query: "Our team has high employee turnover",
    context: {
      team_size: "25",
      turnover_rate: "30%",
      department: "Engineering",
      time_period: "Last 6 months"
    }
  })
});

const result = await response.json();
console.log('Problem Type:', result.problem_type);
console.log('Action Plan:', result.action_plan);
```

---

## 2️⃣ Continue Workflow

**Endpoint:** `POST /api/v1/workflow/continue`

**Use this when:** The system asked clarifying questions and you want to provide answers.

### Request Format

```bash
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Original query",
    "context": {
      "field1": "answer1",
      "field2": "answer2"
    }
  }'
```

### Example: Two-Step Conversation

**Step 1: Initial Request**
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I improve team performance?"
  }'
```

**Response from Step 1:**
```json
{
  "requires_clarification": true,
  "next_questions": [
    "What specific performance metrics or KPIs are you tracking?",
    "What is the role or position of the employee(s) in question?",
    "Over what time period have you observed these performance issues?",
    "What specific performance issues have you noticed?"
  ]
}
```

**Step 2: Continue with Answers**
```bash
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can I improve team performance?",
    "context": {
      "performance_metrics": "Sales targets and customer satisfaction scores",
      "team_role": "Sales representatives",
      "performance_period": "Last quarter",
      "specific_issues": "Missing sales targets by 20%"
    }
  }'
```

**Response from Step 2:**
```json
{
  "requires_clarification": false,
  "action_plan": "Comprehensive performance improvement plan...",
  "next_questions": []
}
```

### Python Example: Multi-Turn Conversation

```python
import requests

url_execute = "http://localhost:8000/api/v1/workflow/execute"
url_continue = "http://localhost:8000/api/v1/workflow/continue"

# Step 1: Initial query
response1 = requests.post(url_execute, json={
    "user_query": "How can I improve team performance?"
})
result1 = response1.json()

if result1['requires_clarification']:
    print("Questions to answer:")
    for q in result1['next_questions']:
        print(f"  - {q}")
    
    # Step 2: Provide answers
    response2 = requests.post(url_continue, json={
        "user_query": "How can I improve team performance?",
        "context": {
            "performance_metrics": "Sales targets",
            "team_role": "Sales team",
            "performance_period": "Q4 2024",
            "specific_issues": "Missing targets by 20%"
        }
    })
    result2 = response2.json()
    print(f"\nAction Plan: {result2['action_plan']}")
```

---

## 3️⃣ List Available Agents

**Endpoint:** `GET /api/v1/workflow/agents`

**Use this when:** You want to see all available specialized agents.

### Request Format

```bash
curl http://localhost:8000/api/v1/workflow/agents
```

### Response

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

### Python Example

```python
import requests

response = requests.get("http://localhost:8000/api/v1/workflow/agents")
agents = response.json()

print(f"Available agents ({agents['count']}):")
for agent in agents['agents']:
    print(f"  - {agent}")
```

---

## 4️⃣ Classify Problem Only

**Endpoint:** `POST /api/v1/chat_bot/classify-problem`

**Use this when:** You only want to classify the problem without executing the full workflow.

### Request Format

```bash
curl -X POST http://localhost:8000/api/v1/chat_bot/classify-problem \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your problem description",
    "user_id": "optional_user_id"
  }'
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/chat_bot/classify-problem \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Our employees seem unmotivated and disengaged"
  }'
```

### Response

```json
{
  "problem_type": "Engagement",
  "confidence": 0.92,
  "suggested_agent": "EngagementAgent"
}
```

---

## 🎯 Complete Workflow Examples

### Example 1: Attrition Problem

```bash
# Full context provided upfront
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "We are experiencing high turnover in our sales team",
    "context": {
      "team_size": "15",
      "turnover_rate": "40%",
      "department": "Sales",
      "time_period": "Last 6 months"
    },
    "user_id": "manager_123"
  }'
```

### Example 2: Performance Issue

```bash
# No context - will ask questions
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "My team is not meeting their targets"
  }'

# Then continue with context
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "My team is not meeting their targets",
    "context": {
      "performance_metrics": "Monthly sales quota",
      "team_role": "Account Executives",
      "performance_period": "Q1 2024",
      "specific_issues": "20% below quota"
    }
  }'
```

### Example 3: Leadership Development

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Need to prepare managers for senior leadership roles",
    "context": {
      "leadership_level": "Middle management",
      "development_areas": "Strategic thinking, executive presence",
      "succession_planning": "Yes, for VP positions",
      "timeline": "18 months"
    }
  }'
```

### Example 4: DEI Initiative

```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "How can we improve diversity in our hiring?",
    "context": {
      "diversity_metrics": "15% women, 10% minorities",
      "dei_initiatives": "Unconscious bias training",
      "specific_concerns": "Low representation in tech roles",
      "organizational_commitment": "High - CEO priority"
    }
  }'
```

---

## 🔄 Decision Flow: Which Endpoint to Use?

```
START
  ↓
Do you just want to classify the problem?
  ├─ YES → Use: /chat_bot/classify-problem
  └─ NO ↓
  
Is this a new conversation?
  ├─ YES → Use: /workflow/execute
  └─ NO ↓
  
Did the system ask clarifying questions?
  ├─ YES → Use: /workflow/continue (with updated context)
  └─ NO → Use: /workflow/execute (new query)
```

---

## 📱 Testing with Different Tools

### Using cURL (Command Line)
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{"user_query": "Your query here"}'
```

### Using Postman
1. Method: POST
2. URL: `http://localhost:8000/api/v1/workflow/execute`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "user_query": "Your query here",
  "context": {}
}
```

### Using Python requests
```python
import requests
response = requests.post(
    "http://localhost:8000/api/v1/workflow/execute",
    json={"user_query": "Your query here"}
)
print(response.json())
```

### Using JavaScript fetch
```javascript
fetch('http://localhost:8000/api/v1/workflow/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_query: "Your query here"})
})
.then(r => r.json())
.then(data => console.log(data));
```

### Using HTTPie
```bash
http POST localhost:8000/api/v1/workflow/execute \
  user_query="Your query here"
```

---

## 🎨 Interactive API Documentation

The easiest way to test all endpoints is through the interactive docs:

**Swagger UI:** http://localhost:8000/docs

1. Click on any endpoint
2. Click "Try it out"
3. Fill in the request body
4. Click "Execute"
5. See the response

---

## 🚨 Common Mistakes

### ❌ Wrong: Missing Content-Type header
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -d '{"user_query": "test"}'
```

### ✅ Correct: Include Content-Type
```bash
curl -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{"user_query": "test"}'
```

### ❌ Wrong: Using /continue without context
```bash
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{"user_query": "test"}'
```

### ✅ Correct: Include context in /continue
```bash
curl -X POST http://localhost:8000/api/v1/workflow/continue \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "test",
    "context": {"field": "value"}
  }'
```

---

## 📊 Response Fields Explained

| Field | Type | Description |
|-------|------|-------------|
| `problem_type` | string | Classified problem category |
| `suggested_agent` | string | Which agent handled the request |
| `confidence` | float | Classification confidence (0-1) |
| `action_plan` | string | Detailed recommendations |
| `next_questions` | array | Questions for clarification |
| `requires_clarification` | boolean | If true, use /continue endpoint |
| `context` | object | Current conversation context |
| `iteration_count` | integer | Number of workflow iterations |

---

## 🎯 Quick Test Script

Save this as `test_workflow.sh`:

```bash
#!/bin/bash

echo "Testing Multi-Agent Workflow System"
echo "===================================="

# Test 1: Health check
echo -e "\n1. Health Check"
curl -s http://localhost:8000/health | jq

# Test 2: List agents
echo -e "\n2. Available Agents"
curl -s http://localhost:8000/api/v1/workflow/agents | jq

# Test 3: Classify problem
echo -e "\n3. Classify Problem"
curl -s -X POST http://localhost:8000/api/v1/chat_bot/classify-problem \
  -H "Content-Type: application/json" \
  -d '{"message": "High employee turnover"}' | jq

# Test 4: Execute workflow
echo -e "\n4. Execute Workflow"
curl -s -X POST http://localhost:8000/api/v1/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{"user_query": "How to reduce attrition?"}' | jq

echo -e "\n✅ All tests completed!"
```

Run with: `chmod +x test_workflow.sh && ./test_workflow.sh`

---

## 📖 Need More Help?

- **Full Documentation**: See `MULTI_AGENT_SYSTEM.md`
- **Interactive Docs**: Visit http://localhost:8000/docs
- **Quick Start**: See `QUICK_START_AGENTS.md`

---

**Summary:** Use `/workflow/execute` for new queries, `/workflow/continue` when answering clarifying questions! 🚀
