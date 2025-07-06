#!/usr/bin/env python3
"""
전체 파이프라인 테스트: YouTube 다운로드 → 프레임 추출
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from youtube_downloader import download_youtube_video, youtube_downloader
from frame_extractor import extract_video_frames, frame_extractor

def test_full_pipeline():
    """전체 파이프라인 테스트: YouTube URL → 비디오 다운로드 → 4개 대표 이미지 추출"""
    print("🎬 PromptSnap 전체 파이프라인 테스트")
    print("=" * 60)
    
    # 테스트할 YouTube URL (짧은 비디오 사용)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"📍 테스트 URL: {test_url}")
    print("⚠️  실제 비디오를 다운로드하고 프레임을 추출합니다. 진행하시겠습니까? (y/N): ", end="")
    
    user_input = input().lower().strip()
    if user_input != 'y':
        print("테스트를 취소합니다.")
        return
    
    try:
        print("\n" + "=" * 60)
        print("1️⃣ YouTube 비디오 다운로드 중...")
        
        # 1단계: 비디오 다운로드
        download_result = download_youtube_video(test_url, quality='360p')
        
        if not download_result:
            print("❌ 비디오 다운로드 실패")
            return
        
        print("✅ 비디오 다운로드 성공!")
        print(f"   제목: {download_result['title']}")
        print(f"   파일: {download_result['file_path']}")
        print(f"   크기: {download_result['file_size']:,} bytes")
        
        print("\n" + "=" * 60)
        print("2️⃣ 프레임 추출 중...")
        
        # 2단계: 프레임 추출
        extraction_result = extract_video_frames(
            download_result['file_path'], 
            method='auto',  # 자동으로 최적 방법 선택
            frame_count=4
        )
        
        if not extraction_result['success']:
            print(f"❌ 프레임 추출 실패: {extraction_result['error']}")
            return
        
        print("✅ 프레임 추출 성공!")
        print(f"   추출 방법: {extraction_result['extraction_method']}")
        print(f"   추출 시간: {extraction_result['extraction_time']}초")
        print(f"   추출된 프레임: {extraction_result['frames_extracted']}개")
        print(f"   총 이미지 크기: {extraction_result['total_size']:,} bytes")
        
        print("\n📸 추출된 프레임 목록:")
        for i, frame in enumerate(extraction_result['frames'], 1):
            print(f"   {i}. {frame['file_name']}")
            print(f"      시간: {frame['timestamp_str']} ({frame['timestamp']:.1f}초)")
            print(f"      크기: {frame['file_size']:,} bytes")
            if 'change_score' in frame:
                print(f"      변화도: {frame['change_score']:.3f}")
            print()
        
        print("=" * 60)
        print("🎉 전체 파이프라인 테스트 성공!")
        
        # 정리 옵션
        print("\n파일을 정리하시겠습니까?")
        print("1. 모든 파일 삭제 (비디오 + 프레임)")
        print("2. 비디오만 삭제 (프레임 유지)")
        print("3. 프레임만 삭제 (비디오 유지)")
        print("4. 파일 유지")
        
        choice = input("선택 (1-4): ").strip()
        
        if choice == '1':
            # 모든 파일 삭제
            youtube_downloader.cleanup_download(download_result)
            frame_paths = [frame['file_path'] for frame in extraction_result['frames']]
            frame_extractor.cleanup_frames(frame_paths)
            print("✅ 모든 파일 정리 완료")
            
        elif choice == '2':
            # 비디오만 삭제
            youtube_downloader.cleanup_download(download_result)
            print("✅ 비디오 파일 정리 완료")
            print("📸 프레임 파일들이 유지됩니다:")
            for frame in extraction_result['frames']:
                print(f"   {frame['file_path']}")
                
        elif choice == '3':
            # 프레임만 삭제
            frame_paths = [frame['file_path'] for frame in extraction_result['frames']]
            frame_extractor.cleanup_frames(frame_paths)
            print("✅ 프레임 파일 정리 완료")
            print(f"🎬 비디오 파일이 유지됩니다: {download_result['file_path']}")
            
        else:
            print("📁 모든 파일이 유지됩니다:")
            print(f"   비디오: {download_result['file_path']}")
            print("   프레임:")
            for frame in extraction_result['frames']:
                print(f"     {frame['file_path']}")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")

def test_frame_extraction_only():
    """프레임 추출만 테스트 (기존 비디오 파일 사용)"""
    print("🎬 프레임 추출 단독 테스트")
    print("=" * 40)
    
    video_path = input("비디오 파일 경로를 입력하세요: ").strip()
    
    if not os.path.exists(video_path):
        print("❌ 파일이 존재하지 않습니다.")
        return
    
    try:
        print("\n📊 비디오 정보 분석 중...")
        
        # 비디오 정보 확인
        from frame_extractor import get_video_info
        video_info = get_video_info(video_path)
        
        if video_info:
            print("✅ 비디오 정보:")
            print(f"   해상도: {video_info['width']}x{video_info['height']}")
            print(f"   길이: {video_info['duration_str']}")
            print(f"   FPS: {video_info['fps']:.2f}")
            print(f"   총 프레임: {video_info['total_frames']:,}")
        
        print("\n🎨 프레임 추출 시작...")
        
        # 프레임 추출
        result = extract_video_frames(video_path, method='auto', frame_count=4)
        
        if result['success']:
            print("✅ 프레임 추출 성공!")
            print(f"   방법: {result['extraction_method']}")
            print(f"   소요 시간: {result['extraction_time']}초")
            
            for i, frame in enumerate(result['frames'], 1):
                print(f"   {i}. {frame['file_name']} ({frame['timestamp_str']})")
        else:
            print(f"❌ 프레임 추출 실패: {result['error']}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def main():
    """메인 메뉴"""
    print("🎬 PromptSnap 프레임 추출 테스트 도구")
    print("=" * 50)
    print("1. 전체 파이프라인 테스트 (YouTube → 프레임 추출)")
    print("2. 프레임 추출만 테스트 (기존 비디오 파일)")
    print("3. 종료")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == '1':
        test_full_pipeline()
    elif choice == '2':
        test_frame_extraction_only()
    elif choice == '3':
        print("👋 테스트를 종료합니다.")
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main() 