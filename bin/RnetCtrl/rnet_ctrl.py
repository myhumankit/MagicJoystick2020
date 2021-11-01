import threading
import argparse
import time
import socket
import sys
import logging
from rnet_can import  RnetCan
import paho.mqtt.client as mqtt
from magick_joystick.can2RNET import can2RNET, RnetDissector
from magick_joystick.Topics import *

logger = can2RNET.logger



"""
Main R-net class to send joystick frames on the bus
and take the control over the legacy JSM

"""
class RnetControl(threading.Thread):

    POSITION_FREQUENCY = 0.01   # 100Hz - RNET requirement
    STATUS_FREQUENCY = 0.1      # 10Hz

    def __init__(self, testmode = False):
        self.RnetHorn = None
        self.testmode = testmode
        self.drive_mode = False
        self.battery_level = 0
        threading.Thread.__init__(self)
        
        try:
            self.mqtt_client = mqtt.Client() 
            self.mqtt_client.on_connect = self.on_connect 
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.connect("localhost", 1883, 60) 
            self.mqtt_client.loop_start()
            logger.info("mqtt connection successfull")
        except:
            logger.error("mqtt connection error")

        if testmode is False:
            self.cansend = can2RNET.cansendraw
        else:
            logger.warning("Switching in test mode, do not connect to CAN bus")
            self.cansend = self.dummy

        # Open can socket to prepare fake JSM power_on
        logger.info("Opening socketcan")
        self.rnet_can =  RnetCan(self.testmode)


    # MQTT Connection initialization
    def on_connect(self, mqtt_client, userdata, flags, rc):
            if rc == 0:
                logger.info("Connection successful")
                mqtt_client.subscribe(action_drive.TOPIC_NAME)
                mqtt_client.subscribe(action_light.TOPIC_NAME)
                mqtt_client.subscribe(action_horn.TOPIC_NAME)
                mqtt_client.subscribe(action_max_speed.TOPIC_NAME)
                mqtt_client.subscribe(joystick_state.TOPIC_NAME)
            else:
                logger.info(f"Connection failed with code {rc}")


    # MQTT Message broker :
    def on_message(self, mqtt_client, userdata, msg):         
            # ENABLE DRIVE COMMAND
            if msg.topic == action_drive.TOPIC_NAME:
                logger.debug("[recv %s] Switch to drive mode ON" %(msg.topic))
                self.drive_mode = True

            # ENABLE/DISABLE LIGHTS COMMAND
            elif msg.topic == action_light.TOPIC_NAME:
                logger.debug("[recv %s] Switch ON lights" %(msg.topic))

            # ENABLE/DISABLE HORN
            elif msg.topic == action_horn.TOPIC_NAME:
                self.RnetHorn.toogle_state()
                logger.debug("[recv %s] Switch horn state to %r" %(msg.topic, self.RnetHorn.get_state))
                self.cansend(self.rnet_can.jsm_cansocket,self.RnetHorn.encode())
                time.sleep(1)
                self.RnetHorn.toogle_state()
                logger.debug("[recv %s] Switch horn state to %r" %(msg.topic, self.RnetHorn.get_state))
                self.cansend(self.rnet_can.jsm_cansocket,self.RnetHorn.encode())

            # SET MAX SPEED
            elif msg.topic == action_max_speed.TOPIC_NAME:
                logger.debug("[recv %s] set max speed to FXME" %(msg.topic))

            # JOYSTICK POSITION
            elif msg.topic == joystick_state.TOPIC_NAME:
                if self.drive_mode is True:
                    joy_data = deserialize(msg.payload)
                    
                    # Check if long click is pressed to get out of drive mode
                    # and force position to neutral if true
                    if (joy_data.buttons == 1) :
                        self.drive_mode = False
                        self.RnetJoyPosition.set_data(0, 0)
                    else:
                        self.RnetJoyPosition.set_data(joy_data.x, joy_data.y)
                        if joy_data.x or joy_data.y:
                            logger.debug("[recv %s] X=%d, Y=%d" %(msg.topic, joy_data.x, joy_data.y))


            else:
                logger.error("MQTT unsupported message")



    def power_on(self):

        # Send power on sequence (Sends all JSM init frames)
        self.rnet_can.connect()

        # Wait for init to be sent by JSM
        while self.rnet_can.init_done is not True:
            time.sleep(0.1)

        logger.info("Rnet Init complete, jsm_subtype id is: %x" %self.rnet_can.jsm_subtype)

        # Initialize required Rnet frame objects and callbacks:
        self.rnet_can.set_battery_level_callback(self.update_battery_level)        
        self.RnetHorn = RnetDissector.RnetHorn(self.rnet_can.jsm_subtype)
        self.RnetJoyPosition = RnetDissector.RnetJoyPosition(0,0,self.rnet_can.jsm_subtype)
        self.RnetBatteryLevel = RnetDissector.RnetBatteryLevel()

        return self.start_threads()


    def dummy(self, arg0, arg1):
        pass


    def update_battery_level(self, raw_frame):
        self.RnetBatteryLevel.set_raw(raw_frame)
        self.battery_level = self.RnetBatteryLevel.decode()


    def start_threads(self):
        logger.debug("Starting Rnet joystick position thread")
        thread = threading.Thread(target=self.rnet_joystick_thread, daemon=True)
        thread.start()
        return thread


    """
    Endless loop that provides wheelchair statuses such as battery level...
    """
    def rnet_status_thread(self):
        logger.debug("Rnet status thread started")
        while True:
            status = status_battery_level(self.battery_level)
            self.mqtt_client.publish(status.TOPIC_NAME, status.serialize())
            time.sleep(self.STATUS_FREQUENCY)


    """
    Endless loop that sends periodically Rnet joystick position frames
    """
    def rnet_joystick_thread(self):
        logger.debug("Rnet joystick thread started")
        while True:
            joyframe = self.RnetJoyPosition.encode()
            self.cansend(self.rnet_can.motor_cansocket, joyframe)
            time.sleep(self.POSITION_FREQUENCY)



"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("-t", "--testmode", help="Test mode, do not connect to CAN bus", action="store_true")

    return parser.parse_args()

if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Connect to piCan and initialize Rnet controller,
    rnet = RnetControl(args.testmode)

    # Send JSM init sequence 'power on'
    thread = rnet.power_on()
    thread.join()
