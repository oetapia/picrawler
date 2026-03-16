from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
import threading
import time


class SimpleCamera:
    def __init__(self, size=(640, 480)):
        self._buf = io.BytesIO()
        self._lock = threading.Lock()

        self.camera = Picamera2()
        self.camera.configure(
            self.camera.create_video_configuration(main={"size": size})
        )
        self._jpeg_encoder = JpegEncoder()

    def start(self):
        self.camera.start_recording(self._jpeg_encoder, FileOutput(self._make_output()))

    def _make_output(self):
        class _SafeBuffer(io.BufferedIOBase):
            def __init__(self_, buf, lock):
                self_._buf = buf
                self_._lock = lock

            def write(self_, data):
                with self_._lock:
                    self_._buf.seek(0)
                    self_._buf.truncate()
                    self_._buf.write(data)
                return len(data)

        return _SafeBuffer(self._buf, self._lock)

    def get_frame(self):
        with self._lock:
            return self._buf.getvalue()

    def mjpeg_generator(self):
        while True:
            frame = self.get_frame()
            if frame:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' +
                    frame +
                    b'\r\n'
                )
            time.sleep(0.03)

    def start_encoder(self, encoder, output):
        self.camera.start_encoder(encoder, output)

    def stop_encoder(self, encoder):
        self.camera.stop_encoder(encoder)

    def stop(self):
        self.camera.stop_recording()
