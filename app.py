from flask import Flask, request, jsonify, send_file
from moviepy.editor import VideoFileClip, AudioFileClip
import requests, uuid, os

app = Flask(__name__)

@app.route("/merge", methods=["POST"])
def merge():
    data = request.json
    audio_url = data["audio_url"]
    video_url = data["video_url"]

    os.makedirs("temp", exist_ok=True)
    audio_path = "temp/audio.mp3"
    video_path = "temp/video.mp4"
    output_path = f"temp/out_{uuid.uuid4().hex}.mp4"

    with open(audio_path, "wb") as f:
        f.write(requests.get(audio_url).content)
    with open(video_path, "wb") as f:
        f.write(requests.get(video_url).content)

    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)

    looped = video.loop(duration=audio.duration).subclip(0, audio.duration)
    result = looped.set_audio(audio)
    result.write_videofile(output_path, codec="libx264", audio_codec="aac")

    return send_file(output_path, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
