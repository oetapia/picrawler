from flask import Flask, Response, redirect, url_for, request, jsonify
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

# -------------------------
# Camera setup
# -------------------------
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
camera.start_recording(JpegEncoder(), FileOutput(output))

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

# ---------- RECORDING ----------
recording = False
recording_start_time = None  # track when current recording started
video_encoder = H264Encoder(bitrate=10_000_000)
video_output = None
current_h264 = None
record_lock = threading.Lock()  # prevent multiple triggers

def convert_to_mp4(h264_file, delete_original=True):
    """Convert .h264 to .mp4 and optionally delete raw file"""
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
    print("Converted to:", mp4_file)
    if delete_original:
        os.remove(h264_file)
    return mp4_file

def stop_recording_after_delay(delay_seconds):
    global recording, current_h264, recording_start_time
    time.sleep(delay_seconds)
    with record_lock:
        if recording:
            camera.stop_encoder(video_encoder)
            recording = False
            print(f"Recording automatically stopped after {delay_seconds} seconds")
            if current_h264:
                convert_to_mp4(current_h264)
                current_h264 = None
            recording_start_time = None  # reset start time

@app.route('/start_recording')
def start_recording():
    global recording, video_output, current_h264, recording_start_time
    with record_lock:
        if not recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_h264 = f"recording_{timestamp}.h264"
            video_output = FileOutput(current_h264)
            camera.start_encoder(video_encoder, video_output)
            recording = True
            recording_start_time = datetime.now()
            print("Recording started:", current_h264)
    return redirect(url_for('index'))

@app.route('/stop_recording')
def stop_recording():
    global recording, current_h264, recording_start_time
    with record_lock:
        if recording:
            camera.stop_encoder(video_encoder)
            recording = False
            print("Recording stopped")
            if current_h264:
                convert_to_mp4(current_h264)
                current_h264 = None
            recording_start_time = None
    return redirect(url_for('index'))

@app.route('/')
def index():
    recording_msg = ""
    if recording and recording_start_time:
        recording_msg = f"<p style='color:red; font-weight:bold;'>Recording in progress! Started at {recording_start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>"

    return f"""
    <html>
        <body>
            <h1>Live Camera</h1>
            {recording_msg}
            <img src="/video_feed"><br><br>
            <a href="/start_recording"><button>Start Recording</button></a>
            <a href="/stop_recording"><button>Stop Recording</button></a>
        </body>
    </html>
    """

# -------------------------
# IR SENSOR ENDPOINT
# -------------------------
@app.route('/ir_event', methods=['POST'])
def ir_event():
    global recording, video_output, current_h264, recording_start_time
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON"}), 400

    print(f"IR event received: {data}")

    if data.get("beam_broken"):
        with record_lock:
            if not recording:
                # Start recording
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                current_h264 = f"recording_{timestamp}.h264"
                video_output = FileOutput(current_h264)
                camera.start_encoder(video_encoder, video_output)
                recording = True
                recording_start_time = datetime.now()
                print("Recording started automatically due to IR event:", current_h264)

                # Start a background thread to stop recording after 5 minutes
                threading.Thread(
                    target=stop_recording_after_delay,
                    args=(5*60,),  # 5 minutes
                    daemon=True
                ).start()

    return jsonify({"status": "ok"})

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == '__main__':
    camera.start()
    app.run(host='0.0.0.0', port=5000, threaded=True)

