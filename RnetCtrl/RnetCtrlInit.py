#!/python3
import can2RNET
import threading
import argparse
import time
import socket
import sys
import struct
import binascii
import logging
from can2RNET import can2RNET
from can2RNET.RnetDissector import RnetDissector

logger = can2RNET.logger

"""
Rnet JSM init sequence recorder and playback
Must use a raspberry + Dual Can board architecture

Will be placed between JSM and main controller to log all messages with source name
in case of record mode, or replace JSM incase of playback.

For the recording init sequence, the following frame sequences will
be tagged :

    JSM   0000006xxxx
    MOTOR 0000006xxxx
    => Init sequence done

    Then, waiting for either JoyPosition frame or MaxSpeed frame
    to get the JSM identifier value.

    Then init sequence recording is completed.

"""


"""
R-net class for single raspi and pican dual port logging
"""
class RnetDualLogger(threading.Thread):

    def __init__(self, tag0, tag1, logfile):
        self.cansocket0 = None
        self.cansocket1 = None
        self.tag0 = tag0
        self.tag1 = tag1
        self.logfile = logfile
        
        threading.Thread.__init__(self)
        logger.info("Opening socketcan")
        try:
            self.cansocket0 = can2RNET.opencansocket(0)
        except :
            logger.error("socketcan can0 cannot be opened! Check connectivity")
            sys.exit(1)
        try:
            self.cansocket1 = can2RNET.opencansocket(1)
        except :
            logger.error("socketcan can1 cannot be opened! Check connectivity")
            sys.exit(1)


    """
    used for single raspi and pican dual config
    """
    def start_daemons(self):

        # launch daemon
        logger.debug("Starting Rnet Dual daemons")
        daemon0 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket0, self.cansocket1, self.tag0], daemon=True)
        daemon0.start()
        daemon1 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket1, self.cansocket0, self.tag1], daemon=True)
        daemon1.start()
        return daemon0, daemon1


    """
    Endless loop waiting for Rnet frames
    Each frame is logged and forwarded to remote server
    """
    def rnet_daemon(self, listensock, sendsock, logger_tag):
        logger.debug("Rnet listener daemon started")

        record = True
        
        while record:
            rnetFrame = can2RNET.canrecv(listensock)
            frameToLog  = binascii.hexlify(rnetFrame)
            logger.debug('%s:%s\n' %(logger_tag, frameToLog))
            self.logfile.write('%s:%s\n' %(logger_tag, frameToLog))
            can2RNET.cansendraw(sendsock, rnetFrame)

            # Check end of init condition
            __, __, frameName = RnetDissector.getFrameType(rnetFrame)
            if frameName == 'END_OF_INIT':
                record = False



"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port0tag", type=str, default="MOTOR", help="Defines logger tag like 'MOTOR' for Rx-CAN0 stream. Default is 'MOTOR'")
    parser.add_argument("--port1tag", type=str, default="JSM", help="Defines logger tag like 'JSM' for Rx-CAN1 stream. Default is 'JSM'")
    parser.add_argument("--outfile", type=str, default="init.log", help="JMS init sequence filename, default is 'init.log'")
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")

    return parser.parse_args()



"""
Configuration using one raspi with dual port pican boards.
"""
def picanDualCase(outfile, port0tag, port1tag):
    # Start Rnet listener daemon
    with open(outfile,"w") as outfile:

        # Connect and initialize Rnet controller
        # Will listen for Rnet frames and transmit
        # them to other Rnet Port
        rnet = RnetDualLogger(port0tag, port1tag, outfile)
        daemon0, daemon1 = rnet.start_daemons()

        daemon0.join()
        daemon1.join()



if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    picanDualCase(args.outfile, args.port0tag, args.port1tag)

