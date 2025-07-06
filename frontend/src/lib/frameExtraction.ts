export interface FrameInfo {
  frame_number: number;
  timestamp: number;
  timestamp_str: string;
  file_name: string;
  file_size: number;
  change_score?: number;
}

export interface VideoInfo {
  total_frames: number;
  fps: number;
  width: number;
  height: number;
  duration: number;
  duration_str: string;
}

export interface FrameExtractionRequest {
  url: string;
  quality?: '144p' | '240p' | '360p' | '480p' | '720p' | '1080p';
  method?: 'time' | 'scene' | 'auto';
  frame_count?: number;
}

export interface FrameExtractionResponse {
  success: boolean;
  error?: string;
  video_title?: string;
  video_info?: VideoInfo;
  extraction_method?: string;
  extraction_time?: number;
  frames_extracted?: number;
  frames?: FrameInfo[];
  total_size?: number;
}

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Extract frames from YouTube URL
 */
export async function extractFramesFromYouTube(
  request: FrameExtractionRequest
): Promise<FrameExtractionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/frame/extract-from-youtube`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: request.url,
        quality: request.quality || '360p',
        method: request.method || 'auto',
        frame_count: request.frame_count || 4,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Frame extraction API error:', error);
    throw error;
  }
}

/**
 * Generate frame image file URL
 */
export function getFrameImageUrl(fileName: string): string {
  return `${API_BASE_URL}/frame/download/${fileName}`;
}

/**
 * Get system information
 */
export async function getSystemInfo() {
  try {
    const response = await fetch(`${API_BASE_URL}/frame/info`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('System info query error:', error);
    throw error;
  }
}

/**
 * Clean up temporary frame files
 */
export async function cleanupFrames() {
  try {
    const response = await fetch(`${API_BASE_URL}/frame/cleanup`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Frame cleanup error:', error);
    throw error;
  }
}

/**
 * Check if YouTube URL is valid
 */
export function isValidYouTubeUrl(url: string): boolean {
  const patterns = [
    /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
    /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
    /^https?:\/\/youtu\.be\/[\w-]+/,
  ];
  
  return patterns.some(pattern => pattern.test(url));
} 