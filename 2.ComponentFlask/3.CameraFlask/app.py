# flask_libcamera_stream.py

from flask import Flask, render_template_string, Response
import cv2
from picamera2 import Picamera2

app = Flask(__name__)

# HTML 템플릿
html = """
<!doctype html>
<html>
<head>
    <title>Raspberry Pi Camera Stream</title>
</head>
<body>
    <h1>Live Camera Stream</h1>
    <img src="{{ url_for('video_feed') }}" width="640" height="480">
</body>
</html>
"""

# 카메라 초기화
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

def gen_frames():
    while True:
        frame = picam2.capture_array()
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template_string(html)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
