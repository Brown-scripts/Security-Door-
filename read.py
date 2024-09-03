from flask import Flask, render_template, Response
import cv2
import paho.mqtt.client as mqtt

app = Flask(__name__)
camera = None  # Initialize camera to None

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
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("glblcd/videocam")


def on_message(client, userdata, msg):
    global camera
    print(msg.topic + " \n " + msg.payload.decode("utf-8") + " \n ")
    
    if msg.payload.decode("utf-8") == 'Motion Detected':
        if camera is None:
            camera = cv2.VideoCapture(0)
        else:
            print("Camera is already on.")
            
    elif msg.payload.decode("utf-8") == 'Motion Stopped':
        if camera is not None:
            camera.release()
            camera = None
            print("Camera turned off.")
        else:
            print("Camera is already off.")
    else:
        print('\nInvalid Input')


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message    

client.connect("mqtt.eclipseprojects.io", 1883, 60)
client.loop_start() 

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/video')
def video():
    global camera
    if camera is None:
        return "Camera is off, no feed available"
    else:
        return Response(cctv_live(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)

