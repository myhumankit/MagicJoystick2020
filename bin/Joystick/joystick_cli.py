import math
import time
import paho.mqtt.client as mqtt
import argparse
from magick_joystick.Topics import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--buttons", type=  int, choices = [0, 1, 2], default = 0)
    parser.add_argument("-x", "--x_speed", type = int, default = 0)
    parser.add_argument("-y", "--y_speed", type = int, default = 0)

    args = parser.parse_args()

    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    client.loop_start()

    joy_data = joystick_state(args.buttons, args.x_speed, args.y_speed, 0)
    client.publish(joy_data.TOPIC_NAME, joy_data.serialize())

    client.disconnect()