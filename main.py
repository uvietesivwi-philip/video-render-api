from flask import Flask, request, jsonify, send_from_directory
import subprocess
import uuid
import requests
import os
import shutil

app = Flask(__name__)

# Utility: Get audio duration using ffprobe
def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout.decode().strip())

# Utility: Safe file download + type check
def safe_download(url, path, expected_type):
    r = requests.get(url, stream=True)
    if r.status_code == 200 and expected_type in r.headers.get("Content-Type", ""):
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    return False

@app.route('/render', methods=['POST'])
def render():
    data = request.json
    audio_url = data.get("audio_url")
    video_url = data.get("video_url")

    # Prepare folders
    os.makedirs("assets", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    # Paths
    audio_path = "assets/audio.mp3"
    video_path = "assets/video.mp4"

    # Download audio + video
    if not safe_download(audio_url, audio_path, "audio"):
        return jsonify({"error": "Invalid or inaccessible audio file."}), 400

    if not safe_download(video_url, video_path, "video"):
        return jsonify({"error": "Invalid or inaccessible video file."}), 400

    # Get audio duration
    try:
        audio_duration = get_audio_duration(audio_path)
    except Exception as e:
        return jsonify({"error": "Failed to read audio duration.", "details": str(e)}), 500

    # Output path
    out_name = f"video_{uuid.uuid4().hex}.mp4"
    out_path = f"static/{out_name}"

    # Render final video
    subprocess.call([
        "ffmpeg",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-t", str(audio_duration),
        "-vf", "scale=1080:1920",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y", out_path
    ])

    # Cleanup
    shutil.rmtree("assets")

    return jsonify({
        "video_url": f"https://{request.host}/static/{out_name}"
    })

@app.route('/static/<path:filename>')
def serve_video(filename):
    return send_from_directory("static", filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
