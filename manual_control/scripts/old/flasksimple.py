from flask import Flask, Response
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
import threading
import time

app = Flask(__name__)

camera = Picamera2()
camera.configure(
    camera.create_video_configuration(
        main={"size": (640, 480)}
    )
)

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

@app.route('/')
def index():
    return '<img src="/video_feed">'

if __name__ == '__main__':
    camera.start()
    app.run(host='0.0.0.0', port=5000, threaded=True)
