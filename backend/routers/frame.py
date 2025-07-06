from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import os
import sys
import asyncio
from pathlib import Path

# Add service module path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from youtube_downloader import download_youtube_video, youtube_downloader, validate_youtube_url
from frame_extractor import extract_video_frames, frame_extractor

router = APIRouter(prefix="/frame", tags=["frame"])

# Pydantic models
class YouTubeRequest(BaseModel):
    url: HttpUrl
    quality: str = "360p"
    method: str = "auto"  # 'time', 'scene', 'auto'
    frame_count: int = 4

class FrameInfo(BaseModel):
    frame_number: int
    timestamp: float
    timestamp_str: str
    file_name: str
    file_size: int
    change_score: Optional[float] = None

class VideoInfo(BaseModel):
    total_frames: int
    fps: float
    width: int
    height: int
    duration: float
    duration_str: str

class FrameExtractionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    video_title: Optional[str] = None
    video_info: Optional[VideoInfo] = None
    extraction_method: Optional[str] = None
    extraction_time: Optional[float] = None
    frames_extracted: Optional[int] = None
    frames: Optional[List[FrameInfo]] = None
    total_size: Optional[int] = None

@router.post("/extract-from-youtube", response_model=FrameExtractionResponse)
async def extract_frames_from_youtube(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Extract 4 representative frames from YouTube URL.
    
    - **url**: YouTube video URL (supports regular videos and Shorts)
    - **quality**: Video quality (144p, 240p, 360p, 480p, 720p, 1080p)
    - **method**: Frame extraction method ('time', 'scene', 'auto')
    - **frame_count**: Number of frames to extract (default: 4)
    
    Returns:
        Frame extraction results and individual frame information
    """
    try:
        # 1. URL validation
        url_str = str(request.url)
        if not validate_youtube_url(url_str):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL.")
        
        # 2. Video download
        download_result = download_youtube_video(
            url_str, 
            quality=request.quality
        )
        
        if not download_result:
            raise HTTPException(status_code=500, detail="Video download failed.")
        
        # 3. Frame extraction
        extraction_result = extract_video_frames(
            download_result['file_path'],
            method=request.method,
            frame_count=request.frame_count
        )
        
        if not extraction_result['success']:
            # Clean up downloaded files
            background_tasks.add_task(youtube_downloader.cleanup_download, download_result)
            raise HTTPException(status_code=500, detail=f"Frame extraction failed: {extraction_result['error']}")
        
        # 4. Build response data
        frames_info = []
        for frame in extraction_result['frames']:
            frames_info.append(FrameInfo(
                frame_number=frame['frame_number'],
                timestamp=frame['timestamp'],
                timestamp_str=frame['timestamp_str'],
                file_name=frame['file_name'],
                file_size=frame['file_size'],
                change_score=frame.get('change_score')
            ))
        
        video_info = VideoInfo(**extraction_result['video_info'])
        
        response = FrameExtractionResponse(
            success=True,
            video_title=download_result['title'],
            video_info=video_info,
            extraction_method=extraction_result['extraction_method'],
            extraction_time=extraction_result['extraction_time'],
            frames_extracted=extraction_result['frames_extracted'],
            frames=frames_info,
            total_size=extraction_result['total_size']
        )
        
        # 5. Clean up video files in background (keep frames)
        background_tasks.add_task(youtube_downloader.cleanup_download, download_result)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/download/{file_name}")
async def download_frame(file_name: str):
    """
    Download extracted frame image file.
    
    - **file_name**: Frame filename (file_name from extract-from-youtube response)
    """
    try:
        file_path = os.path.join(frame_extractor.output_dir, file_name)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found.")
        
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type="image/jpeg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File download error: {str(e)}")

@router.get("/info")
async def get_system_info():
    """
    Get system information.
    """
    try:
        temp_dir = frame_extractor.output_dir
        temp_files = []
        
        if os.path.exists(temp_dir):
            temp_files = [f for f in os.listdir(temp_dir) if f.endswith('.jpg')]
        
        return {
            "frame_output_directory": temp_dir,
            "temporary_frames": len(temp_files),
            "supported_qualities": ["144p", "240p", "360p", "480p", "720p", "1080p"],
            "extraction_methods": ["time", "scene", "auto"],
            "max_frame_count": 10
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System info query error: {str(e)}")

@router.delete("/cleanup")
async def cleanup_frames(background_tasks: BackgroundTasks):
    """
    Clean up temporary frame files.
    """
    try:
        temp_dir = frame_extractor.output_dir
        
        if not os.path.exists(temp_dir):
            return {"message": "No files to clean up.", "deleted_count": 0}
        
        temp_files = [f for f in os.listdir(temp_dir) if f.endswith('.jpg')]
        file_paths = [os.path.join(temp_dir, f) for f in temp_files]
        
        # Clean up files in background
        background_tasks.add_task(frame_extractor.cleanup_frames, file_paths)
        
        return {
            "message": f"{len(temp_files)} files will be cleaned up.",
            "deleted_count": len(temp_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File cleanup error: {str(e)}")

# Endpoints for backward compatibility
@router.post("/extract", response_model=FrameExtractionResponse)
async def extract_frames_legacy(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """Legacy endpoint - redirects to extract-from-youtube"""
    return await extract_frames_from_youtube(request, background_tasks)

@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        return {
            "status": "healthy",
            "service": "frame-extraction",
            "version": "1.0.0",
            "endpoints_available": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")