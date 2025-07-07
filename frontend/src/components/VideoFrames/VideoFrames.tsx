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
  const [showPromptModal, setShowPromptModal] = useState<FrameInfo | null>(null);
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

  const handleShowPrompt = useCallback((frame: FrameInfo) => {
    setShowPromptModal(frame);
  }, []);

  const handleClosePromptModal = useCallback(() => {
    setShowPromptModal(null);
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

  const generateVideoPrompt = (frame: FrameInfo, videoTitle?: string) => {
    // Simplified creative prompt templates
    const promptTemplates = [
      "Create a hyper-realistic, satisfying short video where a person carefully {action} a {adjective} {object} on a {surface} in a {setting}. The {object} looks {texture} with {details}. As the {tool} {motion_verb} through it slowly, the material {reaction} and gives a {result}. Add realistic hand movements with {hands} holding the {object}. Focus on textures, reflections, and {sensory} satisfaction. Lighting should be {lighting}, enhancing the {visual_effect}. Video duration: {duration} seconds. Camera: {camera}, {motion_style} on the {focus_moment}",
      
      "Create a mesmerizing, ultra-detailed video showcasing {action} a {adjective} {object} with precise movements. The {object} appears {texture} with {details}. Watch as each {motion_verb} creates {visual_result}. The {setting} provides perfect {ambiance}. Capture every detail with {camera}. Include {environmental} and {atmospheric} effects. Duration: {duration} seconds. Style: {style} with {motion_characteristics}",
      
      "Produce a breathtaking, cinematic video where someone {action} a {adjective} {object} in a {setting}. The {object} exhibits {texture} while {interaction}. Every detail should be {quality}, from {detail1} to {detail2}. The {atmosphere} creates {mood} as the {dynamic} unfolds. Filming: {camera} with {lighting}. Focus on {sensory} and {aesthetic}. Runtime: {duration} seconds"
    ];
    
    // Word banks for vivid descriptions
    const wordBanks = {
      actions: ['slices', 'carves', 'cuts', 'sculpts', 'shapes', 'transforms', 'crafts', 'molds'],
      adjectives: ['glossy', 'translucent', 'shimmering', 'crystalline', 'iridescent', 'luminous', 'pristine', 'ethereal'],
      objects: ['watermelon', 'gemstone', 'crystal sphere', 'glass sculpture', 'metallic orb', 'prism', 'diamond', 'pearl'],
      surfaces: ['wooden cutting board', 'polished marble countertop', 'glass surface', 'pristine white table'],
      settings: ['modern kitchen', 'minimalist studio', 'elegant dining room', 'contemporary workspace'],
      textures: ['translucent and shiny, resembling red jelly', 'like polished marble', 'with mirror-like surfaces', 'appearing as flowing honey', 'looking like molten glass', 'smooth as porcelain'],
      details: ['embedded realistic black seeds', 'crystalline elements that catch the light', 'intricate patterns', 'prismatic reflections', 'subtle color gradients'],
      tools: ['large knife', 'precision blade', 'sharp cleaver', 'professional knife'],
      motions: ['glides', 'flows', 'dances', 'ripples', 'wobbles', 'undulates', 'oscillates'],
      reactions: ['wobbles gently', 'shimmers beautifully', 'cascades smoothly', 'ripples elegantly', 'flows gracefully'],
      results: ['smooth, clean slice', 'perfectly satisfying cut', 'elegant separation', 'pristine division'],
      hands: ['perfectly manicured hands', 'hands with painted nails', 'elegant fingers', 'skilled hands'],
      sensory: ['ASMR-like', 'tactile', 'satisfying', 'mesmerizing', 'hypnotic'],
      lighting: ['bright and soft', 'warm golden hour glow', 'dramatic rim lighting', 'diffused natural light', 'cinematic lighting'],
      visual_effects: ['glassy effect of the jelly', 'prismatic reflections', 'crystalline sparkles', 'ethereal glow'],
      cameras: ['close-up angle', 'macro lens detail', 'intimate close-up', 'extreme close-up', 'artistic angle'],
      motion_styles: ['slow motion', 'ultra slow motion', 'smooth camera movement', 'steady tracking'],
      durations: ['10', '12', '15', '18', '20']
    };
    
    const getRandomItem = (array: string[]) => array[Math.floor(Math.random() * array.length)];
    
    // Select random template
    const template = getRandomItem(promptTemplates);
    
    // Replace all placeholders
    const filledPrompt = template
      .replace('{action}', getRandomItem(wordBanks.actions))
      .replace('{adjective}', getRandomItem(wordBanks.adjectives))
      .replace('{object}', getRandomItem(wordBanks.objects))
      .replace('{surface}', getRandomItem(wordBanks.surfaces))
      .replace('{setting}', getRandomItem(wordBanks.settings))
      .replace('{texture}', getRandomItem(wordBanks.textures))
      .replace('{details}', getRandomItem(wordBanks.details))
      .replace('{tool}', getRandomItem(wordBanks.tools))
      .replace('{motion_verb}', 'cuts')
      .replace('{reaction}', getRandomItem(wordBanks.reactions))
      .replace('{result}', getRandomItem(wordBanks.results))
      .replace('{hands}', getRandomItem(wordBanks.hands))
      .replace('{sensory}', getRandomItem(wordBanks.sensory))
      .replace('{lighting}', getRandomItem(wordBanks.lighting))
      .replace('{visual_effect}', getRandomItem(wordBanks.visual_effects))
      .replace('{camera}', getRandomItem(wordBanks.cameras))
      .replace('{motion_style}', getRandomItem(wordBanks.motion_styles))
      .replace('{focus_moment}', 'cutting moment')
      .replace('{duration}', getRandomItem(wordBanks.durations))
      .replace('{visual_result}', 'stunning visual effects')
      .replace('{ambiance}', 'atmospheric lighting')
      .replace('{environmental}', 'subtle particle effects')
      .replace('{atmospheric}', 'ambient lighting')
      .replace('{style}', 'cinematic quality')
      .replace('{motion_characteristics}', 'fluid motion')
      .replace('{interaction}', 'beautiful light interactions')
      .replace('{quality}', 'ultra-realistic')
      .replace('{detail1}', 'surface textures')
      .replace('{detail2}', 'light reflections')
      .replace('{atmosphere}', 'ambient environment')
      .replace('{mood}', 'satisfying atmosphere')
      .replace('{dynamic}', 'cutting action')
      .replace('{aesthetic}', 'visual satisfaction');
    
    return filledPrompt;
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Prompt copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy text:', error);
      alert('Failed to copy to clipboard.');
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
                  className={styles.promptBtn}
                  onClick={() => handleShowPrompt(frame)}
                  title="Show video prompt"
                >
                  🎬 Show Video Prompt
                </button>
                
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

      {/* Video Prompt Modal */}
      {showPromptModal && (
        <div className={styles.modal} onClick={handleClosePromptModal}>
          <div className={styles.promptModalContent} onClick={e => e.stopPropagation()}>
            <button className={styles.closeBtn} onClick={handleClosePromptModal}>
              ✕
            </button>
            
            <div className={styles.promptModalHeader}>
              <h3>🎬 Video Generation Prompt</h3>
              <p>Frame #{showPromptModal.frame_number} at {showPromptModal.timestamp_str}</p>
            </div>
            
            <div className={styles.promptPreview}>
              <div className={styles.promptImageContainer}>
                <Image
                  src={getFrameImageUrl(showPromptModal.file_name)}
                  alt={`Frame ${showPromptModal.frame_number}`}
                  fill
                  className={styles.promptImage}
                  sizes="200px"
                />
              </div>
              
              <div className={styles.promptText}>
                <h4>Reference Image:</h4>
                <p>Use this frame as a reference for video generation</p>
              </div>
            </div>
            
            <div className={styles.promptContent}>
              <h4>Video Generation Prompt:</h4>
              <textarea
                className={styles.promptTextarea}
                value={generateVideoPrompt(showPromptModal, video_title)}
                readOnly
                rows={6}
              />
              
              <div className={styles.promptActions}>
                <button
                  className={styles.copyBtn}
                  onClick={() => copyToClipboard(generateVideoPrompt(showPromptModal, video_title))}
                >
                  📋 Copy Prompt
                </button>
                
                <div className={styles.aiPlatforms}>
                  <h4>🎬 Try with AI Video Platforms:</h4>
                  <div className={styles.platformLinks}>
                    <a 
                      href="https://pika.art" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>🎭</span> Pika Labs
                    </a>
                    <a 
                      href="https://runwayml.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>🚀</span> RunwayML
                    </a>
                    <a 
                      href="https://www.midjourney.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>🎨</span> Midjourney
                    </a>
                    <a 
                      href="https://stability.ai/stable-video" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>⚡</span> Stable Video
                    </a>
                    <a 
                      href="https://lumalabs.ai/dream-machine" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>🌙</span> Luma Dream
                    </a>
                    <a 
                      href="https://www.kaiber.ai" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.platformLink}
                    >
                      <span>🎵</span> Kaiber
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 