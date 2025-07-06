import cv2
import os
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time
from datetime import timedelta
from PIL import Image

class FrameExtractor:
    def __init__(self, output_dir: str = None):
        """
        Initialize frame extractor
        
        Args:
            output_dir: Directory to save extracted frames
        """
        self.output_dir = output_dir or os.path.join(os.getcwd(), "temp", "extracted_frames")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """
        Extract basic video information
        
        Args:
            video_path: Video file path
            
        Returns:
            Video information dictionary or None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"Cannot open video file: {video_path}")
                return None
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                'total_frames': total_frames,
                'fps': fps,
                'width': width,
                'height': height,
                'duration': duration,
                'duration_str': str(timedelta(seconds=int(duration)))
            }
            
        except Exception as e:
            print(f"Failed to extract video information: {str(e)}")
            return None
    
    def extract_frames_by_time(self, video_path: str, frame_count: int = 4) -> List[Dict]:
        """
        Extract frames by time intervals (even distribution)
        
        Args:
            video_path: Video file path
            frame_count: Number of frames to extract
            
        Returns:
            List of extracted frame information
        """
        try:
            video_info = self.get_video_info(video_path)
            if not video_info:
                return []
            
            cap = cv2.VideoCapture(video_path)
            duration = video_info['duration']
            fps = video_info['fps']
            
            # Exclude first and last 10% for even distribution
            start_time = duration * 0.1
            end_time = duration * 0.9
            effective_duration = end_time - start_time
            
            time_intervals = []
            for i in range(frame_count):
                timestamp = start_time + (effective_duration / (frame_count - 1)) * i if frame_count > 1 else duration / 2
                time_intervals.append(timestamp)
            
            extracted_frames = []
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            for i, timestamp in enumerate(time_intervals):
                # Move to frame at specified time
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if ret:
                    # Save frame
                    frame_filename = f"{video_name}_frame_{i+1:02d}_{int(timestamp):03d}s.jpg"
                    frame_path = os.path.join(self.output_dir, frame_filename)
                    
                    # Optimize image quality
                    success = cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if success:
                        extracted_frames.append({
                            'frame_number': i + 1,
                            'timestamp': timestamp,
                            'timestamp_str': str(timedelta(seconds=int(timestamp))),
                            'file_path': frame_path,
                            'file_name': frame_filename,
                            'file_size': os.path.getsize(frame_path)
                        })
                        print(f"Frame extraction complete: {frame_filename} (time: {int(timestamp)}s)")
            
            cap.release()
            return extracted_frames
            
        except Exception as e:
            print(f"Time-based frame extraction failed: {str(e)}")
            return []
    
    def extract_frames_by_scene_change(self, video_path: str, frame_count: int = 4) -> List[Dict]:
        """
        Extract frames based on scene changes (more intelligent)
        
        Args:
            video_path: Video file path
            frame_count: Number of frames to extract
            
        Returns:
            List of extracted frame information
        """
        try:
            cap = cv2.VideoCapture(video_path)
            video_info = self.get_video_info(video_path)
            
            if not video_info:
                return []
            
            total_frames = video_info['total_frames']
            fps = video_info['fps']
            
            # Histogram comparison for scene change detection
            scene_changes = []
            prev_hist = None
            
            # Sample every 1% of total frames for performance optimization
            sample_interval = max(1, total_frames // 100)
            
            print("Analyzing scene changes...")
            
            for frame_idx in range(0, total_frames, sample_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Calculate RGB histogram
                hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                
                if prev_hist is not None:
                    # Calculate histogram difference (scene change degree)
                    diff = cv2.compareHist(hist, prev_hist, cv2.HISTCMP_CORREL)
                    scene_changes.append({
                        'frame_idx': frame_idx,
                        'timestamp': frame_idx / fps,
                        'change_score': 1 - diff  # Higher value means bigger change
                    })
                
                prev_hist = hist
            
            # Select points with largest scene changes
            scene_changes.sort(key=lambda x: x['change_score'], reverse=True)
            
            # Remove frames too close in time (minimum 10 seconds apart)
            min_interval = 10  # seconds
            selected_scenes = []
            
            for scene in scene_changes:
                is_too_close = False
                for selected in selected_scenes:
                    if abs(scene['timestamp'] - selected['timestamp']) < min_interval:
                        is_too_close = True
                        break
                
                if not is_too_close:
                    selected_scenes.append(scene)
                    
                if len(selected_scenes) >= frame_count:
                    break
            
            # Sort by time
            selected_scenes.sort(key=lambda x: x['timestamp'])
            
            # Supplement with time-based method if insufficient
            if len(selected_scenes) < frame_count:
                print(f"Scene-based method found only {len(selected_scenes)} frames, supplementing with time-based method")
                time_based_frames = self.extract_frames_by_time(video_path, frame_count - len(selected_scenes))
                
                # Merge results
                extracted_frames = []
                for scene in selected_scenes:
                    extracted_frames.extend(self._extract_frame_at_timestamp(video_path, scene['timestamp'], len(extracted_frames) + 1))
                
                for frame in time_based_frames:
                    if len(extracted_frames) < frame_count:
                        extracted_frames.append(frame)
                
                cap.release()
                return extracted_frames
            
            # Extract frames at selected scene change points
            extracted_frames = []
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            
            for i, scene in enumerate(selected_scenes):
                timestamp = scene['timestamp']
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                
                ret, frame = cap.read()
                if ret:
                    # Save frame
                    frame_filename = f"{video_name}_frame_{i+1:02d}_{int(timestamp):03d}s.jpg"
                    frame_path = os.path.join(self.output_dir, frame_filename)
                    
                    success = cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if success:
                        extracted_frames.append({
                            'frame_number': i + 1,
                            'timestamp': timestamp,
                            'timestamp_str': str(timedelta(seconds=int(timestamp))),
                            'file_path': frame_path,
                            'file_name': frame_filename,
                            'file_size': os.path.getsize(frame_path),
                            'change_score': scene['change_score']
                        })
                        print(f"Scene-based frame extraction complete: {frame_filename} (change score: {scene['change_score']:.3f})")
            
            cap.release()
            return extracted_frames
            
        except Exception as e:
            print(f"Scene-based frame extraction failed: {str(e)}")
            return []
    
    def _extract_frame_at_timestamp(self, video_path: str, timestamp: float, frame_number: int) -> List[Dict]:
        """
        Extract a single frame at specified timestamp
        """
        try:
            cap = cv2.VideoCapture(video_path)
            video_info = self.get_video_info(video_path)
            
            if not video_info:
                cap.release()
                return []
            
            fps = video_info['fps']
            frame_idx = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            
            ret, frame = cap.read()
            if ret:
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                frame_filename = f"{video_name}_frame_{frame_number:02d}_{int(timestamp):03d}s.jpg"
                frame_path = os.path.join(self.output_dir, frame_filename)
                
                success = cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                if success:
                    cap.release()
                    return [{
                        'frame_number': frame_number,
                        'timestamp': timestamp,
                        'timestamp_str': str(timedelta(seconds=int(timestamp))),
                        'file_path': frame_path,
                        'file_name': frame_filename,
                        'file_size': os.path.getsize(frame_path)
                    }]
            
            cap.release()
            return []
            
        except Exception as e:
            print(f"Single frame extraction failed: {str(e)}")
            return []
    
    def extract_representative_frames(self, video_path: str, method: str = 'auto', frame_count: int = 4) -> Dict:
        """
        Extract representative frames using specified method
        
        Args:
            video_path: Video file path
            method: Extraction method ('time', 'scene', 'auto')
            frame_count: Number of frames to extract
            
        Returns:
            Extraction result dictionary
        """
        start_time = time.time()
        
        try:
            # Get video information
            video_info = self.get_video_info(video_path)
            if not video_info:
                return {
                    'success': False,
                    'error': 'Failed to get video information',
                    'extraction_time': time.time() - start_time
                }
            
            # Determine extraction method
            actual_method = method
            if method == 'auto':
                # Use scene-based for videos longer than 5 minutes, time-based for shorter videos
                actual_method = 'scene' if video_info['duration'] > 300 else 'time'
            
            # Extract frames
            if actual_method == 'scene':
                frames = self.extract_frames_by_scene_change(video_path, frame_count)
            else:  # time
                frames = self.extract_frames_by_time(video_path, frame_count)
            
            if not frames:
                return {
                    'success': False,
                    'error': 'No frames extracted',
                    'extraction_time': time.time() - start_time
                }
            
            # Calculate total size
            total_size = sum(frame['file_size'] for frame in frames)
            
            return {
                'success': True,
                'video_info': video_info,
                'extraction_method': actual_method,
                'extraction_time': round(time.time() - start_time, 2),
                'frames_extracted': len(frames),
                'frames': frames,
                'total_size': total_size
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'extraction_time': time.time() - start_time
            }
    
    def cleanup_frames(self, frame_paths: List[str]) -> bool:
        """
        Clean up extracted frame files
        
        Args:
            frame_paths: List of frame file paths to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success_count = 0
            for file_path in frame_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    success_count += 1
            
            print(f"Frame cleanup complete: {success_count} files deleted")
            return success_count > 0
            
        except Exception as e:
            print(f"Frame cleanup failed: {str(e)}")
            return False

# Create global instance
frame_extractor = FrameExtractor()

# Convenience functions
def extract_video_frames(video_path: str, method: str = 'auto', frame_count: int = 4) -> Dict:
    return frame_extractor.extract_representative_frames(video_path, method, frame_count)

def get_video_info(video_path: str) -> Optional[Dict]:
    return frame_extractor.get_video_info(video_path) 