from inspect import stack
import threading
import time
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import logging
import sys
import os
import RPi.GPIO as GPIO

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

#Send the command of TV_A.html
def send_command_A(command_id):
    if(command_id != 15 and command_id != 19):
        os.system("sudo ir-ctl --device /dev/lirc0 --send TV_A_raw_command/TV_A_" + str(command_id)+ ".txt")
    elif(command_id != 15 or command_id != 19):
        print("pas de bouton 15 ou 19")
    

# MQTT Connection initialization
def on_connect(mqtt_client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connection successful TVA")
            mqtt_client.subscribe(TV_A_control.TOPIC_NAME)
        else:
            logger.info(f"Connection failed with code {rc}")


# MQTT Message broker :
def on_message(mqtt_client, userdata, msg):
    data_current = deserialize(msg.payload)
    if msg.topic == TV_A_control.TOPIC_NAME:
        command_id = data_current.id
        print("TV_A : un bouton")
        send_command_A(command_id)

#Set the PIN to 3v3
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
GPIO.output(26, GPIO.HIGH)


mqtt_client = mqtt.Client() 
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()
print("Mqtt connection opened")
time.sleep(0.5)




