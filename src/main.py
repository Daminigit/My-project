"""
FastAPI Application Entry Point.

Initializes the FastAPI app, registers middleware,
and includes API route handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import app_config, llm_config


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Validate LLM API key at startup
    llm_config.validate()

    application = FastAPI(
        title=app_config.NAME,
        description="AI-powered restaurant recommendation service inspired by Zomato.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware — allow frontend connections
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from src.api.routes import router
    application.include_router(router, prefix="/api")

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=app_config.HOST,
        port=app_config.PORT,
        reload=app_config.DEBUG,
    )
