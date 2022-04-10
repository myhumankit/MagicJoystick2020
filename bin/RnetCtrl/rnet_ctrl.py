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
    JOY_WATCHDOG_TIMEOUT = 20   # Force joystick position to [0,0] after 200ms without data

    def __init__(self, testmode = False):
        self.RnetHorn = None
        # self.hornThread = None
        self.testmode = testmode
        self.drive_mode = False
        self.battery_level = 0
        self.joy_watchdog = self.JOY_WATCHDOG_TIMEOUT
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
                logger.info("[recv %s] Switch to drive mode ON" %(msg.topic))
                self.drive_mode = True

            # ENABLE/DISABLE LIGHTS COMMAND
            elif msg.topic == action_light.TOPIC_NAME:
                logger.info("[recv %s] Switch ON lights" %(msg.topic))

            # HORN
            elif msg.topic == action_horn.TOPIC_NAME:
                logger.info("[recv %s] Play Tone" %(msg.topic))
                tone = RnetDissector.RnetPlayTone()
                self.cansend(self.rnet_can.jsm_cansocket, tone.encode())

            # SET MAX SPEED
            elif msg.topic == action_max_speed.TOPIC_NAME:
                max_speed = deserialize(msg.payload)
                speed = (max_speed.max_speed)*20
                self.RnetMotorMaxSpeed.set_data(speed)
                self.cansend(self.rnet_can.motor_cansocket,self.RnetMotorMaxSpeed.encode())
                logger.info("[recv %s] set max speed to %d" %(msg.topic, speed))

            # JOYSTICK POSITION
            elif msg.topic == joystick_state.TOPIC_NAME:
                if self.drive_mode is True:
                    joy_data = deserialize(msg.payload)
                    
                    # Data received from Joystck, reset watchdog
                    self.joy_watchdog = self.JOY_WATCHDOG_TIMEOUT

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


    # For now Horn doesn't work, use 'playTone' instead
    # def horn_thread(self):
    #     while self.RnetHorn.get_state() == 0:
    #         self.cansend(self.rnet_can.motor_cansocket,self.RnetHorn.encode())
    #         logger.info("Send horn to motor: %s " %(RnetDissector.printFrame(self.RnetHorn.encode())))
    #         time.sleep(0.1)

    #     self.RnetHorn.toogle_state()
    #     self.cansend(self.rnet_can.motor_cansocket,self.RnetHorn.encode())      
    #     logger.info("Send horn to motor: %s " %(RnetDissector.printFrame(self.RnetHorn.encode())))
    #     self.hornThread = None


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
        self.RnetMotorMaxSpeed = RnetDissector.RnetMotorMaxSpeed(20, self.rnet_can.jsm_subtype)

        return self.start_threads()


    def dummy(self, arg0, arg1):
        pass


    def update_battery_level(self, raw_frame):
        self.RnetBatteryLevel.set_raw(raw_frame)
        self.battery_level = self.RnetBatteryLevel.decode()
        logger.debug("Got battery level info: %d" %self.battery_level)


    def start_threads(self):
        logger.info("Starting Rnet joystick position thread")
        thread = threading.Thread(target=self.rnet_joystick_thread, daemon=True)
        thread.start()
        return thread


    """
    Endless loop that provides wheelchair statuses such as battery level...
    """
    def rnet_status_thread(self):
        logger.info("Rnet status thread started")
        while True:
            status = status_battery_level(self.battery_level)
            self.mqtt_client.publish(status.TOPIC_NAME, status.serialize())
            time.sleep(self.STATUS_FREQUENCY)


    """
    Endless loop that sends periodically Rnet joystick position frames
    """
    def rnet_joystick_thread(self):
        logger.info("Rnet joystick thread started")
        while True:
            joyframe = self.RnetJoyPosition.encode()
            self.cansend(self.rnet_can.motor_cansocket, joyframe)
            
            # Decrement joystick watchdog
            # force position to [0,0] if no data received from 
            # joystick 
            self.joy_watchdog -= 1
            if self.joy_watchdog == 0 :
                self.RnetJoyPosition.set_data(0, 0)
            
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
