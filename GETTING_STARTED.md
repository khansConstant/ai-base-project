# Getting Started with FastAPI Skeleton

This guide will help you get started with your new FastAPI skeleton project.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start all services with Docker:**
   ```bash
   docker-compose up -d --build
   ```

3. **Verify everything is running:**
   - API: http://localhost:8000/health
   - API Docs: http://localhost:8000/docs
   - Flower (Celery Monitor): http://localhost:5556

## Project Structure

```
ai-chatbot/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── example.py      # Example API endpoints
│   ├── config/
│   │   └── settings.py             # Application settings
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── example_tasks.py        # Example Celery tasks
│   ├── celery_config.py            # Celery configuration
│   └── main.py                     # FastAPI application
├── docker-compose.yml              # Docker services configuration
├── Dockerfile                      # Docker image configuration
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment variables template
```

## Testing the Example Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Get All Items (GET)
```bash
curl http://localhost:8000/api/v1/example/
```

### 3. Get Single Item (GET with path parameter)
```bash
curl http://localhost:8000/api/v1/example/1
```

### 4. Create Item (POST)
```bash
curl -X POST http://localhost:8000/api/v1/example/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "value": 42}'
```

### 5. Trigger Background Task
```bash
curl -X POST http://localhost:8000/task/example \
  -H "Content-Type: application/json" \
  -d '{"x": 10, "y": 20}'
```

## Customizing Your Project

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/`:
   ```python
   # app/api/v1/endpoints/users.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/users", tags=["users"])
   
   @router.get("/")
   async def get_users():
       return {"users": []}
   ```

2. Include the router in `app/main.py`:
   ```python
   from .api.v1.endpoints import example, users
   
   app.include_router(users.router, prefix="/api/v1")
   ```

### Adding Background Tasks

1. Create task functions in `app/tasks/`:
   ```python
   # app/tasks/email_tasks.py
   from ..celery_config import celery_app
   
   @celery_app.task(name="send_email")
   def send_email(to: str, subject: str, body: str):
       # Your email sending logic here
       pass
   ```

2. Call the task from your endpoints:
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

### Adding Database Support

1. Uncomment database dependencies in `requirements.txt`:
   ```txt
   sqlalchemy==2.0.23
   psycopg2-binary==2.9.9
   alembic==1.12.1
   ```

2. Add database service to `docker-compose.yml`:
   ```yaml
   postgres:
     image: postgres:15-alpine
     environment:
       POSTGRES_USER: user
       POSTGRES_PASSWORD: password
       POSTGRES_DB: your_db
     ports:
       - "5432:5432"
     volumes:
       - postgres_data:/var/lib/postgresql/data
   ```

3. Create database connection in `app/database/base.py`

4. Update `DATABASE_URL` in `.env`

## Development Tips

### Running Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Run API
uvicorn app.main:app --reload

# Run Celery worker (in another terminal)
celery -A app.celery_config.celery_app worker --loglevel=info

# Run Flower (optional)
celery -A app.celery_config.celery_app flower --port=5555
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
```

### Stopping Services

```bash
docker-compose down
```

### Rebuilding After Changes

```bash
docker-compose up -d --build
```

## Next Steps

1. **Update the project name** in `README.md` and `docker-compose.yml`
2. **Configure CORS** in `app/main.py` for your frontend domain
3. **Add authentication** if needed (JWT, OAuth, etc.)
4. **Set up a database** if your project requires persistence
5. **Add tests** using pytest
6. **Configure CI/CD** for automated deployments
7. **Update security settings** in `.env` for production

## Common Issues

### Port Already in Use
If port 8000 or 6379 is already in use, update the ports in `docker-compose.yml`

### Celery Tasks Not Running
- Check if Redis is running: `docker-compose ps`
- Check Celery worker logs: `docker-compose logs celery_worker`
- Verify task name matches in decorator and when calling

### Import Errors
- Make sure you're using relative imports in the `app/` directory
- Verify `PYTHONPATH` is set correctly in Dockerfile

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Support

For issues or questions, please check the documentation or create an issue in your repository.
