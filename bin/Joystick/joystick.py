#!/usr/bin/python3
from math import sqrt
import time
from ads1015 import ADS1015
from gpiozero import Button
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

# Constants definition:
DEFAULT_PERIOD = 0.03

GPIO_LEFT_BUTTON = 23
GPIO_RIGHT_BUTTON = 25

X = 0
Y = 1

class Joystick():

    ADS_GAIN = 4.096

    def __init__(self, dead_zone_size=.1, swap_xy=False, swap_x=False, swap_y=False, squareToCircle = False):
        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)

        self.swap_xy = swap_xy
        self.swap_x = swap_x
        self.swap_y = swap_y
        self.dead_zone_size = dead_zone_size # Between 0.0 and 1.0
        self.squareToCircle = squareToCircle

        # Create an ADS1015 ADC (16-bit) instance.
        self.ads = ADS1015()
        self.ads.set_programmable_gain(self.ADS_GAIN)

        self.offsets = [.0,.0]
        self.maxs = [.01,.01]
        self.mins = [.01,.01]
        self.calibrate()

    """
    Calibration function to set the zero position
    """
    def calibrate(self):
        NB_SAMPLE = 30
        x_sum = 0
        y_sum = 0

        print("Calibration in progress", end='', flush=True)
        for i in range(NB_SAMPLE):
            x = self.ads.get_voltage('in0/gnd')
            y = self.ads.get_voltage('in1/gnd')
            x_sum += x
            y_sum += y
            if i%3==0:
                print(".", end='', flush=True)
            time.sleep(0.1)
        print(" Done")

        self.offsets[X] = (x_sum / NB_SAMPLE)
        self.offsets[Y] = (y_sum / NB_SAMPLE)
        self.mins[X] = self.offsets[X] * -0.05 # TODO Is it truly secure?
        self.maxs[X] = self.offsets[X] * 0.05 
        self.mins[Y] = self.offsets[Y] * -0.05
        self.maxs[Y] = self.offsets[Y] * 0.05
        print("[CALIB] Offsets = x:%.3f, y:%.3f" % (self.offsets[X],self.offsets[Y]))
        print("[CALIB] MinMax set to X [%.3f,%.3f] Y [%.3f,%.3f]" % (self.mins[X], self.maxs[X], self.mins[Y], self.maxs[Y]))
    

    def getRaw_xy(self):
        """
        Get new x/y couple from ADC
        """
        x = self.ads.get_voltage('in0/gnd') - self.offsets[X]
        y = self.ads.get_voltage('in1/gnd') - self.offsets[Y]
        if x > self.maxs[X]:
            self.maxs[X] = x
        elif x < self.mins[X]:
            self.mins[X] = x
        if y > self.maxs[Y]:
            self.maxs[Y] = y
        elif y < self.mins[Y]:
            self.mins[Y] = y
        return x, y
    
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

    def get_xy(self):
        rawX, rawY = self.getRaw_xy()
        x, y = self.normalize_xy(rawX, rawY)

        if self.squareToCircle:
            x,y = self.swapToCircle(x, y)

        if self.swap_x:
            x = - x
        if self.swap_y:
            y = - y
        if self.swap_xy :
            return (int(y), int(x), rawY, rawX)
        return (int(x), int(y), rawX, rawY)

    def normalize_xy(self, x, y):
        """Change x & y from [min,max] to [-100,100], using the dead zone"""
        # Fonction affine en 3 morceaux
        dz = self.dead_zone_size
        if (x > (dz*self.maxs[X])): # x positif
            #Changement de repère, puis application du coef
            x_res = (x-(dz*self.maxs[X])) * (100 / ((1.0-dz) * self.maxs[X]))
        elif (x < (dz*self.mins[X])): # x negatif
            x_res = (x-(dz*self.mins[X])) * (100 / ((dz-1.0) * self.mins[X]))
        else: # Dans la zone morte
            x_res = 0.0

        if (y > (dz*self.maxs[Y])):
            y_res = (y-(dz*self.maxs[Y])) * (100 / ((1.0-dz) * self.maxs[Y]))
        elif (y < (dz*self.mins[Y])):
            y_res = (y-(dz*self.mins[Y])) * (100 / ((dz-1.0) * self.mins[Y]))
        else:
            y_res = 0.0

        return x_res, y_res


if __name__ == "__main__":
    
    state = [0,0,0,0]           #state = [buttons, x, y, long_click]
    marge_long_clic = 0.5
    marge_false_clic = 0.05
    test = False

    client = mqtt.Client()
    client.connect("localhost",1883,60)
    client.loop_start()
    print("[MAIN] Connect MQTT")

    # Instanciate joystick 
    joy = Joystick(swap_y=True, dead_zone_size=0.2, squareToCircle=True)
    lstBtn = [joy.left_button, joy.right_button]

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

        state[1], state[2], rawX, rawY = joy.get_xy()

        if test :
            s = "JOY[{:1d}, {:+4d}, {:+4d}, {:1d}] RAW[{:+7.3f}, {:+7.3f}] MinMax[X {:+7.3f},{:+7.3f} | Y {:+7.3f},{:+7.3f}]"
            print(s.format(state[0], state[1], state[2], state[3], rawX, rawY, joy.mins[X], joy.maxs[X], joy.mins[Y], joy.maxs[Y]), end='\r')
        else:
            joy_data = joystick_state(state[0], state[1], state[2], state[3])
            client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        time.sleep(DEFAULT_PERIOD)