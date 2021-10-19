#!/usr/bin/python3
from os import initgroups
import can2RNET
import threading
import argparse
import time
import socket
import sys
import struct
import logging
import binascii
from can2RNET import can2RNET
from can2RNET.RnetDissector import RnetDissector
import RnetCtrlInit

logger = can2RNET.logger


# Default constants:
NEUTRAL_JOY_POSITION = '%d.%d' %(0,0)
TCP_BUFFER_SIZE = 1024


"""
JMS PowerOn class will substitute to a legacy JSM 
So you can poweron raspberry witout the need to 
poweron the JMS
"""
class JsmDeamons(threading.Thread):

    SERIAL_PERIOD = 0.05
    HEARTBEAT_PERIOD = 0.1

    def __init__(self, cansocket, jsm_serial):
        self.cansocket = cansocket
        self.jsm_serial = RnetDissector.rnet_serial(jsm_serial)
        self.heartbeat = RnetDissector.rnet_heartbeat()
        threading.Thread.__init__(self)


    """
    Sending periodic 50ms serial number <Thread>
    """
    def serialDaemon(self):
        logger.info("<Serial number send daemon started>")
        while True:
            time.sleep(self.SERIAL_PERIOD)
            can2RNET.cansendraw(self.cansocket,self.jsm_serial.encode())


    def startSerialDaemon(self):
        daemon = threading.Thread(target=self.serialDaemon, daemon=True)
        daemon.start()
        return daemon


    """
    Sending periodic 100ms heartbeat <Thread>
    """
    def heartbeatDaemon(self):
        logger.info("<Heartbeat daemon started>")
        while True:
            time.sleep(self.HEARTBEAT_PERIOD)
            can2RNET.cansendraw(self.cansocket, self.heartbeat.encode())


    def startHeartbeatDaemon(self):
        daemon = threading.Thread(target=self.heartbeatDaemon, daemon=True)
        daemon.start()
        return daemon




"""
Main R-net class to send joystick frames on the bus
and take the control over the legacy JSM

"""
class RnetControl(threading.Thread):

    POSITION_FREQUENCY = 0.01   # 100Hz

    def __init__(self, jsm_init_file = "", testmode = False):
        self.joy_x = 0
        self.joy_y = 0
        self.cansocket = None
        self.testmode = testmode
        threading.Thread.__init__(self)
        logger.info("Opening socketcan")

        if testmode is False:
            self.cansend = can2RNET.cansend
        else:
            logger.warning("Switching in test mode, do not connect to CAN bus")
            self.cansend = self.dummy

        # Open can socket to prepare fake JSM PowerOn
        self.jsm =  RnetCtrlInit.RnetDualLogger()

        self.cansocket = self.jsm.motor_cansocket
        self.joyPosition = RnetDissector.rnet_joyPosition(0,0,self.jsm.jsm_subtype)


    def powerOn(self):
        # self.jsmDaemons = JsmDeamons(self.cansocket, self.jsm.jsm_serial)
        # Send power on sequence (Sends all JSM init frames)
        self.jsm.start_daemons()

        # Wait for init to be sent by JSM
        while self.jsm.init_done is not True:
            time.sleep(0.1)



    def dummy(self, arg0, arg1):
        pass


    """
    Function to be called when a new position is received from positionning client
    """
    def update_joy_position(self, data):
        x = int((data).split('.')[0])
        y = int((data).split('.')[1])
        logger.debug("Update position: x=%r, y=%r" %(x,y))
        self.joyPosition.set_data(x, y)


    """
    Function to be called periodically to send new joy command to Rnet bus
    """
    def send_joy_position(self):
        joyframe = self.joyPosition.encode()
        can2RNET.cansendraw(self.cansocket, joyframe)


    def start_daemon(self):
        logger.debug("Starting Rnet daemon")
        daemon = threading.Thread(target=self.rnet_daemon, daemon=True)
        daemon.start()
        return daemon


    """
    Endless loop that sends periodically Rnet frames
    """
    def rnet_daemon(self):
        logger.debug("Rnet daemon started")
        # sending joystick frame @100Hz
        while True:
            self.send_joy_position()
            time.sleep(self.POSITION_FREQUENCY)


class server():

    def __init__(self, ip, port, rnet):
        self.ip = ip
        self.port =port
        self.rnet = rnet
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.ip, self.port))
        except:
            logger.error("binding socket to %s:%d failed" %(self.ip, self.port))
            sys.exit(1)


    def start(self):         
            
        while True:
            logger.info('Wait for new connection')
            self.s.listen(1)
            conn, addr = self.s.accept()
            logger.info('Accept connection from: %r' %addr[0])

            while True:
                data = conn.recv(TCP_BUFFER_SIZE)
                if not data: break
                logger.debug('Received data: "%s"' %data)
                self.rnet.update_joy_position(data.decode())

            logger.info('Connection closed, reset joy position to neutral position')
            self.rnet.update_joy_position(NEUTRAL_JOY_POSITION)
            conn.close()



"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="0.0.0.0", help="Define server IPv4 address to listen to receive Joy positions, default is '0.0.0.0'")
    parser.add_argument("--port", type=int, default="4141", help="Define server port to listen, default is 4141")
    parser.add_argument("-c", "--config", default="./jsm_init.log", help="path to jsm_init_file, default is under 'xx/MagicJoystick2020/RnetCtrl/jsm_init.log'")
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("-t", "--test", help="Test mode, do not connect to CAN bus", action="store_true")

    return parser.parse_args()

if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)


    # Connect and initialize Rnet controller,
    # start heartbeat
    rnet = RnetControl(args.config, args.test)

    # Send JSM init sequence 'power on'
    rnet.powerOn()


    # Start Rnet controller
    try:
        # Start position daemon
        deamon = rnet.start_daemon()
        
    except:
        logger.error("Cannot start Rnet controller")
        sys.exit(1)


    # Start Joy or any positionning sensor server listener
    serv = server(args.ip, args.port, rnet)
    serv.start()
