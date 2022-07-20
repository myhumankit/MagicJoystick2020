import binascii
import threading
import argparse
import time
import logging
from rnet_can_JSMsub import RnetCanJSMsub
import paho.mqtt.client as mqtt
from magick_joystick.can2RNET import can2RNET, RnetDissector
from magick_joystick.Topics import *

logger = can2RNET.logger

"""
Main R-net class to Act just like a JSM (using only one can interface)
"""
class RnetControlJSMsub(threading.Thread):

    POSITION_FREQUENCY = 0.01   # 100Hz - RNET requirement
    STATUS_FREQUENCY = 0.5        # 2Hz
    JOY_WATCHDOG_TIMEOUT = 20   # Force joystick position to [0,0] after 200ms without data.
    ACTUATOR_FREQUENCY = 0.05   # 20 Hz
    ACTUATOR_WATCHDOG_TIMEOUT = 6 # 700ms (assume mqtt publish every 2Hz / 500ms)
    SERIAL_FREQUENCY = 0.05     # 50 ms period
    JSM_HEARTBEAT_PERIOD = 0.1 #10Hz
    AUTO_LIGHT_PERIOD = 0.25
    power_state = False

    light_state = [False,False,False] # flashing left, flashing right, Warnning
    auto_light = False

    def __init__(self):
        """
        Main R-net class to Act just like a JSM (using only one can interface)
        """
        self.RnetHorn = None
        self.threads = None
        # self.hornThread = None
        self.drive_mode = False
        self.battery_level = 0
        self.chair_speed = 0.0
        self.joy_watchdog = 0
        self.actuator_watchdog = 0
        
        threading.Thread.__init__(self)
        
        logger.info("========== START ========== ")

        # Open can socket to prepare JSM power_on
        logger.info("Opening socketcan...")
        self.rnet_can = RnetCanJSMsub()
        self.cansend = can2RNET.cansendraw

        try:
            self.mqtt_client = mqtt.Client() 
            self.mqtt_client.on_connect = self.on_connect 
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.connect("localhost", 1883, 60) 
            self.mqtt_client.loop_start()
            logger.info("mqtt connection successfull")
        except:
            logger.error("mqtt connection error")

        drive = action_drive(False) #Sen to enveryone that the joy doesn't control the chair
        self.mqtt_client.publish(action_drive.TOPIC_NAME, drive.serialize())
        

    # MQTT Connection initialization
    def on_connect(self, mqtt_client, userdata, flags, rc):
            if rc == 0:
                logger.info("Connection successful")
                mqtt_client.subscribe(action_drive.TOPIC_NAME)
                mqtt_client.subscribe(action_light.TOPIC_NAME)
                mqtt_client.subscribe(action_horn.TOPIC_NAME)
                mqtt_client.subscribe(action_max_speed.TOPIC_NAME)
                mqtt_client.subscribe(joystick_state.TOPIC_NAME)
                mqtt_client.subscribe(action_actuator_ctrl.TOPIC_NAME)
                mqtt_client.subscribe(action_poweroff.TOPIC_NAME)
                mqtt_client.subscribe(action_poweron.TOPIC_NAME)
                mqtt_client.subscribe(action_auto_light.TOPIC_NAME)
            else:
                logger.info(f"Connection failed with code {rc}")
            
    def update_light_state(self, rnetLid):
        """Makeing shure that 'light_state' attribute is up to date"""
        if rnetLid == 4 :
            return # Front light status is not save
        elif rnetLid == 3: # Warning
            self.light_state = [False, False, not self.light_state[2]]
        elif rnetLid == 2 and not self.light_state[2]: # Can change flashing only if warn is off
            self.light_state = [False, not self.light_state[1], False]
        elif rnetLid == 1 and not self.light_state[2]:
            self.light_state = [not self.light_state[0], False, False]
        return

    # MQTT Message broker :
    def on_message(self, mqtt_client, userdata, msg):

            # To ignore mqtt messages when we are off 
            if (self.power_state is False) and (msg.topic != action_poweron.TOPIC_NAME):
                if not msg.topic == joystick_state.TOPIC_NAME: #Ignore joy msg
                    logger.info("[WARNING] : Recv %s but power_on not done yet" % (msg.topic))
                return

            # ENABLE/DISABLE DRIVE COMMAND
            elif msg.topic == action_drive.TOPIC_NAME:
                self.drive_mode = deserialize(msg.payload).doDrive
                logger.info("[recv %s] Switch to drive mode %s" %(msg.topic, self.drive_mode))

            # ENABLE/DISABLE LIGHT 
            elif msg.topic == action_light.TOPIC_NAME:
                action_light_obj = deserialize(msg.payload)
                rnetLid = action_light_obj.light_id               
                self.RnetLight.set_data(rnetLid) # Send to can
                self.cansend(self.rnet_can.cansocket, self.RnetLight.encode())
                self.update_light_state(rnetLid)
                logger.info("[recv %s] Swich Light #%d" %(msg.topic, rnetLid))
            
            # ENABLE/DISABLE AUTO LIGHTS
            elif msg.topic == action_auto_light.TOPIC_NAME:
                self.auto_light = not self.auto_light
                if self.auto_light:
                    thread_auto = threading.Thread(target=self.auto_light_thread, daemon=True)
                    thread_auto.start()
                    logger.info("[recv %s] Turn ON automatic lights" %(msg.topic))
                else:
                    logger.info("[recv %s] Turn OFF automatic lights" %(msg.topic))

            # POWER ON
            elif msg.topic == action_poweron.TOPIC_NAME:
                if self.power_state is True:
                    logger.info("[recv %s] Power On - But already ON, message ignored" %(msg.topic))
                    return
                logger.info("[recv %s] Power On - Sending init frames" %(msg.topic))
                self.threads = self.power_on()               


            # POWER OFF
            elif msg.topic == action_poweroff.TOPIC_NAME:
                logger.info("[recv %s] Power Off" %(msg.topic))

                #cmd = RnetDissector.RnetPowerOff() #TODO NOT ENOUGH: study poweroff sequences to be able to repeate them
                #self.cansend(self.rnet_can.cansocket, cmd.encode())

                drive = action_drive(False) #Tell to everyone that joy dosen't control the weelchair anymore
                self.mqtt_client.publish(drive.TOPIC_NAME, drive.serialize())
                time.sleep(0.1)
                self.power_state = False
                self.auto_light = False

            # HORN
            elif msg.topic == action_horn.TOPIC_NAME:
                logger.info("[recv %s] Play Tone" %(msg.topic))
                tone = RnetDissector.RnetPlayTone()
                self.cansend(self.rnet_can.cansocket, tone.encode())

            # SET MAX SPEED
            elif msg.topic == action_max_speed.TOPIC_NAME:
                max_speed = deserialize(msg.payload)
                speed = max_speed.max_speed
                if (speed < 1) or (speed > 5):
                    logger.error("[ERROR] : [recv %s] Non supported max speed of %d" %(msg.topic, speed))
                    return
                self.RnetMotorConfSpeed.set_data(speed)
                self.maxSpeedState = 6
                self.max_speed_configuration()                
                logger.info("[recv %s] Configuring max speed to %d..." %(msg.topic, speed))

            # JOYSTICK POSITION
            elif msg.topic == joystick_state.TOPIC_NAME:
                if self.drive_mode is True:
                    joy_data = deserialize(msg.payload)
                    
                    # Data received from Joystck, reset watchdog
                    self.joy_watchdog = self.JOY_WATCHDOG_TIMEOUT

                    #If incoherent data not in +/-100 range critical error kill the thread
                    x = joy_data.x
                    y = joy_data.y
                    if (x > 100) or (x < -100) or (y > 100) or (y < -100):
                        logger.error("[recv %s] X=%d, Y=%d" %(msg.topic, x, y))
                        logger.error("[CRITICAL ERROR] Invalid x or y, not in [-100;100]")
                        # TODO do it more gently
                        # from xmlrpc.client import ServerProxy #Reboot all services
                        # server = ServerProxy('http://localhost:9000/RPC2')
                        # server.supervisor.restart()

                    # Check if long click is pressed to get out of drive mode
                    # and force position to neutral if true
                    if (joy_data.long_click == 1) :
                        logger.info("[CLIC] Switch to drive mode OFF")
                        self.drive_mode = False
                        drive = action_drive(False)
                        self.mqtt_client.publish(drive.TOPIC_NAME, drive.serialize())
                        self.RnetJoyPosition.set_data(0, 0)
                    else:
                        self.RnetJoyPosition.set_data(x, y)
                        if x or y:
                            logger.debug("[recv %s] X=%d, Y=%d" %(msg.topic, x, y))

            # ACTUATOR_CTRL
            elif msg.topic == action_actuator_ctrl.TOPIC_NAME:
                actuator_data = deserialize(msg.payload)
                self.RnetActuatorCtrl.set_data(actuator_data.actuator_num, actuator_data.direction)
                self.actuator_watchdog = self.ACTUATOR_WATCHDOG_TIMEOUT
                logger.debug("Actuator topic received : %r, %r" %(actuator_data.actuator_num, actuator_data.direction))


            else:
                logger.error("MQTT unsupported message")




    def power_on(self):
        """
        Method that starts the communication with motor by\n
         - Sending init sequence to wake the motor up
         - Starting all threads to communicate with the motor
         - Starting listening thread to get motor's info
        """

        self.rnet_can.turnMotorOn()
        logger.info("Rnet Init complete, jsm_subtype id is: %x" %self.rnet_can.jsm_subtype)

        # Initialize required Rnet frame objects and callbacks:
        self.rnet_can.set_battery_level_callback(self.update_battery_level)  
        self.rnet_can.set_chair_speed_callback(self.update_chair_speed)   
        self.RnetHorn = RnetDissector.RnetHorn(self.rnet_can.jsm_subtype)
        self.RnetJoyPosition = RnetDissector.RnetJoyPosition(0,0,self.rnet_can.joy_subtype)
        self.RnetLight = RnetDissector.RnetLightCtrl(self.rnet_can.jsm_subtype)
        self.RnetBatteryLevel = RnetDissector.RnetBatteryLevel()
        self.RnetMotorMaxSpeed = RnetDissector.RnetMotorMaxSpeed(100, self.rnet_can.joy_subtype)
        self.RnetMotorConfSpeed = RnetDissector.RnetMotorConfSpeed(1)
        self.RnetActuatorCtrl = RnetDissector.RnetActuatorCtrl(0, 0, self.rnet_can.jsm_subtype)

        self.power_state = True

        thrs = self.start_threads()
        self.rnet_can.connect()

        logger.info("Power on done")

        return thrs


    def update_battery_level(self, raw_frame):
        """Callback to update internal battery level"""
        self.RnetBatteryLevel.set_raw(raw_frame)
        self.battery_level = self.RnetBatteryLevel.decode()
        logger.debug("Got battery level info: %d" %self.battery_level)

    def update_chair_speed(self, rnetFrame):
        """Callback to update internal chair speed"""
        data = RnetDissector.getFrameType(rnetFrame)[4]
        speedStr = binascii.hexlify(data)[0:4]
        self.chair_speed = int(speedStr[2:4],16) + (int(speedStr[0:2],16)/256)
        logger.debug("Got chair speed info: %f" %self.chair_speed)
    
    def max_speed_configuration(self):
        """
        Function that handle max speed configuration of the weelchair.
        
        To change the max speed, we must first send the max speed value with a 'MAX_SPEED_CONF' frame (data between 1 and 5).
        Then, after receiving 5 frames of type 'MAX_SPEED_REAC' from motor (using rnet_can), we send the last 'MAX_SPEED' frame with a 100% value in data.

        this function is a state machine. At each call, it takes one step in this algorithm, using self.maxSpeedState variable.
        """
        self.maxSpeedState -= 1
        #logger.info("[MAX_SPEED_CONF] State is %d" % self.maxSpeedState)

        if self.maxSpeedState == 5: #At first call, send the 'MAX_SPEED_CONF' frame
            self.rnet_can.set_max_speed_config_callback(self.max_speed_configuration) #To count all 'MAX_SPEED_REAC' frames
            self.cansend(self.rnet_can.cansocket,self.RnetMotorConfSpeed.encode())
            logger.debug("[MAX_SPEED_CONF] Frame 'MAX_SPEED_CONF' sent.")
            return
        
        if self.maxSpeedState == 0: # Last call, send the 'MAX_SPEED' frame with a 100% (already fixed) value
            self.cansend(self.rnet_can.cansocket, self.RnetMotorMaxSpeed.encode())
            self.rnet_can.set_max_speed_config_callback(None) # To ignore other unwanted 'MAX_SPEED_REAC' frames
            logger.info("[MAX_SPEED_CONF] Max speed configuration done.")
            return        
        # Else, just decrement the maxSpeedState in order to wait the 5 'MAX_SPEED_REAC' frames from motor
        return

    def start_threads(self):
        """Start all threads to communicate with the motor"""
        logger.info("Starting Rnet threads...")
        thread_serial = threading.Thread(target=self.serial_thread, daemon=True)
        thread_joy = threading.Thread(target=self.rnet_joystick_thread, daemon=True)
        thread_act = threading.Thread(target=self.actuator_ctrl_thread, daemon=True)
        thread_batt = threading.Thread(target=self.rnet_status_thread, daemon=True)
        thread_htbt = threading.Thread(target=self.heartbeat_thead, daemon=True)
        thread_serial.start()
        thread_htbt.start()
        thread_joy.start()
        thread_act.start()
        thread_batt.start()
        return [thread_joy, thread_act, thread_batt, thread_serial, thread_htbt]


    def rnet_status_thread(self):
        """ Loop that publishes wheelchair statuses such as battery level, chair speed..."""
        logger.info("[RNET_STATUS] thread started")
        while self.power_state:
            status = status_battery_level(self.battery_level)
            self.mqtt_client.publish(status.TOPIC_NAME, status.serialize())
            speedStatus = status_chair_speed(self.chair_speed)
            self.mqtt_client.publish(speedStatus.TOPIC_NAME, speedStatus.serialize())
            logger.debug("[RNET_STATUS] Published infos: %.1fkm/h %d(battery)" % (self.chair_speed, self.battery_level))
            time.sleep(self.STATUS_FREQUENCY)
        logger.info("[RNET_STATUS] thread ended")


    def actuator_ctrl_thread(self):
        """Threads that moves actuators if necessary"""
        logger.info("[ACTUATOR] thread started")
        while self.power_state:
            # Decrement actuator watchdog
            if self.actuator_watchdog != 0 :
                actuatorframe = self.RnetActuatorCtrl.encode()
                self.cansend(self.rnet_can.cansocket, actuatorframe)           
                self.actuator_watchdog -= 1
            
            time.sleep(self.ACTUATOR_FREQUENCY)
        logger.info("[ACTUATOR] thread ended")


    def serial_thread(self):
        """Threads that send serial bytes periodicaly"""
        logger.info("[SERIAL] thread started")
        serial = RnetDissector.RnetSerial(self.rnet_can.serial_bytes)
        while self.power_state:
            self.cansend(self.rnet_can.cansocket, serial.encode())
            time.sleep(self.SERIAL_FREQUENCY)
        logger.info("[SERIAL] thread ended")

    def heartbeat_thead(self):
        """Threads that send (false) JSM heartBeat periodicaly"""
        logger.info("[HEARTBEAT] thread started")
        htbt = RnetDissector.RnetHeartbeat()
        while self.power_state:
            self.cansend(self.rnet_can.cansocket, htbt.encode())
            time.sleep(self.JSM_HEARTBEAT_PERIOD)
        logger.info("[HEARTBEAT] thread ended")


    def rnet_joystick_thread(self):
        """Loop that sends periodically Rnet joystick position frames"""
        logger.info("[JOYSTICK] thread started")
        while self.power_state:
            joyframe = self.RnetJoyPosition.encode()
            self.cansend(self.rnet_can.cansocket, joyframe)
            
            # Decrement joystick watchdog
            # force position to [0,0] if no data received from joystick 
            self.joy_watchdog -= 1
            if self.joy_watchdog == 0 :
                self.RnetJoyPosition.set_data(0, 0)
            
            time.sleep(self.POSITION_FREQUENCY)
        logger.info("[JOYSTICK] thread ended")

    def auto_light_thread(self):
        """Loop that sends Rnet light frames if necessary, base on 'light_state' attribute and joystick position"""
        logger.info("[AUTO LIGHT] Thread start")
        lim = 10
        while self.auto_light:
            x, y = self.RnetJoyPosition.get_data()
            logger.debug("[AUTO LIGHT] xy=(%d,%d) & %s"%(x,y, str(self.light_state)))
            left, right, warn = self.light_state
            low_x = (x<-lim)
            heigh_x = (x>lim)
            mid_x = not(low_x or heigh_x)
            low_y = (y<-lim)
            if (low_x and not left and not warn) or (mid_x and left):
                lightMsg = action_light(1)
                self.mqtt_client.publish(lightMsg.TOPIC_NAME, lightMsg.serialize())
            if (heigh_x and not right and not warn) or (mid_x and right):
                lightMsg = action_light(2)
                self.mqtt_client.publish(lightMsg.TOPIC_NAME, lightMsg.serialize())
            if (low_y and not warn) or (not low_y and warn):
                lightMsg = action_light(3)
                self.mqtt_client.publish(lightMsg.TOPIC_NAME, lightMsg.serialize())
            time.sleep(self.AUTO_LIGHT_PERIOD)
        logger.info("[AUTO LIGHT] Thread end")
        return


"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")

    return parser.parse_args()

if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Connect to piCan and initialize Rnet controller,
    rnet = RnetControlJSMsub() # Send JSM init sequence 'power on'
    while rnet.threads == None:
        time.sleep(0.5)

    for thread in rnet.threads:
        thread.join()
    logger.info("All threads joined, rebooting <rnet_ctrl.py> using supervisord ..")
