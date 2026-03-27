from flask import Flask, Response, redirect, url_for, request, jsonify


def create_app(name, cors=False):
    app = Flask(name)
    if cors:
        from flask_cors import CORS
        CORS(app)
    return app


def create_flask_server(camera, recorder=None):
    app = create_app(__name__)

    @app.route('/video_feed')
    def video_feed():
        return Response(
            camera.mjpeg_generator(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            headers={'Cache-Control': 'no-cache'},
        )

    @app.route('/')
    def index():
        recording_msg = ""
        if recorder and recorder.recording and recorder.recording_start_time:
            recording_msg = (
                f"<p style='color:red; font-weight:bold;'>"
                f"Recording in progress! Started at "
                f"{recorder.recording_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                f"</p>"
            )
        controls = ""
        if recorder:
            controls = """
            <a href="/start_recording"><button>Start Recording</button></a>
            <a href="/stop_recording"><button>Stop Recording</button></a>
            """
        return f"""
        <html>
            <body>
                <h1>Live Camera</h1>
                {recording_msg}
                <img src="/video_feed"><br><br>
                {controls}
            </body>
        </html>
        """

    if recorder:
        @app.route('/start_recording')
        def start_recording():
            recorder.start()
            return redirect(url_for('index'))

        @app.route('/stop_recording')
        def stop_recording():
            recorder.stop()
            return redirect(url_for('index'))

        @app.route('/ir_event', methods=['POST'])
        def ir_event():
            data = request.json
            if not data:
                return jsonify({"status": "error", "message": "No JSON"}), 400
            print(f"IR event received: {data}")
            if data.get("beam_broken") and not recorder.recording:
                recorder.start()
                recorder.stop_after(5 * 60)
            return jsonify({"status": "ok"})

    return app
