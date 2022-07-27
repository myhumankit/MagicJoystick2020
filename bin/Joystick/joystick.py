#!/usr/bin/python3
import argparse
from math import sqrt
import sys
import time
import board
import adafruit_mlx90393
import threading
from gpiozero import Button
from ads1015 import ADS1015
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

GPIO_LEFT_BUTTON = 23
GPIO_RIGHT_BUTTON = 25

JOY_PERIOD = 0.03 # Same as joystick.py

# REDUCE_COEF**2000 = 0.5
# To devide by 2 a number in 2min at 33Hz
REDUCE_COEF = 0.99982672821815

X = 0
Y = 1

ADS_GAIN = 4.096

# Lenght of the list to save datas
NB_SAMPLE = 60


class Joystick():
    """
    This class is used to get and publish joystick position.
    Here are the args:
     - is_mlx90393 = False :            Decide if the instance will use the mlx_903939 sensor interface or the classic ADC one 
     - continuous_calibration=False :   Automaticaly update the offset of the joystick when his variance is low (any movement)
     - slow_minMax_reduce = False :     Reduce the raw min and max value to delete all aberrant values
     - dead_zone_size = 0.1 :           Fix the size of the dead_zone (percentage of the gap between offset & min/max), any raw value in the dead zone will result in a 0 position published
     - swap_xy = False :                Exchange x and y axis
     - swap_x = False :                 Swap x axis
     - swap_y = False :                 Swap y axis
     - coefX = 1.0 :                    Coeficent applied to the final value of X
     - coefX = 1.0 :                    Coeficent applied to the final value of Y
     - squareToCircle = False :         Transform a square shaped joystick in a circle shaped one (values such as [-100,100] are changed into [-70,70] to fit in a circle)
     - doReduceX = False :              Apply a function that reduce X when Y is high (cf 'reduceX' function)
     - handability = 25 :               Coeficient used to reduce X when Y is high. The higher it is, the smaller the reduction of X is.
    """
    

    def __init__(self,
                is_mlx90393=False,
                continuous_calibration=False,
                slow_minMax_reduce=False,
                dead_zone_size=.1, 
                swap_xy=False, 
                swap_x=False, 
                swap_y=False, 
                coefX = 1.0,
                coefY = 1.0,
                squareToCircle=False, 
                doReduceX=False, 
                handability=25):
        
        print("Start new JOY with handability=%d" % handability)

        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)

        self.is_mlx90393 = is_mlx90393

        self.continuous_calibration = continuous_calibration

        self.swap_xy = swap_xy
        self.swap_x = swap_x
        self.swap_y = swap_y

        self.dead_zone_size = dead_zone_size # Between 0.0 and 1.0

        # continuous calibration imply slow min/max reduce
        self.slow_minMax_reduce = slow_minMax_reduce or continuous_calibration

        self.squareToCircle = squareToCircle

        self.doReduceX = doReduceX
        self.handability = handability

        self.coefs = [coefX,coefY]

        if is_mlx90393:
            i2c = board.I2C()  # uses board.SCL and board.SDA
            self.SENSOR = adafruit_mlx90393.MLX90393(i2c, gain=adafruit_mlx90393.GAIN_1X, filt = adafruit_mlx90393.FILTER_5, resolution= adafruit_mlx90393.RESOLUTION_19)
            self.SENSOR.gain = adafruit_mlx90393.GAIN_5X
            self.SENSOR.resolution_x = adafruit_mlx90393.RESOLUTION_19
            self.SENSOR.resolution_y = adafruit_mlx90393.RESOLUTION_19
            self.SENSOR.resolution_z = adafruit_mlx90393.RESOLUTION_19
        else:
            # Create an ADS1015 ADC (16-bit) instance.
            self.ads = ADS1015()
            self.ads.set_programmable_gain(ADS_GAIN)

        self.offsets = [.0, .0]
        self.mins = [-1.0, -1.0] 
        self.maxs = [1.0, 1.0]
        self.values = [[.0] * NB_SAMPLE, [.0] * NB_SAMPLE] # The 30 last values readed by the joy
        self.curVar = [.0,.0]
        self.initVar = [.0,.0]
        self.curID = 0
        self.calib_ready = False

        self.doDrive = True

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect 
        self.client.on_message = self.on_message
        self.client.connect("localhost",1883,60)
        self.client.loop_start()

        self.calibrate()

        if continuous_calibration:
            thread_joy = threading.Thread(target=self.calbration_thread, daemon=True)
            thread_joy.start()


    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
            self.client.subscribe(action_drive.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic == action_drive.TOPIC_NAME:
            self.doDrive = deserialize(msg.payload).doDrive


    def sense(self):
        """Read the correct sensor and give x & y raw value"""
        x = 0
        y = 0
        if self.is_mlx90393:
            x, y, _ = self.SENSOR.magnetic
        else:
            x = self.ads.get_voltage('in0/gnd')
            y = self.ads.get_voltage('in1/gnd')
        return x, y


    def calibrate(self):
        """This function compute the offset value for x and y axis"""
        slep = 3.0 / NB_SAMPLE # Calibration during 3s

        print("[CALIB] Computing sensor offset:", end='', flush=True)
        for i in range(NB_SAMPLE):
            x, y = self.sense()
            self.values[X][i] = x
            self.values[Y][i] = y
            if i%(NB_SAMPLE//10)==0:
                print(".", end='', flush=True)
            time.sleep(slep)
        print(" Done")

        self.offsets[X] = sum(self.values[X]) / NB_SAMPLE
        self.offsets[Y] = sum(self.values[Y]) / NB_SAMPLE

        self.values[X][:] = [f-self.offsets[X] for f in self.values[X]] # Sub offsets to all values saved,
        self.values[Y][:] = [f-self.offsets[Y] for f in self.values[Y]] #   so mean is now at 0

        self.initVar[X] = sum([f*f for f in self.values[X]]) / NB_SAMPLE # - 0²
        self.initVar[Y] = sum([f*f for f in self.values[Y]]) / NB_SAMPLE # - 0²

        self.mins[X] = self.offsets[X] * -0.05
        self.maxs[X] = self.offsets[X] * 0.05
        self.mins[Y] = self.offsets[Y] * -0.05
        self.maxs[Y] = self.offsets[Y] * 0.05
        
        print("[CALIB] Offsets = x:%.3f, y:%.3f" % (self.offsets[X],self.offsets[Y]))
        print("[CALIB] InitVar are: vx=%.3f, vy=%.3f" % (self.initVar[X], self.initVar[Y]))
        print("[CALIB] MinMax set to X [%.3f,%.3f] Y [%.3f,%.3f]" % (self.mins[X], self.maxs[X], self.mins[Y], self.maxs[Y]))


    def swapToCircle(self, x, y):
        """
        If your joy is in square shape, you must use this function to not send data such as [100,100] which is impossible.
        """
        r = sqrt(x**2 + y**2)
        if r == 0:
            return (x, y)
        if abs(y) <= abs(x):
            absCosTheta = abs(x) / r
            x = x * absCosTheta
            y = y * absCosTheta
        else :
            absSinTheta = abs(y) / r
            x = x * absSinTheta
            y = y * absSinTheta
        return (x, y)
    

    def reduceX(self, x, y):
        """
        Reduce the value of x to change handability of the weelchair using the formula:\n
        newX = x * (A / (A + abs(y))   with A the 'handability' attribute, A>=1
        """
        x = x * (self.handability / (self.handability + abs(y)))
        return (x, y)


    def update_min_max(self, x, y):
        """Update mins and maxs values with params"""
        if self.slow_minMax_reduce:
            #Slowly decrease the value of min & max in case of aberation
            self.mins[X] = REDUCE_COEF * self.mins[X]
            self.mins[Y] = REDUCE_COEF * self.mins[Y]
            self.maxs[X] = REDUCE_COEF * self.maxs[X]
            self.maxs[Y] = REDUCE_COEF * self.maxs[Y]

        if x < self.mins[X]:
            self.mins[X] = x
        elif x > self.maxs[X]:
            self.maxs[X] = x
        
        if y < self.mins[Y]:
            self.mins[Y] = y
        elif y > self.maxs[Y]:
            self.maxs[Y] = y
    

    def get_XY(self):
        """Return float tuple (X,Y), after offset shifting"""
        x, y = self.sense()
        x -= self.offsets[X]
        y -= self.offsets[Y]
        self.update_min_max(x, y)

        if self.continuous_calibration is False:
            return (x, y)

        self.values[X][self.curID] = x
        self.values[Y][self.curID] = y
        self.curID = (self.curID +1) % NB_SAMPLE
        if not self.calib_ready:
            self.calib_ready = (self.curID%(NB_SAMPLE//2)==0) # TODO Update curVar when half of value have changed (See if the freq in good)
        return (x, y)
    

    def normalize_xy(self, rawX, rawY):
        """Change x & y from [min,max] to [-100,100], using the dead zone"""
        # Fonction affine en 3 morceaux
        mins = self.mins
        maxs = self.maxs
        dz = self.dead_zone_size

        if (rawX > (dz*maxs[X])): # x positif
            #Changement de repère, puis application du coef
            posX = (rawX-(dz*maxs[X])) * (100 / ((1.0-dz) * maxs[X]))
        elif (rawX < (dz*mins[X])): # x negatif
            posX = (rawX-(dz*mins[X])) * (100 / ((dz-1.0) * mins[X]))
        else: # Dans la zone morte
            posX = 0.0

        if (rawY > (dz*maxs[Y])):
            posY = (rawY-(dz*maxs[Y])) * (100 / ((1.0-dz) * maxs[Y]))
        elif (rawY < (dz*mins[Y])):
            posY = (rawY-(dz*mins[Y])) * (100 / ((dz-1.0) * mins[Y]))
        else:
            posY = 0.0
        return [posX, posY]

    
    def get_computed_XY(self):
        """Return integer value of x & y ready to be published and raw value gived by get_XY() fonction, into a tuple (X,Y, rawX, rawY)"""
        rawX, rawY = self.get_XY()
        
        x, y = self.normalize_xy(rawX, rawY)     

        if self.squareToCircle:
            x,y = self.swapToCircle(x, y)

        if self.doReduceX and self.doDrive: # Only reduce the left/right if you drive (to not change the mouse control)
            x,y = self.reduceX(x,y)   

        #At last, apply coefs if drive mode is ON
        if self.doDrive:
            x = x * self.coefs[X]
            y = y * self.coefs[Y]

        if self.swap_x:
            x = - x
        if self.swap_y:
            y = - y
        if self.swap_xy :
            return (int(y), int(x), rawY, rawX)
        return (int(x), int(y), rawX, rawY)
    

    def updateCurVar(self):
        """
        Update the variance with the values in tab\n
        Return the mean of all values.
        """
        sumX = .0
        sumY = .0
        sumSqX = .0
        sumSqY = .0
        for i in range(NB_SAMPLE):
            sumX += self.values[X][i]
            sumY += self.values[Y][i]
            sumSqX += self.values[X][i]**2
            sumSqY += self.values[Y][i]**2
        espX = (sumX / NB_SAMPLE)
        espY = (sumY / NB_SAMPLE)
        self.curVar[X] = (sumSqX / NB_SAMPLE) - espX**2
        self.curVar[Y] = (sumSqY / NB_SAMPLE) - espY**2
        return (espX, espY)


    def calbration_thread(self):
        calibSleep = JOY_PERIOD * (NB_SAMPLE/4)
        while True:
            time.sleep(calibSleep)
            if not self.calib_ready: #Half of values must have changed
                continue
            means = self.updateCurVar()
            if (self.curVar[X] < self.initVar[X]*2) and (self.curVar[Y] < self.initVar[Y]*2): #Updating Offsets
                #TODO Must redefine min and max because the offset hase changed
                self.mins[X] += means[X]
                self.mins[Y] += means[Y]
                self.maxs[X] += means[X]
                self.maxs[Y] += means[Y]

                self.offsets[X] += means[X]
                self.offsets[Y] += means[Y]
                print("[CALIB_THR] Offsets updated -> x:%.3f, y:%.3f (shift of %.3f, %.3f)   //...//   " % (self.offsets[X],self.offsets[Y], means[X], means[Y]))
                self.calib_ready = False # to not chain the recalibration



    def start_joy(self, test = False):
        """
        Start joystick class\n
        Use 'test=True' to print and not publish on MQTT server.
        """
        state = [0,0,0,0]           #state = [buttons, x, y, long_click]
        marge_long_clic = 0.5
        marge_false_clic = 0.05
        lstBtn = [self.left_button, self.right_button]

        while True:
            state[0] = 0
            state[3] = 0

            for btn in lstBtn:
                if btn.is_pressed:
                    start = time.monotonic()
                    delay = 0.0
                    while(btn.is_active):
                        delay = time.monotonic() - start
                        if delay > marge_long_clic:
                            break
                    state[0] = lstBtn.index(btn)+1 if (delay > marge_false_clic) else 0
                    state[3] = 1 if (delay > marge_long_clic) else 0
                    # if (delay < marge_false_clic):
                    #     print("\n[WARN] Strange quick clic n°%d delay=%.3f" % (lstBtn.index(btn)+1,delay))

            state[1], state[2], rawX, rawY = self.get_computed_XY()
            
            if state[3]==1:
                self.doDrive = not self.doDrive

            if test :

                s = "JoyXY=[{:+4d},{:+4d}]   Raw=[{:+7.3f},{:+7.3f}]   MinMax=[X {:+7.3f},{:+7.3f} |Y {:+7.3f},{:+7.3f}] curVar=[{:+10.3f},{:+10.3f}]"
                print(s.format(state[1], state[2], rawX, rawY, self.mins[X], self.maxs[X], self.mins[Y], self.maxs[Y], self.curVar[X],self.curVar[Y]), end='\r')
            else:
                joy_data = joystick_state(state[0], state[1], state[2], state[3])
                self.client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            time.sleep(JOY_PERIOD)


def parseInputs():
    """
    Argument parser definition
    """
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-t", "--test", help="Print joy value and not publish on MQTT server.", action="store_true")
    parser.add_argument("-m", "--mlx90393", help="Use the new mlx_90393 sensor and not a classic ADC as input", action="store_true")
    return parser.parse_args()

if __name__ == "__main__":

    args = parseInputs()

    # Instanciate joystick 
    joy = Joystick(
        is_mlx90393=args.mlx90393,
        continuous_calibration=False,
        slow_minMax_reduce=False,
        dead_zone_size=.1, 
        swap_xy=False, 
        swap_x=False, 
        swap_y=True, 
        coefX=1.0,
        coefY=1.0,
        squareToCircle=False, 
        doReduceX=False, 
        handability=25)

    joy.start_joy(test = args.test)