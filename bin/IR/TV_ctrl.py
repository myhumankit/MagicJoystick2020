import threading
import time
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import logging
import sys
import os

# Instanciate logger:
logging.basicConfig(
    level=logging.INFO, #log every message above INFO level (debug, info, warning, error, critical)
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()
h = logging.StreamHandler(sys.stdout)
h.flush = sys.stdout.flush
logger.addHandler(h)

def send_power():
    os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/power.txt")


def send_volume(type):
    if(type == "up"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/volume_plus.txt")
    elif (type == "down"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/volume_less.txt")
    elif (type == "mute"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/mute.txt")


# MQTT Connection initialization
def on_connect(mqtt_client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connection successful")
            mqtt_client.subscribe(TV_power.TOPIC_NAME)
            mqtt_client.subscribe(TV_volume.TOPIC_NAME)
        else:
            logger.info(f"Connection failed with code {rc}")


# MQTT Message broker :
def on_message(mqtt_client, userdata, msg):
    data_current = deserialize(msg.payload)
    if msg.topic == TV_power.TOPIC_NAME:
        #power_state = data_current.state
        print("TV powered")
        send_power()
    elif msg.topic ==TV_volume.TOPIC_NAME:
        print("TV volume + or - or mute")
        volume_type = data_current.type
        print(volume_type)
        send_volume(volume_type)






mqtt_client = mqtt.Client() 
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()
print("Mqtt connection opened")
time.sleep(0.5)




