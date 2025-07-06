// YouTube Data API integration
// You'll need to get an API key from Google Cloud Console

export interface YouTubeVideoData {
  id: string;
  title: string;
  description: string;
  thumbnail: string;
  duration: string;
  viewCount: string;
  publishedAt: string;
}

export async function getYouTubeVideoData(videoId: string): Promise<YouTubeVideoData | null> {
  const API_KEY = process.env.NEXT_PUBLIC_YOUTUBE_API_KEY;
  
  if (!API_KEY) {
    console.warn('YouTube API key not found');
    return null;
  }

  try {
    const response = await fetch(
      `https://www.googleapis.com/youtube/v3/videos?id=${videoId}&key=${API_KEY}&part=snippet,statistics,contentDetails`
    );
    
    const data = await response.json();
    
    if (data.items && data.items.length > 0) {
      const video = data.items[0];
      return {
        id: videoId,
        title: video.snippet.title,
        description: video.snippet.description,
        thumbnail: video.snippet.thumbnails.high.url,
        duration: video.contentDetails.duration,
        viewCount: video.statistics.viewCount,
        publishedAt: video.snippet.publishedAt,
      };
    }
    
    return null;
  } catch (error) {
    console.error('Error fetching YouTube data:', error);
    return null;
  }
}

export function extractVideoIdFromUrl(url: string): string | null {
  const regex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
  const match = url.match(regex);
  return match ? match[1] : null;
} 