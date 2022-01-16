#!/usr/bin/python3
import threading
import argparse
import time
import sys
import binascii
import logging
from build.lib.magick_joystick.can2RNET.RnetDissector import printFrame
from magick_joystick.can2RNET import can2RNET, RnetDissector

logger = can2RNET.logger



"""
R-net class for pican dual port connection
"""
class RnetCan(threading.Thread):

    init_done = False
    jsm_mode = False
    jsm_subtype = None
    motor_cansocket = None
    jsm_cansocket = None
    battery_level = None

    def __init__(self, testmode = False):
        self.cansocket0 = None
        self.cansocket1 = None
        self.testmode = testmode

        threading.Thread.__init__(self)

        if self.testmode is True:
            self.init_done = True
            self.jsm_subtype = 0x200

        else:
            logger.info("RnetListener Opening socketcan")
            try:
                self.cansocket0 = can2RNET.opencansocket(0)
            except:
                logger.error("RnetListener socketcan can0 cannot be opened! Check connectivity")
                sys.exit(1)
            try:
                self.cansocket1 = can2RNET.opencansocket(1)
            except:
                logger.error("RnetListener socketcan can1 cannot be opened! Check connectivity")
                sys.exit(1)


    """
    Sart a listen/transmit daemon on each can port
    """
    def connect(self):
        if self.testmode is False:
            # launch daemon
            logger.debug("RnetListener Starting Rnet Dual daemons")
            daemon0 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket0, self.cansocket1, 'PORT0'], daemon=True)
            daemon0.start()
            daemon1 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket1, self.cansocket0, 'PORT1'], daemon=True)
            daemon1.start()
            return daemon0, daemon1
        else:
            return None, None


    """
    Set weather the JSM or the minijoy has the control on the wheelchair
    """
    def set_jsm_mode(self, mode):
        self.jsm_mode = mode


    """
    Battery level display callback
    """
    def set_battery_level_callback(self, callback):
        self.battery_level = callback


    """
    Endless loop waiting for Rnet frames
    Each received frame is logged/filtered and forwarded to other port
    """
    def rnet_daemon(self, listensock, sendsock, logger_tag):
        logger.debug("RnetListener daemon started")
        is_motor = False
        is_serial = False

        while True:
            rnetFrame = can2RNET.canrecv(listensock)
            frameToLog  = binascii.hexlify(rnetFrame)
            #logger.debug('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))

            __, subType, frameName, data, __, __ = RnetDissector.getFrameType(rnetFrame)
           
            # Trash all joy position frames if not in JSM mode enabled
            if (self.jsm_mode is False) and (frameName == 'JOY_POSITION'):
                pass
            else:
                can2RNET.cansendraw(sendsock, rnetFrame)

            if self.init_done == False:
                if frameName == 'PMTX_HEATBEAT':
                    self.motor_cansocket = listensock
                    self.jsm_cansocket = sendsock

                # Wait for a joy position to record JSM ID
                if frameName == 'JOY_POSITION':
                    #logger.debug('********** Got JMS ID: 0x%x **********\n' %subType)
                    self.jsm_subtype = subType
                
                if (self.jsm_subtype is not None) and (self.jsm_cansocket is not None):
                    self.init_done = True

            if (frameName == 'BATTERY_LEVEL'):
                if self.battery_level is not None:
                    self.battery_level(rnetFrame)


