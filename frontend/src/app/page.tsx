import YouTubeForm from '@/components/YouTubeForm/YouTubeForm';
import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1 className={styles.title}>PromptSnap - YouTube Video Player</h1>
        <p className={styles.description}>
          Enter a YouTube URL to watch videos directly in your browser
        </p>
        
        <YouTubeForm />
      </main>
    </div>
  );
}
