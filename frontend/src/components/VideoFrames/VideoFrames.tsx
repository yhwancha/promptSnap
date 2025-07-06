'use client';

import { useState, useCallback } from 'react';
import Image from 'next/image';
import { FrameExtractionResponse, FrameInfo, getFrameImageUrl } from '../../lib/frameExtraction';
import styles from './VideoFrames.module.css';

interface VideoFramesProps {
  extractionResult: FrameExtractionResponse | null;
  isLoading?: boolean;
  error?: string | null;
}

export default function VideoFrames({ extractionResult, isLoading, error }: VideoFramesProps) {
  const [selectedFrame, setSelectedFrame] = useState<FrameInfo | null>(null);
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  const handleImageError = useCallback((fileName: string) => {
    setImageErrors(prev => new Set(prev).add(fileName));
  }, []);

  const handleFrameClick = useCallback((frame: FrameInfo) => {
    setSelectedFrame(frame);
  }, []);

  const handleCloseModal = useCallback(() => {
    setSelectedFrame(null);
  }, []);

  const formatFileSize = (bytes: number): string => {
    const kb = bytes / 1024;
    return kb > 1024 ? `${(kb / 1024).toFixed(1)}MB` : `${kb.toFixed(1)}KB`;
  };

  const downloadFrame = async (frame: FrameInfo) => {
    try {
      const imageUrl = getFrameImageUrl(frame.file_name);
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = frame.file_name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Frame download failed:', error);
      alert('Frame download failed.');
    }
  };

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner}></div>
          <p>Extracting frames...</p>
          <small>Downloading YouTube video and generating representative images.</small>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h3>❌ Frame Extraction Failed</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!extractionResult || !extractionResult.success || !extractionResult.frames) {
    return null;
  }

  const { video_title, video_info, extraction_method, extraction_time, frames } = extractionResult;

  return (
    <div className={styles.container}>
      {/* Video info header */}
      <div className={styles.header}>
        <h2 className={styles.title}>🎬 Extracted Frames</h2>
        {video_title && <h3 className={styles.videoTitle}>{video_title}</h3>}
        
        <div className={styles.videoInfo}>
          {video_info && (
            <>
              <span className={styles.infoItem}>
                📐 {video_info.width}×{video_info.height}
              </span>
              <span className={styles.infoItem}>
                ⏱️ {video_info.duration_str}
              </span>
              <span className={styles.infoItem}>
                🎯 {extraction_method} method
              </span>
              <span className={styles.infoItem}>
                ⚡ {extraction_time}s processing
              </span>
            </>
          )}
        </div>
      </div>

      {/* Frames grid */}
      <div className={styles.framesGrid}>
        {frames.map((frame, index) => {
          const imageUrl = getFrameImageUrl(frame.file_name);
          const hasError = imageErrors.has(frame.file_name);
          
          return (
            <div key={frame.file_name} className={styles.frameCard}>
              <div 
                className={styles.imageContainer}
                onClick={() => handleFrameClick(frame)}
              >
                {hasError ? (
                  <div className={styles.imageError}>
                    <span>🖼️</span>
                    <p>Image load failed</p>
                  </div>
                ) : (
                  <Image
                    src={imageUrl}
                    alt={`Frame ${frame.frame_number} at ${frame.timestamp_str}`}
                    fill
                    className={styles.frameImage}
                    onError={() => handleImageError(frame.file_name)}
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                  />
                )}
                <div className={styles.overlay}>
                  <span className={styles.frameNumber}>#{frame.frame_number}</span>
                  <span className={styles.timestamp}>{frame.timestamp_str}</span>
                </div>
              </div>
              
              <div className={styles.frameInfo}>
                <div className={styles.infoRow}>
                  <span className={styles.label}>Time:</span>
                  <span>{frame.timestamp_str}</span>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.label}>Size:</span>
                  <span>{formatFileSize(frame.file_size)}</span>
                </div>
                {frame.change_score && (
                  <div className={styles.infoRow}>
                    <span className={styles.label}>Change Score:</span>
                    <span>{(frame.change_score * 100).toFixed(1)}%</span>
                  </div>
                )}
                
                <button
                  className={styles.downloadBtn}
                  onClick={() => downloadFrame(frame)}
                  title="Download frame"
                >
                  📥 Download
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary info */}
      <div className={styles.summary}>
        <p>
          Total {frames.length} frames extracted • 
          Total size: {formatFileSize(extractionResult.total_size || 0)}
        </p>
      </div>

      {/* Modal - view selected frame in large size */}
      {selectedFrame && (
        <div className={styles.modal} onClick={handleCloseModal}>
          <div className={styles.modalContent} onClick={e => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={handleCloseModal}>
              ✕
            </button>
            
            <div className={styles.modalHeader}>
              <h3>Frame #{selectedFrame.frame_number}</h3>
              <p>At {selectedFrame.timestamp_str}</p>
            </div>
            
            <div className={styles.modalImageContainer}>
              <Image
                src={getFrameImageUrl(selectedFrame.file_name)}
                alt={`Frame ${selectedFrame.frame_number}`}
                fill
                className={styles.modalImage}
                sizes="90vw"
              />
            </div>
            
            <div className={styles.modalInfo}>
              <div className={styles.modalInfoGrid}>
                <div>
                  <strong>Frame:</strong> #{selectedFrame.frame_number}
                </div>
                <div>
                  <strong>Timestamp:</strong> {selectedFrame.timestamp_str}
                </div>
                <div>
                  <strong>File Size:</strong> {formatFileSize(selectedFrame.file_size)}
                </div>
                {selectedFrame.change_score && (
                  <div>
                    <strong>Change Score:</strong> {(selectedFrame.change_score * 100).toFixed(1)}%
                  </div>
                )}
              </div>
              
              <button
                className={styles.modalDownloadBtn}
                onClick={() => downloadFrame(selectedFrame)}
              >
                📥 Download Frame
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 