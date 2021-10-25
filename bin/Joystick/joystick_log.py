import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filename", help = "File to output the joystick data", type = str)
args = parser.parse_args()

if args.filename:
    f = open(args.filename, "w")
    f.write("x,y,buttons,long_click")

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
            client.subscribe(joystick_state.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

    def on_message(client, userdata, msg):
        state = deserialize(msg.payload)
        f.write("%d,%d,%d,%d\n" % (state.x, state.y, state.buttons, state.long_click))

    client = mqtt.Client() 
    client.on_connect = on_connect 
    client.on_message = on_message
    client.connect("localhost", 1883, 60) 
    client.loop_forever()
else:
    parser.print_help()
