from flask import Flask, request, render_template, send_file, jsonify
import yt_dlp
from io import BytesIO
from mutagen.id3 import ID3, APIC
from PIL import Image
import os
import tempfile
import requests
import time

app = Flask(__name__)

download_info = {'status': 'not started', 'speed': 0, 'elapsed': 0, 'progress': 0, 'time': 0}

def convert_image_to_jpeg(image_data):
    with Image.open(image_data) as img:
        with BytesIO() as output:
            img.convert('RGB').save(output, format='JPEG')
            return BytesIO(output.getvalue())

def download_youtube_audio_with_cover(url, output_dir, quality):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': quality,
        }],
        'writethumbnail': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        thumbnail_url = info_dict.get('thumbnail', None)
        title = info_dict['title']
        mp3_file = os.path.join(output_dir, f"{title}.mp3")

        if thumbnail_url:
            response = requests.get(thumbnail_url)
            cover_image_data = convert_image_to_jpeg(BytesIO(response.content))
        else:
            cover_image_data = None

        return mp3_file, cover_image_data

def add_cover_image(mp3_file, cover_image_data):
    audio = ID3(mp3_file)
    audio.add(APIC(
        encoding=3,
        mime='image/jpeg',
        type=3,
        desc='Cover',
        data=cover_image_data.read()
    ))
    audio.save()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    global download_info
    download_info = {'status': 'not started', 'speed': 0, 'elapsed': 0, 'progress': 0, 'time': 0}
    
    url = request.form['url']
    format = request.form['format']
    resolution = request.form.get('resolution', 'best')
    quality = request.form.get('quality', '192')
    
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        if format == 'mp3':
            file_name, cover_image_data = download_youtube_audio_with_cover(url, temp_dir, quality)
            if cover_image_data:
                add_cover_image(file_name, cover_image_data)
            end_time = time.time()
            download_info['status'] = 'finished'
            download_info['time'] = end_time - start_time
            return send_file(file_name, as_attachment=True)
        else:
            ydl_opts = {
                'format': f'bestvideo[height<={resolution}]+bestaudio/best' if resolution != 'best' else 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'merge_output_format': 'mp4',
                'progress_hooks': [progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_name = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp4'
                if not os.path.exists(file_name):
                    file_name = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.webm'

            end_time = time.time()
            download_info['status'] = 'finished'
            download_info['time'] = end_time - start_time
            return send_file(file_name, as_attachment=True)

def progress_hook(d):
    if d['status'] == 'downloading':
        download_info['speed'] = d.get('speed', 0)
        download_info['elapsed'] = d.get('elapsed', 0)
        download_info['progress'] = d.get('_percent_str', '0.00%')

@app.route('/progress', methods=['GET'])
def progress():
    return jsonify(download_info)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
