#!/usr/bin/python3
import time
import logging
import RPi.GPIO as GPIO
from gpiozero import Button
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

# Constants definition:
DEFAULT_PERIOD = 0.01

GPIO_LEFT_BUTTON = 23
GPIO_RIGHT_BUTTON = 26
# In case of test mode run on a PC, no 
# ADC or screen will be available
# imports for ADC
try:
    FORCE_JOY_TESTMODE = False
    import Adafruit_ADS1x15
except Exception as e:
    FORCE_JOY_TESTMODE = True
    print(str(e))

    # Instanciate logger:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()


# Unsigned 8 bits to signed 8bits
# input x      : 0..255 center on 127 unsigned
# input invert : True/False, invert sign
def unsigned2signed(x, invert):

    # Invert the sign if required
    if invert is True :
        x = 255-x

    if x == 0:
        out  = 128

    # Case 'negative' range input 1..127 output 127..255 <=> -127..-1
    elif x < 128:
        out = x + 127

    # Case positive range input 128..255 output 0..127
    else :
        # Range 0..127
        out = x - 128

    return out

"""
joystick class implements the interface with hardware and offers 
a 'get_new_data' to the client thread.
'sleeptime' parameters is a timing delay expressed in seconds 
            between each read on the hardware interface
"""
class Joystick():

    # Choose a gain of 1 for reading voltages from 0 to 4.09V.
    # Or pick a different gain to change the range of voltages that are read:
    #  - 2/3 = +/-6.144V
    #  -   1 = +/-4.096V
    #  -   2 = +/-2.048V
    #  -   4 = +/-1.024V
    #  -   8 = +/-0.512V
    #  -  16 = +/-0.256V
    # See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    ADC_GAIN        = 2     # This gain gives 0 to 2048 measures

    ADC_GAIN_SCALE          = 2048.0    # Scale the ADC value function of ADC_GAIN
    HYSTERESIS              = 30        # Used to generate a real 'zero' point 
    NB_SAMPLE               = 10        # number of samples for calibaration


    def __init__(self, sleeptime = DEFAULT_PERIOD, invert_x = False, invert_y = False, swap_xy = False, test = False):
        self.sleeptime = sleeptime
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.swap_xy = swap_xy
        self.offset_x = 0
        self.offset_y = 0
        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)
        
        if test is True:
            logger.info("Starting joy in debug mode with with computer keybaord")
            self.kbdtest = kbdtest()
        else :
            self.kbdtest = None
            # Create an ADS1115 ADC (16-bit) instance.
            self.adc = Adafruit_ADS1x15.ADS1015()
            self.calibrate()
            logger.info("Starting joy, calibration done")

           

    """
    Get new x/y couple from ADC
    """
    def get_xy(self):
        if self.swap_xy is False:
            x = self.adc.read_adc(0, gain=self.ADC_GAIN)
            y = self.adc.read_adc(1, gain=self.ADC_GAIN)
        else:
            x = self.adc.read_adc(1, gain=self.ADC_GAIN)
            y = self.adc.read_adc(0, gain=self.ADC_GAIN)
        return x, y


    """
    Calibration function to set the zero position
    """
    def calibrate(self):
        
        x_sum = 0
        y_sum = 0
        
        for i in range(self.NB_SAMPLE):
            x, y = self.get_xy()
            x_sum += x
            y_sum += y
            logger.debug(" JOY Calibration %d = %6d / %6d" %(i, x_sum, y_sum))
               
        self.offset_x = int((x_sum / self.NB_SAMPLE) - self.ADC_GAIN_SCALE * 0.5)
        self.offset_y = int((y_sum / self.NB_SAMPLE) - self.ADC_GAIN_SCALE * 0.5)
        logger.debug("ZERO calibration result : x=%d, y=%d" %(self.offset_x, self.offset_y))            


    """
        Normalize x/y values between 0 and 1
    """
    def normalize_xy(self, x, y):
        min_x = self.offset_x
        max_x = self.ADC_GAIN_SCALE - 1 + self.offset_x
        range_x = max_x - min_x

        min_y = self.offset_y
        max_y = self.ADC_GAIN_SCALE - 1 + self.offset_y
        range_y = max_y - min_y

        norm_x = min(1, max(0, (x - min_x) / range_x))
        norm_y = min(1, max(0, (y - min_y) / range_y))
        return norm_x, norm_y


    """
    Scale x/y from ADC dynamic to 8 bits signed dynamic
    """
    def scale_xy(self, x, y):
        # Scale values to 8 bits:
        x_scaled = int((x / self.ADC_GAIN_SCALE)*255)
        y_scaled = int((y / self.ADC_GAIN_SCALE)*255)
        return x_scaled, y_scaled

    """
    Scale value for screen display
    """
    def screen_scale(self, x, in_min, in_max, out_min, out_max):
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min



    """
    This funtion is called periodically by the client
    to get new X/Y data from joystick, and must output
    
    Note: Rnet works with signed int8, so 0..127 => [0..127], 128..255 => [-127..-1]
    """
    def get_new_data(self):

        # Get magnetometer x/y values from ADC:
        x, y = self.normalize_xy(*self.get_xy())

        # Scale ADC range to 8bits range for rnet
        x, y = int(x * 255), int(y * 255)

        # Convert unsigned scaled value to signed value, and possibly
        # invert sign if required
        rnet_x = unsigned2signed(x, self.invert_x)
        rnet_y = unsigned2signed(y, self.invert_y)


        # Filter raw data to create a real zero
        # FIXME : If required, add filter function on x,y
        rnet_x, rnet_y  = self.zero_filter(rnet_x, rnet_y)

        return rnet_x, rnet_y


    """
    Joystick filtering function:
    This function will filter the x/y data 
    from analog to digital converter 
    input: x/y unsigned 8 bits data. Center around 127
    """
    def zero_filter(self, x, y):
        x_out = x
        y_out = y
        if (x > 255 - self.HYSTERESIS) or (x < self.HYSTERESIS):
            x_out = 0

        if (y > 255 - self.HYSTERESIS) or (y < self.HYSTERESIS):
            y_out = 0

        return x_out, y_out


if __name__ == "__main__":

    state = [0,0,0,0]
    save_state = [0,0,0,0]
    diff = 1
    btn1_state_save = False

    client = mqtt.Client()
    client.connect("localhost",1883,60)
    client.loop_start()
    logger.info("Connect MQTT")

    # Instanciate joystick 
    joy = Joystick(invert_x = False, invert_y = True)

    while True:
        state[0] = 0
        state[3] = 0
        
        if joy.left_button.is_pressed:
            start_btn1 = time.monotonic()
            while(joy.left_button.is_active):
                current = time.monotonic()
                delai = current - start_btn1
                #print("Delai: ", delai)
                if  delai > diff:
                    print("Appui long sur bouton 1 detecté")
                    state[0] = 1
                    state[3] = 1
                    break                   
            state[0] = 1
        elif joy.right_button.is_pressed:
            start_btn2 = time.monotonic()
            while(joy.right_button.is_active):
                current = time.monotonic()
                delai = current - start_btn2
                #print("Delai: ", delai)
                if  delai > diff:
                    print("Appui long sur bouton 2 detecté")
                    state[0] = 2
                    state[3] = 1
                    break       
            state[0] = 2 

        state[1], state[2] = joy.get_new_data()

        # if(save_state != state ):
        joy_data = joystick_state(state[0], state[1], state[2],state[3])
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            # save_state = state
        time.sleep(0.03)

