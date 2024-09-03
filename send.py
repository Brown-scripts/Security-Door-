import paho.mqtt.client as mqtt
import time
from gpiozero import MotionSensor
from signal import pause
from time import sleep


pir = MotionSensor(18)

def motion_function():
    message = "Motion Detected"
    print(message)
    client.publish("glblcd/videocam", message)

def no_motion_function():
    sleep(10)
    message = "Motion Stopped"
    print(message)
    client.publish("glblcd/videocam", message)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected  # Use global variable
        Connected = True  # Signal connection

    else:
        print("Connection failed")

Connected = False  # global variable for the state of the connection

client = mqtt.Client()
client.on_connect = on_connect
client.connect("mqtt.eclipseprojects.io", 1883, 60)
client.loop_start()  # start the loop

pir.when_motion = motion_function
pir.when_no_motion = no_motion_function

while Connected != True:  # Wait for connection
    time.sleep(0.1)

try:
    pause()
except KeyboardInterrupt:
    client.disconnect()
    client.loop_stop()
