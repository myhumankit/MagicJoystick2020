#!/usr/bin/python3
import threading
import sys
from magick_joystick.can2RNET import can2RNET, RnetDissector
from RnetCtrlInit import JSMiser

logger = can2RNET.logger


# To change if "no buffer space available" error occurs during power on part
SOCKET_NO = 1

class RnetCanJSMsub(threading.Thread):

    init_done = False
    jsm_subtype = None
    joy_subtype = None
    battery_level_callback = None
    chair_speed_callback = None
    cansocket = None
    serial_bytes = None

    def __init__(self):
        """R-net class for pican mono port connection"""

        threading.Thread.__init__(self)
        try:
            self.cansocket = can2RNET.opencansocket(SOCKET_NO)
        except:
            logger.error("RnetListener socketcan can1 cannot be opened!")
            sys.exit(1)


    def turnMotorOn(self):
        """Send init sequence to motor. Get deviceID and serial bytes as well."""
        logger.info("Turn motor on with JSMiser...")
        jsm = JSMiser()
        deviceID, serial = jsm.jsm_start()
        self.jsm_subtype = deviceID & 0x0F
        self.joy_subtype = deviceID
        self.serial_bytes = serial
        
    
    def connect(self):
        """Starting listening thread to get motor information such as battery level or chair speed."""
        thr = threading.Thread(target=self.rnet_daemon, daemon=True)
        thr.start()
        self.init_done = True
        

    def set_battery_level_callback(self, callback):
        """Set battery level display callback"""
        self.battery_level_callback = callback
    
    def set_chair_speed_callback(self, callback):
        """Set chair speed callback"""
        self.chair_speed_callback = callback


    def rnet_daemon(self):
        """Endless loop waiting for Rnet frames"""

        logger.debug("RnetListener daemon started")
        while True:
            rnetFrame = can2RNET.canrecv(self.cansocket)

            __, _, _, frameName, _, __, __ = RnetDissector.getFrameType(rnetFrame)
           
            if (frameName == 'BATTERY_LEVEL'):
                if self.battery_level_callback is not None:
                    self.battery_level_callback(rnetFrame)
            
            if (frameName == 'CHAIR_SPEED'):
                if self.chair_speed_callback is not None:
                    self.chair_speed_callback(rnetFrame)

