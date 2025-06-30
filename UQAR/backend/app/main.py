import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
from .core.config import settings
from .core.database import Base, engine


# Import API routers
try:
    from .api import auth, users, sections, documents, exercises, chat, feedback
    all_routers_available = True
except ImportError as e:
    logging.error(f"Error importing API routers: {e}")
    # Import only essential routers
    from .api import auth, users, sections
    all_routers_available = False

# Create tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range"]
)

# Include routers
app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api/users")
app.include_router(sections.router, prefix="/api/sections")

# Include optional routers if available
if all_routers_available:
    app.include_router(documents.router, prefix="/api/documents")
    app.include_router(exercises.router, prefix="/api/exercises")
    app.include_router(chat.router, prefix="/api/chat")
    app.include_router(feedback.router, prefix="/api/feedback")

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request info
    logging.info(f"Request path: {request.url.path}")
    logging.info(f"Request method: {request.method}")
    
    # Log origin for debugging CORS issues
    origin = request.headers.get("origin")
    logging.info(f"Request origin: {origin}")
    
    # Log headers for debugging
    logging.info(f"Request headers: {request.headers}")
    
    # Call the next middleware or endpoint
    response = await call_next(request)
        
    # Log response info
    process_time = time.time() - start_time
    logging.info(f"Response status: {response.status_code}")
    logging.info(f"Response headers: {response.headers}")
    logging.info(f"Processing time: {process_time:.4f} seconds")
        
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Une erreur interne s'est produite."}
    )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    ) 