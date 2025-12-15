"""FastAPI application for AiNews."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ainews.config import get_settings

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="AiNews",
    description="AI News Aggregator - Daily AI news summaries",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint - redirects to homepage."""
    return {"message": "AiNews API - Use /health or /api/* endpoints"}


# Import routes (will be created in next steps)
# from ainews.web.routes import api, pages
# app.include_router(api.router, prefix="/api", tags=["api"])
# app.include_router(pages.router, tags=["pages"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
    )
