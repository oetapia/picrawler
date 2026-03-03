from components.camera.simple_camera import SimpleCamera
from components.save.save_to_file import VideoRecorder
from components.server.flask import create_flask_server

camera = SimpleCamera()
camera.start()

recorder = VideoRecorder(camera)
app = create_flask_server(camera, recorder)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
