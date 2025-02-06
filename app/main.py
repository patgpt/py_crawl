from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import scraper
from app.utils.events import broadcaster
from sse_starlette.sse import EventSourceResponse

"""
Main FastAPI application instance and configuration
"""

app = FastAPI(
    title="py_crawl",
    description="A modern, async web crawler built with FastAPI",
    version="1.0.0",
    # Redirect root to docs
    docs_url="/",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper.router, prefix="/api/v1", tags=["scraper"])

@app.get("/")
async def root():
    """
    Root endpoint returning a welcome message

    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to FastAPI Application"}

@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint

    Returns:
        dict: Status of the application
    """
    return {"status": "healthy"}

@app.get("/stream")
async def stream_events(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    return EventSourceResponse(
        broadcaster.subscribe(request),
        media_type="text/event-stream"
    )
