# FastAPI Skeleton - Quick Reference Card

## 🚀 Quick Start Commands

```bash
# Setup
cp .env.example .env

# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📍 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main API |
| Swagger Docs | http://localhost:8000/docs | Interactive API documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API documentation |
| Flower | http://localhost:5556 | Celery task monitor |
| Redis | localhost:6379 | Message broker |

## 🔌 Available Endpoints

### Health & Status
```bash
GET /health
# Returns: {"status": "healthy", "app_name": "...", "environment": "..."}
```

### Example CRUD Operations
```bash
# Get all items
GET /api/v1/example/

# Get single item
GET /api/v1/example/{item_id}

# Create item
POST /api/v1/example/
Body: {"name": "string", "value": 123}
```

### Background Tasks
```bash
# Trigger example task
POST /task/example
Body: {"x": 10, "y": 20}
# Returns: {"message": "...", "task_id": "...", "status": "pending"}
```

## 📝 Code Templates

### Add New Endpoint

```python
# app/api/v1/endpoints/your_endpoint.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/your-resource", tags=["your-resource"])

class YourModel(BaseModel):
    name: str
    value: int

@router.get("/")
async def get_items():
    return {"items": []}

@router.post("/")
async def create_item(item: YourModel):
    return {"message": "Created", "data": item.dict()}
```

Then include in `app/main.py`:
```python
from .api.v1.endpoints import example, your_endpoint
app.include_router(your_endpoint.router, prefix="/api/v1")
```

### Add New Background Task

```python
# app/tasks/your_tasks.py
from ..celery_config import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="your_task_name")
def your_task(param1: str, param2: int):
    logger.info(f"Task started with {param1}, {param2}")
    # Your logic here
    result = f"Processed {param1}"
    logger.info(f"Task completed: {result}")
    return result
```

Call from endpoint:
```python
from app.tasks.your_tasks import your_task

@router.post("/trigger")
async def trigger_task(data: dict):
    task = your_task.delay(data["param1"], data["param2"])
    return {"task_id": str(task.id)}
```

### Add Configuration Setting

```python
# app/config/settings.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Your new setting
    YOUR_API_KEY: str = os.getenv("YOUR_API_KEY", "")
    YOUR_SETTING: int = int(os.getenv("YOUR_SETTING", 100))
```

Add to `.env.example`:
```bash
# Your Service
YOUR_API_KEY=your-key-here
YOUR_SETTING=100
```

## 🐳 Docker Commands

```bash
# Build and start
docker-compose up -d --build

# Restart specific service
docker-compose restart api

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
docker-compose logs -f flower

# Execute command in container
docker-compose exec api python -c "print('Hello')"

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 🔧 Development Commands

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run API locally (needs Redis)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker locally
celery -A app.celery_config.celery_app worker --loglevel=info

# Run Flower locally
celery -A app.celery_config.celery_app flower --port=5555

# Check Python syntax
python3 -m py_compile app/**/*.py

# Format code (if black installed)
black app/

# Lint code (if flake8 installed)
flake8 app/
```

## 📦 Common Dependencies to Add

```bash
# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9      # PostgreSQL
alembic==1.12.1             # Migrations

# Authentication
python-jose[cryptography]
passlib[bcrypt]
python-multipart

# Testing
pytest
pytest-asyncio
httpx

# Utilities
requests
aiohttp
python-dateutil
```

## 🔍 Debugging Tips

### Check if services are running
```bash
docker-compose ps
```

### Check Redis connection
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Check Celery tasks
```bash
# In Python shell
from app.celery_config import celery_app
celery_app.control.inspect().active()
```

### View all registered tasks
```bash
docker-compose exec celery_worker celery -A app.celery_config.celery_app inspect registered
```

## 🌐 CURL Test Commands

```bash
# Health check
curl http://localhost:8000/health

# Get items
curl http://localhost:8000/api/v1/example/

# Get single item
curl http://localhost:8000/api/v1/example/1

# Create item
curl -X POST http://localhost:8000/api/v1/example/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "value": 100}'

# Trigger background task
curl -X POST http://localhost:8000/task/example \
  -H "Content-Type: application/json" \
  -d '{"x": 5, "y": 10}'
```

## 📂 File Locations

| What | Where |
|------|-------|
| API Endpoints | `app/api/v1/endpoints/` |
| Background Tasks | `app/tasks/` |
| Configuration | `app/config/settings.py` |
| Main App | `app/main.py` |
| Celery Config | `app/celery_config.py` |
| Dependencies | `requirements.txt` |
| Environment Vars | `.env` (create from `.env.example`) |
| Docker Config | `docker-compose.yml` |

## 🎯 Common Patterns

### Dependency Injection
```python
from fastapi import Depends
from app.config.settings import get_settings

@router.get("/")
async def endpoint(settings = Depends(get_settings)):
    return {"env": settings.APP_ENV}
```

### Error Handling
```python
from fastapi import HTTPException, status

@router.get("/{item_id}")
async def get_item(item_id: int):
    if item_id < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID"
        )
    return {"id": item_id}
```

### Response Models
```python
from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    id: int
    name: str

@router.get("/", response_model=List[Item])
async def get_items():
    return [{"id": 1, "name": "Item 1"}]
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Update CORS origins in `app/main.py`
- [ ] Use environment variables for sensitive data
- [ ] Never commit `.env` file
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Validate all inputs
- [ ] Use secure password hashing
- [ ] Keep dependencies updated

## 📚 Documentation

- Full guide: `GETTING_STARTED.md`
- Migration details: `MIGRATION_SUMMARY.md`
- Project overview: `README.md`
- This reference: `QUICK_REFERENCE.md`

---

**Happy coding!** 🚀
