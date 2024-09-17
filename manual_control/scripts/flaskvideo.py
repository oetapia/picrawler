from flask import Flask, Response
import cv2
from picamera2 import Picamera2
import time
import threading
import keyboard_control  # Import your keyboard_control module

app = Flask(__name__)

camera = None
camera_initialized = False

def init_camera():
    global camera, camera_initialized
    if not camera_initialized:
        try:
            print("Initializing camera...")
            camera = Picamera2()
            camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
            camera.start()
            camera_initialized = True
            print("Camera initialized successfully.")
        except RuntimeError as e:
            print(f"Failed to initialize camera: {e}")

def get_frame():
    """Capture a single frame from the camera and return it as JPEG bytes."""
    if camera:
        try:
            frame = camera.capture_array()
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        except RuntimeError as e:
            print(f"Error capturing frame: {e}")
    return b''

def gen():
    """Video streaming generator function."""
    while True:
        frame = get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)  # Adjust the delay to control frame rate

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
        <html>
            <head>
                <title>Raspberry Pi Camera Stream</title>
            </head>
            <body>
                <table>
                <tr>
                <td>

                <img src="/video_feed" style="width: 100%; height: auto;">
                </td>
                <td>
                <img src="/video_feed" style="width: 100%; height: auto;">
                </td>
                </tr>
                </table>
            </body>
        </html>
    '''

def start_keyboard_control():
    """Function to start the keyboard control script."""
    keyboard_control.main()  # Replace 'run' with the function that starts your script

if __name__ == '__main__':
    init_camera()  # Initialize the camera

    # Start keyboard control in a separate thread
    keyboard_thread = threading.Thread(target=start_keyboard_control, daemon=True)
    keyboard_thread.start()

    try:
        print("Starting server...")
        app.run(host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"Failed to run the server: {e}")
    finally:
        if camera:
            camera.stop()
            camera = None
            camera_initialized = False
