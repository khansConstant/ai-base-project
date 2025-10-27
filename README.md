# FastAPI Base Project

A clean and minimal FastAPI base project with Docker, Redis, Celery, and async support - ready for you to build upon.

## Features

- 🚀 FastAPI backend with async support
- 🐳 Docker and Docker Compose for development
- 📦 Redis for caching and message broker
- ⚡ Celery for background task processing
- 🌸 Flower for Celery monitoring
- 🔧 Environment-based configuration
- 📚 Auto-generated API documentation (Swagger UI & ReDoc)
- 🎯 CORS middleware configured
- ✅ Health check endpoint
- 📝 Example API endpoints and background tasks

## Prerequisites

- Docker and Docker Compose
- Python 3.11+

## Getting Started

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Update the `.env` file with your configuration.**

3. **Build and start the services:**
   ```bash
   # Start only API and Redis (default)
   docker-compose up -d --build

   # Start all services including Celery (if you want background tasks)
   docker-compose --profile celery up -d --build
   ```

4. **Access the services:**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Flower (Celery Monitor): http://localhost:5556 *(optional, only if using Celery)*

## Project Structure

```
app/
├── api/
│   └── v1/
│       └── endpoints/
│           └── example.py      # Example API endpoints
├── config/
│   └── settings.py             # Application settings
├── tasks/
│   └── example_tasks.py        # Example Celery tasks
├── celery_config.py            # Celery configuration
└── main.py                     # FastAPI application entry point
```

## API Endpoints

### Health Check
- `GET /health` - Check API health status

### Example Endpoints
- `GET /api/v1/example/` - Get all items
- `GET /api/v1/example/{item_id}` - Get item by ID
- `POST /api/v1/example/` - Create a new item

### Background Tasks
- `POST /task/example` - Trigger example background task *(requires Celery setup)*

## Development

### Running Without Docker

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Redis (required):
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Run Celery worker *(optional - only if using background tasks)*:
   ```bash
   celery -A app.celery_config.celery_app worker --loglevel=info
   ```

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/`:
   ```python
   from fastapi import APIRouter

   router = APIRouter(prefix="/users", tags=["users"])

   @router.get("/")
   async def get_users():
       return {"users": []}
   ```

2. Include the router in `app/main.py`:
   ```python
   from .api.v1.endpoints import router as example_router
   from .api.v1.endpoints.users import router as users_router

   app.include_router(example_router, prefix="/api/v1")
   app.include_router(users_router, prefix="/api/v1")
   ```

### Adding Background Tasks *(Optional - requires Celery setup)*

1. Install Celery dependencies:
   ```bash
   pip install celery redis
   ```

2. Create task functions in `app/tasks/`:
   ```python
   # app/tasks/email_tasks.py
   from ..celery_config import celery_app

   @celery_app.task(name="send_email")
   def send_email(to: str, subject: str, body: str):
       # Your email sending logic here
       pass
   ```

3. Call the task from your endpoints:
   ```python
   from app.tasks.email_tasks import send_email

   @router.post("/send-email")
   async def trigger_email(email_data: dict):
       task = send_email.delay(
           email_data["to"],
           email_data["subject"],
           email_data["body"]
       )
       return {"task_id": str(task.id)}
   ```

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT
