# AI CMO API

AI Marketing Assistant API built with FastAPI, PostgreSQL, and Redis.

## Features

- FastAPI backend with async support
- PostgreSQL database with SQLAlchemy ORM
- Pydantic models for data validation
- Environment-based configuration
- Docker and Docker Compose for development
- API documentation with Swagger UI and ReDoc

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Make (optional, for convenience commands)

## Getting Started

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your configuration.

3. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /api/v1/leads/` - Create a new lead
- `GET /api/v1/leads/` - List all leads
- `GET /api/v1/leads/{lead_id}` - Get a specific lead

## Development

### Running Tests

```bash
docker-compose run --rm api pytest
```

### Database Migrations

This project uses Alembic for database migrations. To create a new migration:

```bash
alembic revision --autogenerate -m "description of changes"
```

To apply migrations:

```bash
alembic upgrade head
```

## Project Structure

```
app/
├── api/
│   └── v1/
│       └── endpoints/
│           └── leads.py
├── core/
│   └── config.py
├── db/
│   └── base.py
├── models/
│   └── lead.py
├── schemas/
│   └── lead.py
├── services/
│   └── lead_service.py
└── main.py
```

## License

MIT
