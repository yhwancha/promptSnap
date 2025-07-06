import styles from './YouTubePlayer.module.css';

interface YouTubePlayerProps {
  url: string;
}

export default function YouTubePlayer({ url }: YouTubePlayerProps) {
  // Extract video ID from YouTube URL (including Shorts)
  const extractVideoId = (url: string): string | null => {
    const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=|shorts\/)|youtu\.be\/)([^"&?\/\s]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
  };

  // Check if it's a YouTube Shorts URL
  const isShorts = (url: string): boolean => {
    return url.includes('/shorts/');
  };

  const videoId = extractVideoId(url);
  const shortsMode = isShorts(url);

  if (!videoId) {
    return (
      <div className={styles.error}>
        <p>Invalid YouTube URL provided</p>
      </div>
    );
  }

  return (
    <div className={styles.youtubePlayer}>
      <div className={shortsMode ? styles.shortsContainer : styles.videoContainer}>
        <iframe
          src={`https://www.youtube.com/embed/${videoId}`}
          title={shortsMode ? "YouTube Shorts player" : "YouTube video player"}
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
      {shortsMode && (
        <div className={styles.shortsInfo}>
          <p>📱 YouTube Shorts</p>
        </div>
      )}
    </div>
  );
} 