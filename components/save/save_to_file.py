from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from datetime import datetime
import threading
import time

from components.save.convert_video import convert_to_mp4


class VideoRecorder:
    def __init__(self, camera, bitrate=10_000_000):
        self._camera = camera
        self._encoder = H264Encoder(bitrate=bitrate)
        self._lock = threading.Lock()
        self.recording = False
        self.recording_start_time = None
        self._current_h264 = None

    def start(self, filepath=None):
        with self._lock:
            if self.recording:
                return None
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"recording_{timestamp}.h264"
            self._current_h264 = filepath
            self._camera.start_encoder(self._encoder, FileOutput(filepath))
            self.recording = True
            self.recording_start_time = datetime.now()
            print("Recording started:", filepath)
        return filepath

    def stop(self):
        with self._lock:
            if not self.recording:
                return None
            self._camera.stop_encoder(self._encoder)
            self.recording = False
            h264 = self._current_h264
            self._current_h264 = None
            self.recording_start_time = None
            print("Recording stopped")
        if h264:
            return convert_to_mp4(h264)
        return None

    def stop_after(self, seconds):
        def _delayed_stop():
            time.sleep(seconds)
            if self.recording:
                self.stop()
                print(f"Recording automatically stopped after {seconds} seconds")

        threading.Thread(target=_delayed_stop, daemon=True).start()
