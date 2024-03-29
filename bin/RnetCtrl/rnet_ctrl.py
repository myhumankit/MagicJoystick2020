import binascii
import threading
import argparse
import time
import logging
from rnet_can import  RnetCan
import paho.mqtt.client as mqtt
from magick_joystick.can2RNET import can2RNET, RnetDissector
from magick_joystick.Topics import *

logger = can2RNET.logger

"""
Main R-net class to send joystick frames on the bus
and take the control over the legacy JSM

"""
class RnetControl(threading.Thread):

    POSITION_FREQUENCY = 0.01   # 100Hz - RNET requirement
    STATUS_FREQUENCY = 0.5        # 2Hz
    JOY_WATCHDOG_TIMEOUT = 20   # Force joystick position to [0,0] after 200ms without data.
    ACTUATOR_FREQUENCY = 0.05   # 20 Hz
    ACTUATOR_WATCHDOG_TIMEOUT = 6 # 700ms (assume mqtt publish every 2Hz / 500ms)
    SERIAL_FREQUENCY = 0.05     # 50 ms period
    AUTO_LIGHT_PERIOD = 0.25
    power_state = True

    light_state = [False,False,False] # flashing left, flashing right, Warnning
    auto_light = False

    def __init__(self):
        self.RnetHorn = None
        self.drive_mode = False
        self.battery_level = 0
        self.chair_speed = 0.0
        self.joy_watchdog = 0
        self.actuator_watchdog = 0
        self.fdLog = None
        threading.Thread.__init__(self)

        self.motorXY = [0,0]
        
        logger.info("========== START RNET_CTRL 'CUT' ========== ")
        try:
            self.mqtt_client = mqtt.Client() 
            self.mqtt_client.on_connect = self.on_connect 
            self.mqtt_client.on_message = self.on_message
            self.mqtt_client.connect("localhost", 1883, 60) 
            self.mqtt_client.loop_start()
            logger.info("mqtt connection successfull")
        except:
            logger.error("mqtt connection error")

        drive = action_drive(False)
        self.mqtt_client.publish(action_drive.TOPIC_NAME, drive.serialize())

        self.cansend = can2RNET.cansendraw

        # Open can socket to prepare fake JSM power_on
        logger.info("Opening socketcan")
        self.rnet_can = RnetCan()


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

    # MQTT Message broker :
    def on_message(self, mqtt_client, userdata, msg):
            if not self.rnet_can.init_done: # TODO Exception when turn ON message is receive
                if not msg.topic == joystick_state.TOPIC_NAME:
                    logger.info("[WARNING] : Recv %s but init of 'rnet_can' not done yet. Turn the JSM on!" % (msg.topic))
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
                self.cansend(self.rnet_can.motor_cansocket, self.RnetLight.encode())
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
                logger.info("[recv %s] Power On - NOT WORKING NO FRAME SENT" %(msg.topic))
                # cmd = RnetDissector.RnetPowerOn()
                # thread_serial = threading.Thread(target=self.serial_thread, daemon=True)
                # thread_serial.start()
                # thread_serial = threading.Thread(target=self.serial_thread, daemon=True)
                # thread_serial.start()


            # POWER OFF
            elif msg.topic == action_poweroff.TOPIC_NAME:
                self.rnet_turn_off(fromMQTT=True)
                # All threads end --> join() end --> reboot using supervisor

            # HORN
            elif msg.topic == action_horn.TOPIC_NAME:
                logger.info("[recv %s] Play Tone" %(msg.topic))
                tone = RnetDissector.RnetPlayTone()
                self.cansend(self.rnet_can.jsm_cansocket, tone.encode())

            # SET MAX SPEED
            elif msg.topic == action_max_speed.TOPIC_NAME:
                max_speed = deserialize(msg.payload)
                speed = (max_speed.max_speed - 1)*25 # 1->0 2->25 3->50 4->75 5->100  
                self.RnetMotorMaxSpeed.set_data(speed)
                self.cansend(self.rnet_can.motor_cansocket,self.RnetMotorMaxSpeed.encode())
                logger.info("[recv %s] set max speed to %d" %(msg.topic, speed))

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
                    if (joy_data.buttons == 1) :
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
    

    def update_light_state(self, rnetLid):
        """Keep the status of lights in order to handle automatic light"""
        if rnetLid == 4 :
            return # Front light status is not save
        elif rnetLid == 3: # Warning
            self.light_state = [False, False, not self.light_state[2]]
        elif rnetLid == 2 and not self.light_state[2]: # Can change flashing only if warn is off
            self.light_state = [False, not self.light_state[1], False]
        elif rnetLid == 1 and not self.light_state[2]:
            self.light_state = [not self.light_state[0], False, False]
        return


    # For now Horn doesn't work, use 'playTone' instead
    # def horn_thread(self):
    #     while self.RnetHorn.get_state() == 0:
    #         self.cansend(self.rnet_can.motor_cansocket,self.RnetHorn.encode())
    #         logger.info("Send horn to motor: %s " %(RnetDissector.printFrame(self.RnetHorn.encode())))
    #         time.sleep(0.1)

    #     self.RnetHorn.toogle_state()
    #     self.cansend(self.rnet_can.motor_cansocket,self.RnetHorn.encode())      
    #     logger.info("Send horn to motor: %s " %(RnetDissector.printFrame(self.RnetHorn.encode())))
    #     self.hornThread = None


    def power_on(self):
        #Start listening on CAN socket
        self.rnet_can.connect()

        # Wait for init to be sent by JSM
        while self.rnet_can.init_done is not True:
            time.sleep(0.1)

        logger.info("Rnet Init complete, deviceID is: 0x%x" % (self.rnet_can.joy_subtype))

        # Initialize required Rnet frame objects and callbacks:
        self.rnet_can.set_battery_level_callback(self.update_battery_level)  
        self.rnet_can.set_chair_speed_callback(self.update_chair_speed)
        self.rnet_can.set_motor_pos_callback(self.update_motor_pos)
        self.rnet_can.set_joy_position_callback(self.send_rnet_joy_frame)
        self.rnet_can.set_power_off_callback(self.rnet_turn_off)
        self.RnetHorn = RnetDissector.RnetHorn(self.rnet_can.jsm_subtype)
        self.RnetJoyPosition = RnetDissector.RnetJoyPosition(0,0,self.rnet_can.joy_subtype)
        self.RnetLight = RnetDissector.RnetLightCtrl(self.rnet_can.jsm_subtype)
        self.RnetBatteryLevel = RnetDissector.RnetBatteryLevel()
        self.RnetMotorMaxSpeed = RnetDissector.RnetMotorMaxSpeed(20, self.rnet_can.joy_subtype)
        self.RnetActuatorCtrl = RnetDissector.RnetActuatorCtrl(0, 0, self.rnet_can.jsm_subtype)

        return self.start_threads()

    def update_motor_pos(self, rawData):
        """Function called by rnet_can when a 'JOY_POSITION' frame is received from motor socket"""
        x = rawData[0]
        y = rawData[1]
        x = (x-256) if (x>127) else x
        y = (y-256) if (y>127) else y
        self.motorXY = [x,y]
        return

    # To assure joy_frame frequency, we use JSM joy_frame as support to send our x and y values
    # We no longer create joy frame from scratch but replace the datas from raw joy_frame received
    def send_rnet_joy_frame(self, rnetFrame):
        """
        Function called by rnet_can when a 'JOY_POSITION' frame is received from JSM socket\n
        It return a rnetFrame with our data for x and y, ready to be send on CAN.
        If drive mode is False, the Frame remain unchanged (JSM control the wheelchair).
        """
        if self.drive_mode is False:
            return rnetFrame
        
        #Keep 8 first bytes of rnetFrame received, replace 8 bytes of data at the end
        return rnetFrame[0:8] + self.RnetJoyPosition.encode()[8:16] 

    def update_battery_level(self, raw_frame):
        """Function called by rnet_can when a 'BATTERY_LEVEL' frame is received from motor socket"""
        self.RnetBatteryLevel.set_raw(raw_frame)
        self.battery_level = self.RnetBatteryLevel.decode()
        logger.debug("Got battery level info: %d" %self.battery_level)

    def update_chair_speed(self, rnetFrame):
        data = RnetDissector.getFrameType(rnetFrame)[4]
        speedStr = binascii.hexlify(data)[0:4]
        self.chair_speed = int(speedStr[2:4],16) + (int(speedStr[0:2],16)/256)
        logger.debug("Got chair speed info: %f" %self.chair_speed)
    
    def rnet_turn_off(self, fromMQTT = False):
        self.rnet_can.set_power_off_callback(None) # To avoid multiple call of this function
        logger.info("Got PowerOFF from %s" % ('MQTT' if fromMQTT else 'RNet'))

        self.power_state = False
        self.auto_light = False
        cmd = RnetDissector.RnetPowerOff() 
        for _ in range(3):
            self.cansend(self.rnet_can.motor_cansocket, cmd.encode())
            self.cansend(self.rnet_can.jsm_cansocket, cmd.encode())
            time.sleep(0.1)


    def start_threads(self):
        logger.info("Starting Rnet threads...")
        thread_joy = threading.Thread(target=self.joy_thread, daemon=True)
        thread_joy.start()
        thread_act = threading.Thread(target=self.actuator_ctrl_thread, daemon=True)
        thread_act.start()
        thread_batt = threading.Thread(target=self.rnet_status_thread, daemon=True)
        thread_batt.start()
        return [thread_joy, thread_act, thread_batt]


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
                self.cansend(self.rnet_can.motor_cansocket, actuatorframe)           
                self.actuator_watchdog -= 1
            time.sleep(self.ACTUATOR_FREQUENCY)
        logger.info("[ACTUATOR] thread ended")


    def serial_thread(self):
        logger.info("Serial periodic Thread")
        while self.power_state:
            serial = RnetDissector.RnetSerial(binascii.unhexlify("9700148100000000"))
            self.cansend(self.rnet_can.cansocket0, serial.encode())
            self.cansend(self.rnet_can.cansocket1, serial.encode())
            time.sleep(self.SERIAL_FREQUENCY)


    
    def joy_thread(self):
        """
        Thread that send mqtt log message for joystick, and handle the watchdog for it
        """
        logger.info("[JOYSTICK] thread started")
        while self.power_state:          
              
            if self.drive_mode: #Only log if you drive
                jx, jy = self.RnetJoyPosition.get_data()
                joyLog = joy_log(jx, jy, self.motorXY[0], self.motorXY[1])
                self.mqtt_client.publish(joyLog.TOPIC_NAME, joyLog.serialize())

            self.joy_watchdog -= 1
            if self.joy_watchdog == 0:
                self.RnetJoyPosition.set_data(0,0)

            time.sleep(self.POSITION_FREQUENCY)
        logger.info("[JOYSTICK] thread ended")

    def auto_light_thread(self):
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
    rnet = RnetControl() # Send JSM init sequence 'power on'
    threads = rnet.power_on()
    for thread in threads:
        thread.join()
    time.sleep(3.0)
    logger.info("All threads joined, rebooting <rnet_ctrl.py> using supervisord ..")
