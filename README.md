# FastAPI Skeleton Project

A production-ready FastAPI skeleton project with Docker, Redis, Celery, and async support.

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
   docker-compose up -d --build
   ```

4. **Access the services:**
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Flower (Celery Monitor): http://localhost:5556

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
- `GET /api/v1/example/` - Example GET endpoint
- `POST /api/v1/example/` - Example POST endpoint

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

4. Run Celery worker:
   ```bash
   celery -A app.celery_config.celery_app worker --loglevel=info
   ```

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/`
2. Define your router and endpoints
3. Include the router in `app/main.py`

### Adding Background Tasks

1. Create task functions in `app/tasks/`
2. Use `@celery_app.task` decorator
3. Call tasks using `.delay()` or `.apply_async()`

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT
