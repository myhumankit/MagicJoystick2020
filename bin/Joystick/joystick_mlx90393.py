#!/usr/bin/python3

import sys
import time
import board
import adafruit_mlx90393

from gpiozero import Button

import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

GPIO_LEFT_BUTTON = 23
GPIO_RIGHT_BUTTON = 24

JOY_PERIOD = 0.03 # Same as joystick.py

# COEF**2000 = 0.5
# To devide by 2 a number in 2min at 33Hz
COEF = 0.99982672821815

X = 0
Y = 1


class Joystick():
    
    def __init__(self):
        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)

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
        self.offsets[X] /= cnt
        self.offsets[Y] /= cnt
        print(" Done")

    def update_min_max(self, x, y):
        """Update mins and maxs values with params"""
        #Slowly decrease the value of min & max in case of aberation
        self.mins[X] = COEF * self.mins[X]
        self.mins[Y] = COEF * self.mins[Y]
        self.maxs[X] = COEF * self.maxs[X]
        self.maxs[Y] = COEF * self.maxs[Y]

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
        offsets = self.offsets
        mins = self.mins
        maxs = self.maxs

        # Values from interval [min, max] are transformed to interval [-100, 100].
        if rawX < offsets[X]:
            posX = (100 * rawX) / (-mins[X])
        else :
            posX = (100 * rawX) / (maxs[X])
        
        if rawY < offsets[Y]:
            posY = (100 * rawY) / (-mins[Y])
        else :
            posY = (100 * rawY) / (maxs[Y])
        
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
    joy = Joystick()

    long_clic_delay = 0.5

    while True:
        state[0] = 0
        state[3] = 0
        
        if joy.left_button.is_pressed:
            start_btn1 = time.monotonic()
            while(joy.left_button.is_active):
                current = time.monotonic()
                delai = current - start_btn1
                if  delai > long_clic_delay:
                    state[0] = 1
                    state[3] = 1
                    break                   
            state[0] = 1
        elif joy.right_button.is_pressed:
            start_btn2 = time.monotonic()
            while(joy.right_button.is_active):
                current = time.monotonic()
                delai = current - start_btn2
                if  delai > long_clic_delay:
                    state[0] = 2
                    state[3] = 1
                    break       
            state[0] = 2 

        state[1], state[2], rawX, rawY = joy.get_XY()

        if debug:
            s = "JoyXY=[{:+4d},{:+4d}]   Raw=[{:+10.1f},{:+10.1f}]   MinMax=[X {:+10.1f},{:+10.1f} |Y {:+10.1f},{:+10.1f}]".format(state[1], state[2], rawX, rawY, joy.mins[X], joy.maxs[X], joy.mins[Y], joy.maxs[Y])
        else:
            s = "JoyState = [{:+4d},{:+4d},{:+4d},{:+4d}]".format(state[0],state[1],state[2],state[3])
        
        print(s, end='\r')

        joy_data = joystick_state(state[0], state[1], state[2], state[3])
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        time.sleep(JOY_PERIOD)