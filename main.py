from flask import Flask, request, jsonify, send_from_directory
import subprocess
import uuid
import requests
import os

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def render():
    data = request.json
    audio_url = data["audio_url"]
    video_url = data["video_url"]

    os.makedirs("assets", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    # Download audio
    audio_path = "assets/audio.mp3"
    audio = requests.get(audio_url)
    with open(audio_path, "wb") as f:
        f.write(audio.content)

    # Download video
    video_path = "assets/video.mp4"
    video = requests.get(video_url)
    with open(video_path, "wb") as f:
        f.write(video.content)

    # Output path
    out_name = f"video_{uuid.uuid4().hex}.mp4"
    out_path = f"static/{out_name}"

    # FFmpeg command: loop video, match audio, scale to vertical
    subprocess.call([
        "ffmpeg",
        "-stream_loop", "-1",
        "-i", video_path,
        "-i", audio_path,
        "-vf", "scale=1080:1920",
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-y",
        out_path
    ])

    return jsonify({"video_url": f"https://{request.host}/static/{out_name}"})


@app.route('/static/<path:filename>')
def serve_video(filename):
    return send_from_directory("static", filename)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
