import yt_dlp
import requests
from mutagen.id3 import ID3, APIC
from PIL import Image
from io import BytesIO
import os

def download_youtube_audio_with_cover(url, output_folder="downloads"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_folder}/%(title)s.%(ext)s',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'writethumbnail': True  # Attempt to download thumbnail if available
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            thumbnail_url = info_dict.get('thumbnail', None)
            mp3_file = f"{output_folder}/{info_dict['title']}.mp3"

            if not os.path.exists(mp3_file):
                print("MP3 file not found.")
                return

            if thumbnail_url:
                # Download cover image directly into memory
                response = requests.get(thumbnail_url)
                cover_image_data = convert_image_to_jpeg(BytesIO(response.content))
                print("Cover image retrieved and converted to JPEG.")
                add_cover_image(mp3_file, cover_image_data)
            else:
                print("No cover image found; skipping.")
    except Exception as e:
        print(f"An error occurred: {e}")

def convert_image_to_jpeg(image_data):
    # Convert image to JPEG format
    with Image.open(image_data) as img:
        with BytesIO() as output:
            img.convert('RGB').save(output, format='JPEG')
            return BytesIO(output.getvalue())

def add_cover_image(mp3_file, cover_image_data):
    try:
        # Load the MP3 file
        audio = ID3(mp3_file)

        # Add cover image directly from BytesIO
        audio.add(APIC(
            encoding=3,  # UTF-8
            mime='image/jpeg',  # Ensure correct image format
            type=3,  # Cover (front)
            desc='Cover',
            data=cover_image_data.read()
        ))
        audio.save()
        print(f"Cover image added to {mp3_file}.")
    except Exception as e:
        print(f"An error occurred while adding the cover image: {e}")

# Example usage
download_youtube_audio_with_cover('https://www.youtube.com/watch?v=your_video_id')
