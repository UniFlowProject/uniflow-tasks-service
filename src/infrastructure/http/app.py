from fastapi import FastAPI

from src.infrastructure.http.container import Container, build_default_container
from src.infrastructure.http.errors import register_error_handlers
from src.infrastructure.http.tasks_router import router as tasks_router


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title="Uniflow Tasks Service")
    app.state.container = container or build_default_container()
    app.include_router(tasks_router)
    register_error_handlers(app)
    return app
