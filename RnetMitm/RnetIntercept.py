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
RnetIntercept is a 2 raspberry + Can boards architecture to perform man in the middle on the can bus
between JSM and main controller.
"""


TCP_BUFFER_SIZE = 1024


"""
Main R-net class to send joystick frames on the bus
and take the control over the legacy JSM

input: "jsm_address" is the identification of the wheelchair JSM
                    this is specific to each JSM and has to be tuned
                    example : '02001100' for our test wheelchair
"""
class RnetLogger(threading.Thread):

    def __init__(self, rIp, rPort, logger_tag, logfile, rawlog):
        self.cansocket = None
        self.sock = None
        self.rIp = rIp
        self.rPort = rPort
        self.server_nopresent = True
        self.logger_tag = logger_tag
        self.logfile = logfile
        self.rawlog = rawlog
        
        threading.Thread.__init__(self)
        logger.info("Opening socketcan")
        try:
            self.cansocket = can2RNET.opencansocket(0)
        except :
            logger.error("socketcan cannot be opened! Check connectivity")
            sys.exit(1)


    def sendFrame(self, data):
        can2RNET.cansendraw(self.cansocket, data)


    def start_daemon(self):

        # launch daemon
        logger.debug("Starting Rnet daemon")
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
            if self.rawlog:
                self.logfile.write('%s - %s: %r\n' %(time.monotonic(), self.logger_tag,binascii.hexlify(rnetFrame)))
            else:
                self.logfile.write('%s - %s: %r\n' %(time.monotonic(), self.logger_tag,can2RNET.dissect_frame(rnetFrame)))
            self.sock.send(rnetFrame)


"""
Server will wait for a distant connection and transmit all received frames
on the Rnet bus.
"""
class server():

    def __init__(self, ip, port, iptag, rnet, logfile, rawlog):
        self.ip = ip
        self.port =port
        self.rnet = rnet
        self.iptag = iptag
        self.logfile = logfile
        self.rawlog = rawlog
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
                if not data: break
                if self.rawlog:
                    self.logfile.write('%s - %s: %r\n' %(time.monotonic(), self.iptag,binascii.hexlify(data)))
                else:
                    self.logfile.write('%s - %s: %r\n' %(time.monotonic(), self.iptag,can2RNET.dissect_frame(data)))
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
    parser.add_argument("--cantag", type=str, default="JSM", help="Defines logger tag like 'JSM' for CAN stream. Default is 'JSM'")
    parser.add_argument("--iptag", type=str, default="MOTOR", help="Defines logger tag like 'MOTOR' for IP stream. Default is 'MOTOR'")
    parser.add_argument("--logfile", type=str, default="logfile.txt", help="Output can log filename")
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("-r", "--raw", help="Log raw binary", action="store_true")

    return parser.parse_args()

if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Start Rnet listener daemon
    with open(args.logfile,"w") as logfile:

        # Connect and initialize Rnet controller
        # Will listen for Rnet frames and transmit
        # them to distant TCP server
        rnet = RnetLogger(args.rIp,args.rPort, args.cantag, logfile, args.raw)
        serv = server(args.lIp, args.lPort, args.iptag, rnet, logfile, args.raw)

        # Start position daemon
        deamon = rnet.start_daemon()

        # Start TCP listener daemon
        # Will listen for TCP frames and transmit
        # them on Rnet bus
        serv.start()
        

