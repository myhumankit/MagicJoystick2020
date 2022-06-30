#!/usr/bin/python3

import sys
import time
import board
import adafruit_mlx90393

from gpiozero import Button

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


class Joystick():
    
    def __init__(self, dead_zone_size=.1, slow_reduce=False, swap_xy=False, swap_x=False, swap_y=False):
        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)

        self.swap_xy = swap_xy
        self.swap_x = swap_x
        self.swap_y = swap_y
        self.dead_zone_size = dead_zone_size # Between 0.0 and 1.0
        self.slow_reduce = slow_reduce

        i2c = board.I2C()  # uses board.SCL and board.SDA
        self.SENSOR = adafruit_mlx90393.MLX90393(i2c, gain=adafruit_mlx90393.GAIN_1X, filt = adafruit_mlx90393.FILTER_5, resolution= adafruit_mlx90393.RESOLUTION_19)
        self.SENSOR.gain = adafruit_mlx90393.GAIN_5X
        self.SENSOR.resolution_x = adafruit_mlx90393.RESOLUTION_19
        self.SENSOR.resolution_y = adafruit_mlx90393.RESOLUTION_19
        self.SENSOR.resolution_z = adafruit_mlx90393.RESOLUTION_19
        self.offsets = [.0, .0]
        self.mins = [-1.0, -1.0] 
        self.maxs = [1.0, 1.0]
        self.variance_seuil = [.0, .0] #TODO MAJ l'offset si la variance redescent proche de celle durant la calib (x1.5)
        self.calibrate()
    

    def calibrate(self):
        """This function compute the offset value for x and y axis"""
        print("[CALIB] Computing sensor offset:", end='', flush=True)
        t = time.time()
        cnt = 0
        while True:
            if time.time() - t > 3.0:
                break
            MX, MY, _ = self.SENSOR.magnetic
            self.offsets[X] += MX
            self.offsets[Y] += MY
            cnt += 1
            print(".", end='', flush=True)
            time.sleep(0.1)
        print(" Done")
        self.offsets[X] /= cnt
        self.offsets[Y] /= cnt

        self.mins[X] = self.offsets[X] * -0.05
        self.maxs[X] = self.offsets[X] * 0.05
        self.mins[Y] = self.offsets[Y] * -0.05
        self.maxs[Y] = self.offsets[Y] * 0.05
        
        print("[CALIB] Offsets = x:%.3f, y:%.3f" % (self.offsets[X],self.offsets[Y]))
        print("[CALIB] MinMax set to X [%.3f,%.3f] Y [%.3f,%.3f]" % (self.mins[X], self.maxs[X], self.mins[Y], self.maxs[Y]))


    def update_min_max(self, x, y):
        """Update mins and maxs values with params"""
        if self.slow_reduce:
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
    
    def getraw_XY(self):
        """Return float tuple (X,Y), after offset shifting"""
        MX, MY, _ = self.SENSOR.magnetic
        MX -= self.offsets[X]
        MY -= self.offsets[Y]
        self.update_min_max(MX, MY)
        return (MX, MY)
    
    def get_XY(self):
        """Return integer value of x & y ready to be published and raw value gived by getraw_XY() fonction, into a tuple (X,Y, rawX, rawY)"""
        rawX, rawY = self.getraw_XY()
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
        

        if self.swap_x:
            posX = - posX
        if self.swap_y:
            posY = - posY
        if self.swap_xy :
            return (int(posY), int(posX), rawY, rawX)
        return (int(posX), int(posY), rawX, rawY)

if __name__ == "__main__":

    debug = len(sys.argv)==2 and sys.argv[1]=='-d'
    if not debug:
        print("Use '-d' to print more info about joystick")

    client = mqtt.Client()
    client.connect("localhost",1883,60)
    client.loop_start()
    print("[MAIN]Connect MQTT")
    
    state = [0,0,0,0] #[buttons, x, y, long_click]
    marge_long_clic = 0.5
    marge_false_clic = 0.05

    joy = Joystick(dead_zone_size=0.5, slow_reduce=True)
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

        state[1], state[2], rawX, rawY = joy.get_XY()


        if debug:
            s = "JoyXY=[{:+4d},{:+4d}]   Raw=[{:+10.1f},{:+10.1f}]   MinMax=[X {:+10.1f},{:+10.1f} |Y {:+10.1f},{:+10.1f}]".format(state[1], state[2], rawX, rawY, joy.mins[X], joy.maxs[X], joy.mins[Y], joy.maxs[Y])
        else:
            s = "JoyState = [{:+4d},{:+4d},{:+4d},{:+4d}]".format(state[0],state[1],state[2],state[3])
        
        print(s, end='\r')

        joy_data = joystick_state(state[0], state[1], state[2], state[3])
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        time.sleep(JOY_PERIOD)