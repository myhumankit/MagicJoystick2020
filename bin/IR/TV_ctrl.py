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

def send_param(type):
    if(type == "exit"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/exit.txt")
    elif (type == "home"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/home.txt")
    elif (type == "info"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/info.txt")
    elif (type == "menu"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/menu.txt")
    elif (type == "return"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/return.txt")
    elif (type == "source"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/source.txt")
    elif (type == "tools"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/tools.txt")


def send_direction(type):
    if(type == "ok"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/ok.txt")
    elif (type == "left"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/left.txt")
    elif (type == "down"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/down.txt")
    elif (type == "right"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/right.txt")
    elif (type == "up"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/up.txt")


def send_number(nb):
    if(nb == "0"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/0.txt")
    elif (nb == "1"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/1.txt")
    elif (nb == "2"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/2.txt")
    elif (nb == "3"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/3.txt")
    elif (nb == "4"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/4.txt")
    elif (nb == "5"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/5.txt")
    elif (nb == "6"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/6.txt")
    elif (nb == "7"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/7.txt")
    elif (nb == "8"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/8.txt")
    elif (nb == "9"):
        os.system("sudo ir-ctl -d /dev/lirc0 -s /home/roxu/bin/IR/raw_command/9.txt")
    

# MQTT Connection initialization
def on_connect(mqtt_client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connection successful TV")
            mqtt_client.subscribe(TV_power.TOPIC_NAME)
            mqtt_client.subscribe(TV_volume.TOPIC_NAME)
            mqtt_client.subscribe(TV_param.TOPIC_NAME)
            mqtt_client.subscribe(TV_direction.TOPIC_NAME)
            mqtt_client.subscribe(TV_number.TOPIC_NAME)
        else:
            logger.info(f"Connection failed with code {rc}")


# MQTT Message broker :
def on_message(mqtt_client, userdata, msg):
    data_current = deserialize(msg.payload)
    if msg.topic == TV_power.TOPIC_NAME:
        #power_state = data_current.state
        print("TV powered")
        send_power()
    elif msg.topic == TV_volume.TOPIC_NAME:
        print("TV volume + or - or mute")
        volume_type = data_current.type
        send_volume(volume_type)
    elif msg.topic == TV_param.TOPIC_NAME:
        print("TV param")
        param_type = data_current.type
        send_param(param_type)
    elif msg.topic == TV_direction.TOPIC_NAME:
        print("TV direction")
        param_type = data_current.type
        send_direction(param_type)
    elif msg.topic == TV_number.TOPIC_NAME:
        print("TV number")
        nb = data_current.nb
        send_number(nb)





mqtt_client = mqtt.Client() 
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()
print("Mqtt connection opened")
time.sleep(0.5)




