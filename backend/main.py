from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from pathlib import Path

# Set up path for router imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'routers'))

from routers.frame import router as frame_router

# Create FastAPI app
app = FastAPI(
    title="PromptSnap API",
    description="API for extracting representative frames from YouTube videos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "https://prompt-snap.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register routers
app.include_router(frame_router)

# Root endpoint
@app.get("/")
async def root():
    """
    API root endpoint
    """
    return {
        "message": "🎬 Welcome to PromptSnap API!",
        "description": "Service for extracting 4 representative images from YouTube videos",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "frame_extraction": "/frame/extract-from-youtube",
            "frame_download": "/frame/download/{file_name}",
            "system_info": "/frame/info",
            "health": "/frame/health"
        },
        "github": "https://github.com/yourrepo/promptsnap",
        "frontend": "http://localhost:3000"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Check server status
    """
    try:
        # Check if required directories exist
        temp_dir = Path("temp")
        services_dir = Path("services")
        
        checks = {
            "status": "healthy",
            "temp_directory": temp_dir.exists(),
            "services_directory": services_dir.exists(),
            "python_version": sys.version.split()[0],
            "fastapi_available": True
        }
        
        # Test imports
        try:
            from services.youtube_downloader import youtube_downloader
            from services.frame_extractor import frame_extractor
            checks["youtube_downloader"] = True
            checks["frame_extractor"] = True
        except ImportError as e:
            checks["youtube_downloader"] = False
            checks["frame_extractor"] = False
            checks["import_error"] = str(e)
        
        # All checks must pass for healthy status
        all_healthy = all([
            checks["temp_directory"],
            checks["services_directory"], 
            checks["youtube_downloader"],
            checks["frame_extractor"]
        ])
        
        checks["overall_status"] = "healthy" if all_healthy else "warning"
        
        return checks
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e)
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Function executed when server starts
    """
    print("🚀 PromptSnap API server has started!")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend: http://localhost:3000")
    
    # Create required directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("temp/extracted_frames", exist_ok=True)
    print("📁 Temporary directories ready")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Function executed when server shuts down
    """
    print("👋 PromptSnap API server is shutting down.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
