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
    subtitle_url = data["subtitle_url"]
    images = data["images"]

    os.makedirs("assets", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    for i, url in enumerate(images):
        img = requests.get(url)
        with open(f"assets/img{i:02d}.png", "wb") as f:
            f.write(img.content)

    audio = requests.get(audio_url)
    with open("assets/audio.mp3", "wb") as f:
        f.write(audio.content)

    subs = requests.get(subtitle_url)
    with open("assets/subs.srt", "wb") as f:
        f.write(subs.content)

    with open("assets/inputs.txt", "w") as f:
        for i in range(len(images)):
            f.write(f"file 'img{i:02d}.png'\nduration 3\n")
        f.write(f"file 'img{len(images)-1:02d}.png'\n")

    out_name = f"video_{uuid.uuid4().hex}.mp4"
    subprocess.call([
        "ffmpeg",
        "-y",
        "-f", "concat", "-safe", "0", "-i", "assets/inputs.txt",
        "-i", "assets/audio.mp3",
        "-vf", "subtitles=assets/subs.srt",
        "-pix_fmt", "yuv420p", "-shortest",
        f"static/{out_name}"
    ])

    return jsonify({"video_url": f"https://{request.host}/static/{out_name}"})

@app.route('/static/<path:filename>')
def serve_video(filename):
    return send_from_directory("static", filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
