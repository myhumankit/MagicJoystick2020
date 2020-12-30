#!/python3
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


logger = can2RNET.logger


# Default constants:
ID_JOY_CONTROL    = '02001100'  # may differ according to your setup
ID_JOY_NULL       = '02000200'  # may differ according to your setup, not used
RNET_XY_FRAME_HEADER = '02000000:FF000000'
NEUTRAL_JOY_POSITION = '00.00'

TCP_BUFFER_SIZE = 1024



"""
convert dec to hex with leading 0s and no '0x'
"""
def dec2hex(dec, hexlen):
    h = hex(int(dec))[2:]
    l = len(h)
    if h[l-1] == "L":
        l -= 1  # strip the 'L' that python int sticks on
    if h[l-2] == "x":
        h = '0'+hex(int(dec))[1:]
    return ('0'*hexlen+h)[l:l+hexlen]


"""
Basic commands over Rnet 
"""
RNET_DICT={
    'JSM_CONNECT'          : '0c000000#', #'00c#'
    'JSM_SERIAL'           : '0e000000#9700148100000000',
    'JSM_SERIAL_REQ'       : 'b3070000#',
    'JMS_CFG_MODE1_REQ'    : '000007b1#',
    'JSM_UI_READY'         : '1c240101#',      # 1c24XX01, XX=device
    'JSM_SPEED_CFG'        : '0a04XXYY#00',    # XXYY is the JSM identifier eg '1100' used for joystick position
    'JSM_JOY_POS'          : '0200XXYY#xxyy',  # XXYY is the JSM identifier, xxyy joystick position

    'PM_SERIAL_ACK'        : '0007b3#R',
    'PM_CFG_MODE1_ACK'     : '0007b0#',
    'PM_BATTERY_LEVEL'     : '1C0CXX00#YY',    # XX=device, YY=power level in % Xx = 0x00 - 0x64. Periodic: 1000ms
    'PM_HEARTBEAT'         : '0c140000#XX',
    'PM_CONNECTED'         : '0c280000#00',    # Sent only once after serial exchange
}

RNET_RAW_DICT={
    'JSM_CONNECT'          : binascii.unhexlify(b'0c000000000000000000000000000000'),
    'JSM_SERIAL'           : binascii.unhexlify(b'0e000000080000009700148100000000'),
    'JSM_SERIAL_REQ'       : binascii.unhexlify(b'b3070000000000000000000000000000'),
    'JMS_CFG_MODE1_REQ'    : binascii.unhexlify(b'b1070000000000000000000000000000'),
    'JSM_UI_READY'         : '1c240101#',      # 1c24XX01, XX=device
    'JSM_SPEED_CFG'        : '0a04XXYY#00',    # XXYY is the JSM identifier eg '1100' used for joystick position
    'JSM_JOY_POS'          : '0200XXYY#xxyy',  # XXYY is the JSM identifier, xxyy joystick position

    'PM_SERIAL_ACK'        : '0007b3#R',
    'PM_CFG_MODE1_ACK'     : '0007b0#',
    'PM_BATTERY_LEVEL'     : '1C0CXX00#YY',    # XX=device, YY=power level in % Xx = 0x00 - 0x64. Periodic: 1000ms
    'PM_HEARTBEAT'         : '0c140000#XX',
    'PM_CONNECTED'         : '0c280000#00',    # Sent only once after serial exchange
}


SERIAL_PERIOD = 0.05
SERIAL_REQ_PERIOD = 0.03



"""
JMS PowerOn class will substitute to a legacy JSM 
So you can poweron raspberry witout the need to 
poweron the JMS
"""
class JsmPowerOn(threading.Thread):

    def __init__(self, cansocket):
        self.cansocket = cansocket
        threading.Thread.__init__(self)


    """
    Sending periodic 50ms serial number <Thread>
    """
    def serialDaemon(self):
        while True:
            time.sleep(SERIAL_PERIOD)
            can2RNET.cansendraw(self.cansocket, RNET_RAW_DICT['JSM_SERIAL'])


    def startSerialDaemon(self):
        daemon = threading.Thread(target=self.serialDaemon, daemon=True)
        daemon.start()
        return daemon


    def reqack(self, req, ack):

        can2RNET.cansendraw(self.cansocket, req)
        ack_frame = can2RNET.canrecvTimeout(self.cansocket, SERIAL_REQ_PERIOD)

        pm_answer = ''

        if ack_frame is not b'':
            pm_answer = can2RNET.dissect_frame(ack_frame)
            logger.debug("Wait for PM %s, got : %s" %(ack, pm_answer))
        else:
            logger.debug("Wait for PM %s, got : TIMEOUT" %(req))

        while pm_answer != ack:
            can2RNET.cansendraw(self.cansocket, req)
            ack_frame = can2RNET.canrecvTimeout(self.cansocket, SERIAL_REQ_PERIOD)

            if ack_frame is not b'':
                pm_answer = can2RNET.dissect_frame(ack_frame)
                logger.debug("Wait for PM %r, got : %r" %(ack, pm_answer))
            else:
                logger.debug("Wait for PM %s, got : TIMEOUT" %(req))


    def powerOn(self):

        # Send JSM wake up to PM
        can2RNET.cansendraw(self.cansocket, RNET_RAW_DICT['JSM_CONNECT'])
        time.sleep(0.2)

        # start periodic serial info send thread:
        self.startSerialDaemon()

        # Initiate serial exchange, and wait for ack from PM
        self.reqack(RNET_RAW_DICT['JSM_SERIAL_REQ'], RNET_DICT['PM_SERIAL_ACK'])        


        logger.info("BOOT: get serial ack from pm")

        binascii.hexlify(dd)
        # Receive serial frames from PM  
        # assuming a 500ms timeout PM tells serial has benn sent
        data = 0
        while data is not None:
            data = can2RNET.canrecvTimeout(self.cansocket, 0.5)
            time.sleep(0.5)
            logger.info("BOOT: got serial data %r" %data)

        # Tell PM that JSM UI is ready and wait for PM connected answer

        can2RNET.cansend(self.cansocket, RNET_DICT['JSM_UI_READY'])

        pm_answer = ''
        while pm_answer is not RNET_DICT['PM_CONNECTED']:
            time.sleep(0.1) 
            pm_answer = can2RNET.dissect_frame(can2RNET.canrecv(self.cansocket))

        logger.info("BOOT: get pm connected !")


"""
Main R-net class to send joystick frames on the bus
and take the control over the legacy JSM

input: "jsm_address" is the identification of the wheelchair JSM
                    this is specific to each JSM and has to be tuned
                    example : '02001100' for our test wheelchair
"""
class RnetControl(threading.Thread):

    # Constants :
    FRAME_JSM_INDUCE_ERROR = '0c000000#'
    POSITION_FREQUENCY = 0.01   # 100Hz
    NB_XY_FRAME = 20 

    def __init__(self, jsm_address, testmode = False):
        self.joy_x = 0
        self.joy_y = 0
        self.cansocket = None
        self.jsm_address = jsm_address
        self.testmode = testmode
        threading.Thread.__init__(self)
        logger.info("Opening socketcan")
        try:
            if testmode is False:
                self.cansocket = can2RNET.opencansocket(0)
                self.cansend = can2RNET.cansend
            else:
                logger.warning("Switching in test mode, do not connect to CAN bus")
                self.cansend = self.dummy
        except :
            logger.error("socketcan cannot be opened! Check connectivity")
            sys.exit(1)

        self.powerOn = JsmPowerOn(self.cansocket)



    def dummy(self, arg0, arg1):
        pass

    
    """
    WIP : autodetect frame address
    """
    def get_xy_frame_id(self, frame):
        return frame[4:8]

    def get_xy_frame_values(self, frame):
        x = struct.unpack("I", frame[:4])[0]

        return frame.split('#')[1]

    """
    WIP : This function will try to identify audomatically the current JSM address
    """
    def get_jsm_header(self):

        positionFrames = []       

        for _ in range(self.NB_XY_FRAME):
            positionFrames.append(can2RNET.canwait(rnet.cansocket, RNET_XY_FRAME_HEADER))


    """
    This function will send 5 frames to the JSM and will crash it
    This is necessary to take the control on the wheel chair
    Idealy this function should not be send...
    """
    def send_jsm_exploit(self):
        logger.debug("Inducing JSM error by sending 5 frames of type '0c000000#'")
        # send in less than 1ms theses frames to induce JSM error
        for _ in range(5):
            self.cansend(self.cansocket, self.FRAME_JSM_INDUCE_ERROR)


    """
    Function to be called when a new position is received from positionning client
    """
    def update_joy_position(self, data):
        x = str(data).split('.')[0]
        y = str(data).split('.')[1]
        logger.debug("Update position: x=%r, y=%r" %(x,y))
        self.joy_x = x
        self.joy_y = y


    def createJoyFrame(self, id_control, joystick_x, joystick_y):
        joyframe = id_control+'#' + \
            dec2hex(joystick_x, 2)+dec2hex(joystick_y, 2)
        return joyframe

    """
    Function to be called periodically to send new joy command to Rnet bus
    """
    def send_joy_position(self):
        joyframe = self.createJoyFrame(ID_JOY_CONTROL, self.joy_x, self.joy_y)
        logger.debug("Sending Rnet frame: %s" %joyframe)
        self.cansend(self.cansocket, joyframe)


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
    parser.add_argument("--ip", type=str, default="0.0.0.0", help="Define server IPv4 address to listen, default is '0.0.0.0'")
    parser.add_argument("--port", type=int, default="4141", help="Define server portto listen, default is 4141")
    parser.add_argument("--rnetaddr", type=str, default=ID_JOY_CONTROL, help="Define Rnet wheelchair JSM address, default is %s" %ID_JOY_CONTROL)
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("-t", "--test", help="Test mode, do not connect to CAN bus", action="store_true")

    return parser.parse_args()

if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)


    # Connect and initialize Rnet controller:
    rnet = RnetControl(args.rnetaddr, args.test)

    rnet.powerOn.powerOn()
    # Start Rnet controller
    try:
        
        # WIP
        # Autodetect the JSM address that controls 
        # X/Y commands
        # rnet.get_jsm_header()

        # Send exploit to crash JSM
        rnet.send_jsm_exploit()
        # Start position daemon
        deamon = rnet.start_daemon()
        
    except:
        logger.error("Cannot start Rnet controller")
        sys.exit(1)


    # Start Joy or any positionning sensor server listener
    serv = server(args.ip, args.port, rnet)
    serv.start()
