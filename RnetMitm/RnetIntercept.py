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

logger = can2RNET.logger

"""
Rnet Man in the middle logger
Supports two configurations:
    - 2 raspberry + Can boards architecture 
    or
    - 1 raspberry + Dual Can board architecture

Will be placed between JSM and main controller to log all messages with source name.
"""


TCP_BUFFER_SIZE = 1024


"""
R-net class for two raspi and pican single port logging
"""
class RnetIPLogger(threading.Thread):

    def __init__(self, rIp, rPort, logger_tag, logfile):
        self.cansocket = None
        self.sock = None
        self.rIp = rIp
        self.rPort = rPort
        self.server_nopresent = True
        self.logger_tag = logger_tag
        self.logfile = logfile
        
        threading.Thread.__init__(self)
        logger.info("Opening socketcan")
        try:
            self.cansocket = can2RNET.opencansocket(0)
        except :
            logger.error("socketcan can0 cannot be opened! Check connectivity")
            sys.exit(1)


    def sendFrame(self, data):
        can2RNET.cansendraw(self.cansocket, data)


    """
    Used for 2 raspi config with IP link
    """
    def start_daemon(self):

        # launch daemon
        logger.debug("Starting IP Rnet daemon")
        daemon = threading.Thread(target=self.rnet_daemon, daemon=True)
        daemon.start()
        return daemon


    """
    Endless loop waiting for Rnet frames
    Each frame is logged and forwarded to remote server
    """
    def rnet_daemon(self):
        logger.debug("Rnet listener daemon started")
        
        # Rnet listener daemon
        while(self.server_nopresent):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_address = (self.rIp, self.rPort)
                self.sock.connect(server_address)
                self.server_nopresent = False
                logger.info("Connected to distant server")
            except:
                logger.error("Connecting to %s:%d failed" %(self.rIp, self.rPort))
                time.sleep(2)

        # sending joystick frame @100Hz
        while True:
            rnetFrame = can2RNET.canrecv(self.cansocket)
            self.logfile.write('%s: %r\n' %(self.logger_tag,can2RNET.dissect_frame(rnetFrame)))
            self.sock.send(rnetFrame)


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
        
        # sending joystick frame @100Hz
        while True:
            rnetFrame = can2RNET.canrecv(listensock)
            logger.debug('%s: %r\n' %(logger_tag,can2RNET.dissect_frame(rnetFrame)))
            self.logfile.write('%s\t %s.%s.%s \t%s: %r\n' %(time.clock_gettime(0), 
                                                            binascii.hexlify(rnetFrame[0:4]),
                                                            binascii.hexlify(rnetFrame[4:8]),
                                                            binascii.hexlify(rnetFrame[8:]), 
                                                            logger_tag, 
                                                            can2RNET.dissect_frame(rnetFrame)))
            can2RNET.cansendraw(sendsock, rnetFrame)


"""
Server will wait for a distant connection and transmit all received frames
on the Rnet bus.
"""
class server():

    def __init__(self, ip, port, iptag, rnet, logfile):
        self.ip = ip
        self.port =port
        self.rnet = rnet
        self.iptag = iptag
        self.logfile = logfile

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.ip, self.port))
            logger.info('server socket bind ok')
        except:
            logger.error("binding socket to %s:%d failed" %(self.ip, self.port))
            sys.exit(1)


    def start(self):         
            
        while True:
            logger.info('Wait for new connection on %s:%d' %(self.ip, self.port))
            self.s.listen(1)
            conn, addr = self.s.accept()
            logger.info('Accept connection from: %r' %addr[0])
            while True:
                data = conn.recv(TCP_BUFFER_SIZE)
                self.logfile.write('%s: %r\n' %(self.iptag,can2RNET.dissect_frame(data)))
                self.rnet.sendFrame(data)

            logger.info('TCP connection closed')
            conn.close()



"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lIp", type=str, default="192.168.1.146", help="Defines local server IPv4 address to listen, default is '192.168.1.146'")
    parser.add_argument("--lPort", type=int, default="4146", help="Defines local server port to listen, default is 4146")
    parser.add_argument("--rIp", type=str, default="192.168.1.145", help="Defines remote IPv4 address to connect, default is '192.168.1.145'")
    parser.add_argument("--rPort", type=int, default="4145", help="Defines remote port to connect, default is 4145")
    parser.add_argument("--cantag", type=str, default="JSM", help="Defines logger tag like 'JSM' for Rx-CAN0 stream. Default is 'JSM'")
    parser.add_argument("--iptag", type=str, default="MOTOR", help="Defines logger tag like 'MOTOR' for Rx-IP or Rx-CAN1 stream. Default is 'MOTOR'")
    parser.add_argument("--logfile", type=str, default="logfile.txt", help="Output can log filename")
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("--dual", help="'PICAN2 Dual' board case, no need to have 2 raspi. IP/port inputs not required", action="store_true")


    return parser.parse_args()


"""
Configuration using two raspi with single port pican boards.
"""
def picanCase(args):
    # Start Rnet listener daemon
    with open(args.logfile,"w") as logfile:

        # Connect and initialize Rnet controller
        # Will listen for Rnet frames and transmit
        # them to distant TCP server
        rnet = RnetIPLogger(args.rIp,args.rPort, args.cantag, logfile)
        serv = server(args.lIp, args.lPort, args.iptag, rnet, logfile)

        # Start position daemon
        rnet.start_daemon()

        # Start TCP listener daemon
        # Will listen for TCP frames and transmit
        # them on Rnet bus
        serv.start()


"""
Configuration using one raspi with dual port pican boards.
"""
def picanDualCase(args):
    # Start Rnet listener daemon
    with open(args.logfile,"w") as logfile:

        # Connect and initialize Rnet controller
        # Will listen for Rnet frames and transmit
        # them to other Rnet Port
        rnet = RnetDualLogger(args.cantag, args.iptag, logfile)
        daemon0, daemon1 = rnet.start_daemons()

        daemon0.join()
        daemon1.join()

"""
Record JSM Initialization sequence
Use logfile as output file
"""
def recInitSequence(args):
    with open(args.logfile,"w") as logfile:

        # Connect and initialize Rnet controller
        # Will listen for Rnet frames and transmit
        # them to distant TCP server
        rnet = RnetDualLogger(args.cantag, args.iptag, logfile)
        daemon0, daemon1 = rnet.start_daemons()

        daemon0.join()
        daemon1.join()



if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if args.dual is False:
        picanCase(args)
    else:
        picanDualCase(args)

