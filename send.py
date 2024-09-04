import paho.mqtt.client as mqtt
import time
from gpiozero import MotionSensor, LED
from signal import pause
from time import sleep

# Initialize LEDs
green_led = LED(17)  # Use the correct GPIO pin number
red_led = LED(27)    # Use the correct GPIO pin number

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
        client.subscribe("glblcd/door")  # Subscribe to the door topic

    else:
        print("Connection failed")

def on_message(client, userdata, msg):
    print(f"Message received: {msg.payload.decode()}")
    
    if msg.payload.decode() == "Grant Access":
        green_led.on()
        red_led.off()
    elif msg.payload.decode() == "Deny Access":
        green_led.off()
        red_led.on()
    else:
        green_led.off()
        red_led.off()

Connected = False  # global variable for the state of the connection

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message  # Handle incoming messages
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
