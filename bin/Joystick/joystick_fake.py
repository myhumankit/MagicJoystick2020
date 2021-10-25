import math
import time
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

if __name__ == "__main__":
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    client.loop_start()

    theta = 0

    while True:
        button = 0
        long_click = 0

        theta += 2 * math.pi / 60
        r = abs(127 * math.sin(theta / 10))
        x = int(r * math.cos(theta))
        y = int(r * math.sin(theta))

        joy_data = joystick_state(button, x, y, long_click)
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        time.sleep(1 / 30)

