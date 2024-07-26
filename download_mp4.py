import yt_dlp

def download_youtube_video(url, resolution="1080p", output_folder="downloads"):
    ydl_opts = {
        'format': f'bestvideo[height<={resolution[:-1]}]+bestaudio/best[height<={resolution[:-1]}]/best',
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',  # Ensure output is in MP4 format
        'noplaylist': True  # Ensure only the single video URL is processed
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Video downloaded successfully to {output_folder}.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
download_youtube_video('https://www.youtube.com/watch?v=your_video_id')
