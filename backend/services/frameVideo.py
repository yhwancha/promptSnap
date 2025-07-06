from scenedetect import detect, AdaptiveDetector, split_video_ffmpeg

def frameVideo(video_path: str):
    scene_list = detect(video_path, AdaptiveDetector())
    return scene_list