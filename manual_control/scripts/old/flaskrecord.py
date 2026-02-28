from flask import Flask, Response, redirect, url_for
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, H264Encoder
from picamera2.outputs import FileOutput
import io
import threading
import time
from datetime import datetime
import subprocess
import os

app = Flask(__name__)

camera = Picamera2()
camera.configure(
    camera.create_video_configuration(
        main={"size": (640, 480)}
    )
)

# ---------- MJPEG STREAM ----------
jpeg_buffer = io.BytesIO()
buffer_lock = threading.Lock()

class SafeBuffer(io.BufferedIOBase):
    def write(self, buf):
        with buffer_lock:
            jpeg_buffer.seek(0)
            jpeg_buffer.truncate()
            jpeg_buffer.write(buf)
        return len(buf)

output = SafeBuffer()

camera.start_recording(
    JpegEncoder(),
    FileOutput(output)
)

# ---------- RECORDING ----------
recording = False
video_encoder = H264Encoder(bitrate=10_000_000)
video_output = None
current_h264 = None

def convert_to_mp4(h264_file):
    mp4_file = h264_file.replace(".h264", ".mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-framerate", "30",
            "-i", h264_file,
            "-c", "copy",
            mp4_file
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return mp4_file

def gen():
    while True:
        with buffer_lock:
            frame = jpeg_buffer.getvalue()

        if frame:
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                frame +
                b'\r\n'
            )
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(
        gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={'Cache-Control': 'no-cache'}
    )

# ---------- CONTROL ROUTES ----------
@app.route('/start_recording')
def start_recording():
    global recording, video_output, current_h264

    if not recording:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_h264 = f"recording_{timestamp}.h264"
        video_output = FileOutput(current_h264)

        camera.start_encoder(video_encoder, video_output)
        recording = True
        print("Recording started:", current_h264)

    return redirect(url_for('index'))

@app.route('/stop_recording')
def stop_recording():
    global recording, current_h264

    if recording:
        camera.stop_encoder(video_encoder)
        recording = False
        print("Recording stopped")

        # Convert to MP4
        mp4_file = convert_to_mp4(current_h264)
        print("Converted to:", mp4_file)

        # Optional: delete raw h264
        # os.remove(current_h264)

        current_h264 = None

    return redirect(url_for('index'))

@app.route('/')
def index():
    return """
    <html>
        <body>
            <h1>Live Camera</h1>
            <img src="/video_feed"><br><br>
            <a href="/start_recording"><button>Start Recording</button></a>
            <a href="/stop_recording"><button>Stop Recording</button></a>
        </body>
    </html>
    """

if __name__ == '__main__':
    camera.start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
