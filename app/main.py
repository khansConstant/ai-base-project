from app.tasks.test_tasks import create_task
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from .api.v1.endpoints import leads
from .config.settings import get_settings
from fastapi.responses import JSONResponse

settings = get_settings()

def create_application() -> FastAPI:
    app = FastAPI(
        title="AI CMO API",
        description="AI Marketing Assistant API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(leads.router, prefix="/api/v1")

    @app.post("/ex1")
    def run_task(data=Body(...)):
        x = data["x"]
        y = data["y"]
        task = create_task.delay( x, y)
        return JSONResponse({"Result": task.get()})

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app

app = create_application()
