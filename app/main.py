from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.v1.endpoints import example, chat_bot, workflow
from .config.settings import get_settings
from .tasks.example_tasks import example_task
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

settings = get_settings()

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="A production-ready FastAPI skeleton project",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware - configure as needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update this in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(example.router, prefix="/api/v1")
    app.include_router(chat_bot.router, prefix="/api/v1")
    app.include_router(workflow.router, prefix="/api/v1")

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.APP_ENV
        }

    @app.post("/task/example")
    async def run_example_task(data: dict = Body(...)):
        """
        Example endpoint that triggers a Celery background task.
        Replace this with your own task logic.
        """
        x = data.get("x", 0)
        y = data.get("y", 0)
        
        # Queue the task asynchronously
        task = example_task.delay(x, y)
        
        return JSONResponse({
            "message": "Task queued successfully",
            "task_id": str(task.id),
            "status": "pending"
        })

    return app

app = create_application()
