#!/usr/bin/python3
import os
import threading
import argparse
import time
import sys
import binascii
import logging
from magick_joystick.can2RNET import can2RNET, RnetDissector
logger = can2RNET.logger

"""
Rnet JSM init sequence recorder and playback
Must use a raspberry + Dual Can board architecture

Will be placed between JSM and main controller to log all messages with source name
in case of record mode, or replace JSM incase of playback.

For the recording init sequence, the following frame sequences will
be tagged:

    JSM   0000006xxxx
    MOTOR 0000006xxxx
    => Init sequence done

    Then, waiting for either JoyPosition frame or MaxSpeed frame
    to get the JSM identifier value.

    Then init sequence recording is completed.

"""

FOLDER='sequences/'
RPI_INIT_FILE = FOLDER + 'rpi_init.log'
RPI_RECONF_FILE = FOLDER + 'rpi_reconf.log'
RPI_OFF_FILE = FOLDER + 'rpi_off.log'




#Only init sequence
class RnetInitSeqRecorder(threading.Thread):

    is_jsm_identified = False
    init = False
    device_id = None

    def __init__(self, logfilePath):
        """R-net class for single raspi and pican dual port init sequence recording"""

        self.cansocket0 = None
        self.cansocket1 = None
        self.logfile = open(logfilePath, "w")

        self.print_rec_procedure()

        threading.Thread.__init__(self)
        logger.info("Opening socketcan")
        try:
            self.cansocket0 = can2RNET.opencansocket(0)
        except:
            logger.error("socketcan can0 cannot be opened! Check connectivity")
            sys.exit(1)
        try:
            self.cansocket1 = can2RNET.opencansocket(1)
        except:
            logger.error("socketcan can1 cannot be opened! Check connectivity")
            sys.exit(1)

    def print_rec_procedure(self):
        print("\n\
        Procedure to generate '%s' file :\n\
            1- Connect the wheelchair JSM to dualPican port1\n\
            2- Connect the wheelchair Motor to dualPican port2\n\
            3- launch this program: 'python3 rnet_sequence_recorder.py -d'\n\
            4- Power On the JSM and wait for the program to complete\n\
            5- After program ends, power Off the JSM\n\
        The %s file will be created with the JSM init sequence\n" %(RPI_INIT_FILE, RPI_INIT_FILE))

    def start_daemons(self):
        """
        used for single raspi and pican dual config
        """
        # launch daemon
        logger.debug("Starting Rnet Dual daemons")
        daemon0 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket0, self.cansocket1, 'PORT0'], daemon=True)
        daemon0.start()
        daemon1 = threading.Thread(target=self.rnet_daemon, args=[self.cansocket1, self.cansocket0, 'PORT1'], daemon=True)
        daemon1.start()
        return daemon0, daemon1


    def rnet_daemon(self, listensock, sendsock, logger_tag):
        """
        Endless loop waiting for Rnet frames\n
        Each frame is logged in order to be repeated
        """
        logger.debug("Rnet listener daemon started")
        is_motor = False
        is_serial = False

        while self.init is False or self.is_jsm_identified is False:
            rnetFrame = can2RNET.canrecv(listensock)
            frameToLog  = binascii.hexlify(rnetFrame)
            logger.debug('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))
            self.logfile.write('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))
            can2RNET.cansendraw(sendsock, rnetFrame)

            # Check end of init condition
            _, _, device_id, frameName, data, _, _ = RnetDissector.getFrameType(rnetFrame)
            if frameName == 'END_OF_INIT':
                self.init = True
            
            # Check current thread is MOTOR or JMS
            if frameName == 'PMTX_CONNECT':
                logger.debug('********** PMTX_CONNECT frame received **********\n')
                is_motor = True

            # Memorize serial
            if is_serial is False and frameName == 'SERIAL':
                logger.debug('********** SERIAL frame received **********\n')
                self.jsm_serial = data
                is_serial = True

            # In case thread is JSM side, wait for 
            # a joy position to record JSM ID
            if is_motor is False and self.init is True:
                if frameName == 'JOY_POSITION':
                    logger.debug('********** Got JMS ID: 0x%x **********\n' %device_id)
                    self.logfile.write('-1.0:DEVICE_ID:0x%x\n' %device_id)
                    self.logfile.write('-1.0:JOY_SERIAL:%s\n' %binascii.hexlify(self.jsm_serial))
                    self.is_jsm_identified = True


class RnetSequencesRecorder(threading.Thread):

    is_jsm_identified = False
    init = False
    device_id = None

    def __init__(self):
        """
        R-net class for reconfiguration, init sequences, and turn OFF sequence recording.\n
        To use this class, make sure that the next power on of the JSM will do an reconfiguration sequence. 
        Launch the script with '-r' coption, then turn on the JSM.
        At the end of the sequence, turn off then on the JSM to start the init sequence recording.
        The two sequences will be saved in .log files
        """

        self.cansocket0 = None
        self.cansocket1 = None
        self.reconfFile = open(RPI_RECONF_FILE, "w")
        self.initFile = open(RPI_INIT_FILE, "w")
        self.offFile = open(RPI_OFF_FILE, "w")

        self.print_rec_procedure()

        threading.Thread.__init__(self)

    def print_rec_procedure(self):
        print("\n\
        Procedure to generate all needed files :\n\
            0- Make sure that the reconfiguration sequence will be lunch at the next JSM power ON\n\
            1- Connect the wheelchair JSM to dualPican port1\n\
            2- Connect the wheelchair Motor to dualPican port2\n\
            3- launch this program: 'python3 rnet_sequence_recorder.py -r'\n\
            4- Power On the JSM and wait for the reconfiguration sequence to complete.\n\
            5- Power Off the JSM (the program will record it automaticaly)\n\
            6- Turn ON the JSM to record the init sequence (automaticaly)\n\
            7- Wait for the program to finish\n\
        The needed files will be created inthe folder '%s' with the 3 sequence\n" %(FOLDER))

    def openSock(self):
        print("Opening socketcan")
        try:
            self.cansocket0 = can2RNET.opencansocket(0)
        except:
            logger.error("socketcan can0 cannot be opened! Check connectivity")
            sys.exit(1)
        try:
            self.cansocket1 = can2RNET.opencansocket(1)
        except:
            logger.error("socketcan can1 cannot be opened! Check connectivity")
            sys.exit(1)
    def closeSock(self):
        self.cansocket0.close()
        self.cansocket1.close()

    def startAllRecords(self):

        self.openSock()
        # First phase, record reconf sequence
        print("Starting Rnet Dual daemons for reconfiguration record")
        dems = self.start_daemons(self.rnet_daemon_reconf)
        for d in dems:
            d.join()
        self.reconfFile.close()
        self.offFile.close()
        self.closeSock()
        print(" ===== Done with reconfiguration sequence ===== ")
        print(" =====     Done with turn off sequence    ===== ")

        time.sleep(.5)

        #Then the init sequence
        self.openSock()
        print("Starting Rnet Dual daemons for init sequence record")
        dems = self.start_daemons(self.rnet_daemon_init)
        for d in dems:
            d.join()
        self.initFile.close()
        self.closeSock()
        

    def start_daemons(self, target):
        # launch daemon
        daemon0 = threading.Thread(target=target, args=[self.cansocket0, self.cansocket1, 'PORT0'], daemon=True)
        daemon1 = threading.Thread(target=target, args=[self.cansocket1, self.cansocket0, 'PORT1'], daemon=True)
        daemon0.start()
        daemon1.start()
        return daemon0, daemon1

    def rnet_daemon_reconf(self, listensock, sendsock, logger_tag):
        """
        Endless loop waiting for Rnet frames\n
        Each frame is logged in order to be repeated\n
        Capture also the powerOFF sequence
        """
        print("Rnet Reconf daemon started")

        gotPowerOff = False

        while True:

            if gotPowerOff is False: #Before the user turn the JSM off
                rnetFrame = can2RNET.canrecv(listensock)
            else: #Once user turn off the JSM
                rnetFrame = can2RNET.canrecvTimeout(listensock, 0.5)
                if rnetFrame == b'':
                    break

            can2RNET.cansendraw(sendsock, rnetFrame)
            frameToLog  = binascii.hexlify(rnetFrame)

            # Check end of init condition
            _, _, _, frameName, _, _, _ = RnetDissector.getFrameType(rnetFrame)
            if gotPowerOff is False and frameName == 'POWER_OFF':
                gotPowerOff = True
            
            logger.debug('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))
            l = '%s:%s:%s\n' %(time.time(), logger_tag, frameToLog)
            self.reconfFile.write(l) # We keep the poweroff sequence in the reconfig file to turn off the motor automaticaly after reconfiguration
            if gotPowerOff:
                self.offFile.write(l)
        


    def rnet_daemon_init(self, listensock, sendsock, logger_tag):
        """
        Endless loop waiting for Rnet frames\n
        Each frame is logged in order to be repeated
        """
        print("Rnet init daemon started")
        is_motor = False
        is_serial = False

        while self.init is False or self.is_jsm_identified is False:
            rnetFrame = can2RNET.canrecv(listensock)
            frameToLog  = binascii.hexlify(rnetFrame)
            logger.debug('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))
            self.initFile.write('%s:%s:%s\n' %(time.time(), logger_tag, frameToLog))
            can2RNET.cansendraw(sendsock, rnetFrame)

            # Check end of init condition
            _, _, device_id, frameName, data, _, _ = RnetDissector.getFrameType(rnetFrame)
            if frameName == 'END_OF_INIT':
                self.init = True
            
            # Check current thread is MOTOR or JMS
            if frameName == 'PMTX_CONNECT':
                print('===== PMTX_CONNECT frame received =====\n')
                is_motor = True

            # Memorize serial
            if is_serial is False and frameName == 'SERIAL':
                print('===== SERIAL frame received =====\n')
                self.jsm_serial = data
                is_serial = True

            # In case thread is JSM side, wait for 
            # a joy position to record JSM ID
            if is_motor is False and self.init is True:
                if frameName == 'JOY_POSITION':
                    print('===== Got JMS ID: 0x%x =====\n' %device_id)
                    self.initFile.write('-1.0:DEVICE_ID:0x%x\n' %device_id)
                    self.initFile.write('-1.0:JOY_SERIAL:%s\n' %binascii.hexlify(self.jsm_serial))
                    self.is_jsm_identified = True



class RnetSeqReplayer(threading.Thread):

    def __init__(self, sourcePath):
        """
        RnetSeqReplayer class will send sequence saved into 'sourcePath', to the motor\n
        You can use an reconfiguration, turn OFF or init sequences. It will be replayed.
        """
        self.device_id = None
        self.jsm_serial = None
        
        try:
            with open(sourcePath,"r") as infile:
                self.jsm_cmds = infile.readlines()
                if len(self.jsm_cmds) == 0:
                    logger.error("[RnetSeqReplayer] The source file %s is empty, make sure to use '-r' option to create all needed files" %sourcePath)
                    sys.exit(1)
        except:
            logger.error("[RnetSeqReplayer] The JMS init file %s is not present, make sure to use '-r' option to create all needed files" %sourcePath)
            sys.exit(1)

        if 'PORT0' in self.jsm_cmds[0]:
            logger.info("[RnetSeqReplayer] JSM connected on port0 and motor on port1")
            self.motor_port = 1
            self.jsm_port = 0
        else:
            logger.info("[RnetSeqReplayer] JSM connected on port1 and motor on port0")
            self.motor_port = 0
            self.jsm_port = 1

        # Set initial timeFrame
        self.timeFrame = float(self.jsm_cmds[0].split(':')[0])

        # Retreive the JSM ID from logs: (only if it's the init sequence, otherwise this is useless)
        for line in self.jsm_cmds:
            if 'DEVICE_ID' in line:
                self.device_id = int(line.split(':')[2],16)
                logger.info("[RnetSeqReplayer] DEVICE_ID: 0x%x" %self.device_id)
            if 'JOY_SERIAL' in line:
                self.jsm_serial = binascii.unhexlify(line.split("'")[1])
                logger.info("[RnetSeqReplayer] JSM serial: %r" %self.jsm_serial)

        # Open motor can socket, assuming at first that the port is identical
        # to the init file. If not, try the other port as init sequence recording
        # is done on a dual port pican, but final project can use a less expensive
        # single port pican board.
        threading.Thread.__init__(self)
        logger.info("[RnetSeqReplayer] Opening socketcan")
        try:
            self.motor_cansocket = can2RNET.opencansocket(self.motor_port)
        except:
            logger.error("[RnetSeqReplayer] socketcan %d cannot be opened! Trying the other port" %self.motor_port)
            # Try the other socket as recording can be done on a dual pican but the environment
            # raspberry controller can use a single port pincan
            try:
                self.motor_cansocket = can2RNET.opencansocket(self.jsm_port)
            except:
                logger.error("[RnetSeqReplayer] socketcan %d cannot be opened either! Check connectivity" %self.jsm_port)
                sys.exit(1)


    def sequence_start(self):
        """
        Start sequence, blocking function call until init sequence
        fully completed.
        """
        daemon = threading.Thread(target=self.seq_daemon, args=[], daemon=True)
        daemon.start()
        daemon.join()
        return self.device_id, self.jsm_serial


    def get_next_frame(self, idx):
        timeFrame, port, frame = self.jsm_cmds[idx].split(':')
        if 'PORT' in port:
            bin_frame = binascii.unhexlify(frame.strip("\n").split("'")[1])
            return float(timeFrame), port, bin_frame
        else:
            return -1.0, 'NONE', b'\x00'

    
    def seq_daemon(self):
        """
        Will send the frames stored in the file and wait for Motor answer
        Once done thread exits
        """
        print("[RnetSeqReplayer] Rnet JSM init daemon started")
        frame_idx = 0
        JSMport = "PORT%d" %self.jsm_port
        MOTORport = "PORT%d" %self.motor_port
        max_idx = len(self.jsm_cmds)

        print("[RnetSeqReplayer] Proceeding a total of %d frames" %max_idx)

        while frame_idx < max_idx:

            currentTimeFrame, port, frame = self.get_next_frame(frame_idx)


            if port == JSMport:
                RnetDissector.printFrame(frame)
                time.sleep(currentTimeFrame - self.timeFrame )
                logger.debug("[RnetSeqReplayer] %d: sleep(%s) - Sending JSM frame %s" %(frame_idx, currentTimeFrame - self.timeFrame ,binascii.hexlify(frame)))
                can2RNET.cansendraw(self.motor_cansocket, frame)

            elif port == MOTORport:
                RnetDissector.printFrame(frame)
                rnetFrame = can2RNET.canrecv(self.motor_cansocket)
                logger.debug('[RnetSeqReplayer] %d: Receive MOTOR frame %s\n' %(frame_idx, binascii.hexlify(rnetFrame)))

            else:
                logger.debug('[RnetSeqReplayer] %d: %r / %r Unsupported frame: %r, %r' %(frame_idx, JSMport, MOTORport, port, frame))
                pass

            self.timeFrame =  currentTimeFrame
            frame_idx += 1



def parseInputs():
    """
    Argument parser definition
    """
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")

    parser.add_argument("-r", "--reconfig", help="Record the reconfiguration sequence, the turn OFF sequence, and the init sequence.", action="store_true")
    parser.add_argument("-c", "--config_test", help="Lauch reconfiguration sequence by sending it to the motor socket.", action="store_true")

    parser.add_argument("-i", "--recInit", help="Record the init sequence in file '%s' (prefer the '-r' argument)"%RPI_INIT_FILE, action="store_true")
    parser.add_argument("-t", "--test_init", help="Test init sequense by sending it to the motor socket.", action="store_true")
    return parser.parse_args()



if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    try:
        os.mkdir(FOLDER)
    except: # Ignore any failure (most of the time the dir is already created)
        pass


    if args.debug:
        logger.setLevel(logging.DEBUG)
        sys.argv
    
    if args.reconfig:
        req = RnetSequencesRecorder()
        req.startAllRecords()

    elif args.config_test:
        print("Relunching reconfiguration sequence preparation...")
        jsm = RnetSeqReplayer(sourcePath=RPI_RECONF_FILE)
        print("Relunching reconfiguration sequence now...")
        jsm.sequence_start()
    
    elif args.test_init:
        jsm = RnetSeqReplayer(sourcePath=RPI_INIT_FILE)
        jsm.sequence_start()

    elif args.recInit: #Useless option, use '-r' to get all sequences instead
        rnet = RnetInitSeqRecorder(RPI_INIT_FILE)
        daemon0, daemon1 = rnet.start_daemons()
        daemon0.join()
        daemon1.join()
    
    print("Use '-h' option for help.")
