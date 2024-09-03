from flask import Flask, render_template, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import cv2
import paho.mqtt.client as mqtt
import os

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cctv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the database model
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Event {self.event_type} at {self.timestamp}>'

# Ensure the database tables are created
def init_db():
    with app.app_context():
        db.create_all()

camera = None  # Initialize camera to None
last_event_time = datetime.min
is_motion_detected = False
capture_interval = timedelta(seconds=10)  # Interval between captures

def cctv_live():
    global camera
    while True:
        if camera is None:
            break
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                break
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def save_event(event_type, image=None):
    with app.app_context():
        image_filename = None
        if image is not None:
            # Save the image to a file and store the filename in the database
            image_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            image_path = os.path.join('uploads', image_filename)
            cv2.imwrite(image_path, image)

        # Save the event to the database
        event = Event(event_type=event_type, image_filename=image_filename)
        db.session.add(event)
        db.session.commit()

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("glblcd/videocam")

def on_message(client, userdata, msg):
    global camera, last_event_time, is_motion_detected, capture_interval
    print(msg.topic + " \n " + msg.payload.decode("utf-8") + " \n ")

    current_time = datetime.now()

    if msg.payload.decode("utf-8") == 'Motion Detected':
        if not is_motion_detected:
            if camera is None:
                camera = cv2.VideoCapture(0)
            if camera is not None:
                success, frame = camera.read()
                if success and (current_time - last_event_time) > capture_interval:
                    save_event('Motion Detected', frame)
                    last_event_time = current_time
            is_motion_detected = True

    elif msg.payload.decode("utf-8") == 'Motion Stopped':
        if camera is not None:
            camera.release()
            camera = None
            print("Camera turned off.")
            save_event('Motion Stopped')
        is_motion_detected = False
    else:
        print('\nInvalid Input')

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message    

client.connect("mqtt.eclipseprojects.io", 1883, 60)
client.loop_start() 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    global camera
    if camera is None:
        return "Camera is off, no feed available"
    else:
        return Response(cctv_live(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/events')
def events():
    try:
        events = Event.query.all()
        return render_template('events.html', events=events)
    except Exception as e:
        print(f"Error loading events: {e}")
        return "Error loading events"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    # Ensure the 'uploads' directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    
    init_db()  # Initialize the database tables
    app.run(debug=True)
