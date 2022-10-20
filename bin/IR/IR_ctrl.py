import threading
import time
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import logging
import sys
import os
import jsonpickle

import actions

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

# MQTT Connection initialization
def on_connect(mqtt_client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connection successful IR")
            mqtt_client.subscribe(IR_write.TOPIC_NAME)
            mqtt_client.subscribe(IR_execute.TOPIC_NAME)
            mqtt_client.subscribe(IR_delete.TOPIC_NAME)
        else:
            logger.info(f"Connection failed with code {rc}")


def send_response(data):
    print("Sending...")
    mqtt_client.publish(IR_response.TOPIC_NAME, jsonpickle.encode(data))
    print("send_response : " + jsonpickle.encode(data))

def on_message(mqtt_client, userdata, msg):
    data_current = deserialize(msg.payload)
    print("on_message : msg.topic = " + msg.topic)

    if msg.topic == IR_write.TOPIC_NAME:
        actions.record(data_current.folder, data_current.action, send_response)

    elif msg.topic == IR_execute.TOPIC_NAME:
        actions.execute(data_current.folder, data_current.action)
    
    elif msg.topic == IR_delete.TOPIC_NAME:
        actions.delete(data_current.folder, data_current.action)


mqtt_client = mqtt.Client() 
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_forever()
print("Mqtt connection opened")
time.sleep(0.5)




