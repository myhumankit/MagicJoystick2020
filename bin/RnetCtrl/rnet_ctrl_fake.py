import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
        
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection successful")
        client.subscribe(action_drive.TOPIC_NAME)
        client.subscribe(action_light.TOPIC_NAME)
        client.subscribe(action_horn.TOPIC_NAME)
        client.subscribe(action_max_speed.TOPIC_NAME)
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    data = deserialize(msg.payload)
    if msg.topic == action_drive.TOPIC_NAME:
        print("Drive: %d" % data.on)
    elif msg.topic == action_light.TOPIC_NAME:
        print("Light")
    elif msg.topic == action_horn.TOPIC_NAME:
        print("Horn")
    elif msg.topic == action_max_speed.TOPIC_NAME:
        print("Max speed: %d" % data.max_speed)

client = mqtt.Client() 
client.on_connect = on_connect 
client.on_message = on_message
client.connect("localhost", 1883, 60) 
client.loop_forever()
