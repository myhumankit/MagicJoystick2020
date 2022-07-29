#!/usr/bin/python3
import threading
import sys
from magick_joystick.can2RNET import can2RNET, RnetDissector

logger = can2RNET.logger



"""
R-net class for pican dual port connection
"""
class RnetCan(threading.Thread):

    init_done = False
    jsm_mode = False
    jsm_subtype = None
    joy_subtype = None
    motor_cansocket = None
    jsm_cansocket = None
    
    battery_level_callback = None
    chair_speed_callback = None
    motor_pos_callback = None
    joy_position_callback = None
    power_off_callback = None

    def __init__(self):
        self.cansocket0 = None
        self.cansocket1 = None

        threading.Thread.__init__(self)

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
        # launch daemon
        logger.debug("RnetListener Starting Rnet Dual daemons")
        daemon0 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket0, self.cansocket1, 'PORT0'], daemon=True)
        daemon1 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket1, self.cansocket0, 'PORT1'], daemon=True)
        daemon0.start()
        daemon1.start()
        return daemon0, daemon1


    """
    Battery level display callback
    """
    def set_battery_level_callback(self, callback):
        self.battery_level_callback = callback
    
    """
    Chair speed callback
    """
    def set_chair_speed_callback(self, callback):
        self.chair_speed_callback = callback
    
    """
    Chair motor pos callback (logging)
    """
    def set_motor_pos_callback(self, callback):
        self.motor_pos_callback = callback
    
    """
    Used to send modified joy frames
    """
    def set_joy_position_callback(self, callback):
        self.joy_position_callback = callback
    
    """
    Set callback for power off frame
    """
    def set_power_off_callback(self, callback):
        self.power_off_callback = callback


    """
    Endless loop waiting for Rnet frames
    Each received frame is logged/filtered and forwarded to other port
    """
    def rnet_daemon(self, listensock, sendsock, logger_tag):
        logger.info("RnetListener daemon '%s' started"%logger_tag)

        while True:
            rnetFrame = can2RNET.canrecv(listensock)

            __, _, device_id, frameName, data, __, __ = RnetDissector.getFrameType(rnetFrame)

            
            if (frameName == 'JOY_POSITION'):
                if (listensock==self.motor_cansocket) and (self.motor_pos_callback is not None): #From motor
                    self.motor_pos_callback(data)
                elif (listensock==self.jsm_cansocket) and (self.joy_position_callback is not None):
                    rnetFrame = self.joy_position_callback(rnetFrame) # joy frame is modified so we send it like the other ones
            
            can2RNET.cansendraw(sendsock, rnetFrame)

            if self.init_done == False:
                if frameName == 'PMTX_HEATBEAT':
                    self.motor_cansocket = listensock
                    self.jsm_cansocket = sendsock

                # Wait for a joy position to record JSM ID
                if (frameName=='JOY_POSITION') and (listensock==self.jsm_cansocket):
                    # and only get it if the frame come from JSM
                    self.jsm_subtype = device_id & 0x0F
                    self.joy_subtype = device_id
                
                if (self.jsm_subtype is not None) and (self.jsm_cansocket is not None):
                    self.init_done = True
                
                continue #Ignore the lines below


            if (frameName == 'BATTERY_LEVEL'):
                if self.battery_level_callback is not None:
                    self.battery_level_callback(rnetFrame)
            
            if (frameName == 'CHAIR_SPEED'):
                if self.chair_speed_callback is not None:
                    self.chair_speed_callback(rnetFrame)      

            if (frameName == 'POWER_OFF'):
                if self.power_off_callback is not None:
                    self.power_off_callback(False)           

