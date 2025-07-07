'use client';

import { useState } from 'react';
import YouTubePlayer from '../YouTubePlayer/YouTubePlayer';
import VideoFrames from '../VideoFrames/VideoFrames';
import { extractFramesFromYouTube, isValidYouTubeUrl, FrameExtractionResponse } from '../../lib/frameExtraction';
import styles from './YouTubeForm.module.css';

export default function YouTubeForm() {
  const [url, setUrl] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  
  // Frame extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionResult, setExtractionResult] = useState<FrameExtractionResponse | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [quality, setQuality] = useState<'144p' | '240p' | '360p' | '480p' | '720p' | '1080p'>('360p');
  const [method, setMethod] = useState<'time' | 'scene' | 'auto'>('auto');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      setVideoUrl(url.trim());
    }
  };

  const handleExtractFrames = async () => {
    if (!url.trim()) {
      alert('Please enter a YouTube URL.');
      return;
    }

    if (!isValidYouTubeUrl(url.trim())) {
      alert('Please enter a valid YouTube URL.');
      return;
    }

    setIsExtracting(true);
    setExtractionError(null);
    setExtractionResult(null);

    try {
      const result = await extractFramesFromYouTube({
        url: url.trim(),
        quality,
        method,
        frame_count: 4
      });

      setExtractionResult(result);
    } catch (error) {
      console.error('Frame extraction failed:', error);
      setExtractionError(error instanceof Error ? error.message : 'Frame extraction failed.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleClear = () => {
    setUrl('');
    setVideoUrl('');
    setExtractionResult(null);
    setExtractionError(null);
  };

  const isValidUrl = url.trim() && isValidYouTubeUrl(url.trim());

  return (
    <div className={styles.container}>
      {/* Input form */}
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputGroup}>
          <label htmlFor="youtube-url" className={styles.label}>
            YouTube URL:
          </label>
          <input
            id="youtube-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=... or https://youtube.com/shorts/..."
            className={styles.input}
          />
        </div>

        {/* Extraction options */}
        <div className={styles.optionsGroup}>
          <div className={styles.option}>
            <label htmlFor="quality" className={styles.optionLabel}>
              Video Quality:
            </label>
            <select
              id="quality"
              value={quality}
              onChange={(e) => setQuality(e.target.value as typeof quality)}
              className={styles.select}
            >
              <option value="144p">144p (Fastest)</option>
              <option value="240p">240p</option>
              <option value="360p">360p (Recommended)</option>
              <option value="480p">480p</option>
              <option value="720p">720p</option>
              <option value="1080p">1080p (Highest Quality)</option>
            </select>
          </div>

          <div className={styles.option}>
            <label htmlFor="method" className={styles.optionLabel}>
              Extraction Method:
            </label>
            <select
              id="method"
              value={method}
              onChange={(e) => setMethod(e.target.value as typeof method)}
              className={styles.select}
            >
              <option value="auto">Auto Select</option>
              <option value="time">Time-based (Even Distribution)</option>
              <option value="scene">Scene-based (Smart)</option>
            </select>
          </div>
        </div>

        {/* Button group */}
        <div className={styles.buttonGroup}>
          <button type="submit" className={styles.submitButton}>
            🎬 Video Preview
          </button>
          <button 
            type="button" 
            onClick={handleExtractFrames}
            disabled={!isValidUrl || isExtracting}
            className={`${styles.extractButton} ${!isValidUrl ? styles.disabled : ''}`}
          >
            {isExtracting ? '🔄 Extracting...' : '📸 Extract Frames'}
          </button>
          <button 
            type="button" 
            onClick={handleClear}
            className={styles.clearButton}
          >
            🗑️ Clear
          </button>
        </div>
      </form>

      {/* URL validation indicator */}
      {url.trim() && (
        <div className={`${styles.urlStatus} ${isValidUrl ? styles.valid : styles.invalid}`}>
          {isValidUrl ? '✅ Valid YouTube URL' : '❌ Invalid YouTube URL'}
        </div>
      )}

      {/* Video preview */}
      {videoUrl && (
        <div className={styles.videoSection}>
          <h3 className={styles.sectionTitle}>🎬 Video Preview</h3>
          <YouTubePlayer url={videoUrl} />
        </div>
      )}

      {/* Frame extraction results */}
      <VideoFrames 
        extractionResult={extractionResult}
        isLoading={isExtracting}
        error={extractionError}
      />

      {/* Help section */}
      <div className={styles.helpSection}>
        <h4>💡 How to Use</h4>
        <ul>
          <li><strong>Video Preview:</strong> Enter a YouTube URL and click &quot;Video Preview&quot; button</li>
          <li><strong>Frame Extraction:</strong> Click &quot;Extract Frames&quot; button to generate 4 representative images</li>
          <li><strong>Quality Selection:</strong> Higher quality provides clearer images but takes longer to process</li>
          <li><strong>Extraction Method:</strong> Auto select chooses the best method based on video length</li>
        </ul>
      </div>
    </div>
  );
} 