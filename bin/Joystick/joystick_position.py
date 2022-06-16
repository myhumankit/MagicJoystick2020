#!/usr/bin/python3
import time
from ads1015 import ADS1015
import RPi.GPIO as GPIO
from gpiozero import Button
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import logging
import sys
#import daemon

# Constants definition:
DEFAULT_PERIOD = 0.01

GPIO_LEFT_BUTTON = 23
GPIO_RIGHT_BUTTON = 26



# Instanciate logger:
logging.basicConfig(
    level=logging.INFO, #log every message above INFO level (debug, info, warning, error, critical)
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()
h = logging.StreamHandler(sys.stdout)
h.flush = sys.stdout.flush
logger.addHandler(h)


# Unsigned 8 bits to signed 8bits
# input x      : 0..255 center on 127 unsigned
def unsigned2signed(x):
    # Case 'negative' range input 1..127 output 127..255 <=> -127..-1
    if x < 128:
        out = x + 127

    # Case positive range input 128..255 output 0..127
    else :
        # Range 0..127
        out = x - 128
    return out


class Joystick():

    ADS_GAIN = 2.048
    NB_SAMPLE = 30

    def __init__(self, swap_xy=False):
        self.left_button = Button(GPIO_LEFT_BUTTON)
        self.right_button = Button(GPIO_RIGHT_BUTTON)

        # Create an ADS1015 ADC (16-bit) instance.
        self.ads = ADS1015()
        #self.reference = self.ads.get_reference_voltage()
        #print("Reference voltage: {:6.3f}v \n".format(self.reference))

        self.sigmax_square = 100
        self.sigmay_square = 100
        #self.offset_x = self.ads.get_voltage('in0/gnd')
        #self.offset_y = self.ads.get_voltage('in1/gnd')
        self.x_min = self.ads.get_voltage('in0/gnd')
        self.x_max = self.x_min
        self.y_min = self.ads.get_voltage('in1/gnd')
        self.y_max = self.y_min


    """
    Get new x/y couple from ADC
    """
    def get_xy(self):
        x = self.ads.get_voltage('in0/gnd')
        y = self.ads.get_voltage('in1/gnd')

        if(x<self.x_min):
            self.x_min = x
        elif(x>self.x_max):
            self.x_max = x
            
        if(y<self.y_min):
            self.y_min = y
        elif(y>self.y_max):
            self.y_max = y

        return x, y


    """
    Calibration function to set the zero position
    """
    def calibrate(self, SEUIL):
        x_sum = 0
        y_sum = 0
        sigmax_sum = 0
        sigmay_sum = 0
        
        for i in range(self.NB_SAMPLE):
            x, y = self.get_xy()
            print("x = %f, y = %f" %(x,y))
            time.sleep(0.03)

            x_sum += x
            y_sum += y
            sigmax_sum += (5*x)**2
            sigmay_sum += (5*y)**2
            logger.debug(" JOY Calibration %d : x_sum = %f ; y_sum = %f ; sigmax_sum = %f ; sigmay_sum = %f" %(i, x_sum, y_sum, sigmax_sum, sigmay_sum))

        #print("attribute offset ?", hasattr(self, 'offset_x'))

        offset_x = (x_sum / self.NB_SAMPLE)
        offset_y = (y_sum / self.NB_SAMPLE)

        if(not hasattr(self, 'offset_x')):
            self.offset_x = offset_x
            self.offset_y = offset_y
               
        sigma_x = 1/self.NB_SAMPLE * sigmax_sum - (5*offset_x)**2   #coef 5 pour augmenter la valeur de sigma
        sigma_y = 1/self.NB_SAMPLE * sigmay_sum - (5*offset_y)**2   #coef 5 pour augmenter la valeur de sigma
        logger.info("offset_x = %f, offset_y = %f, sigma_x = %f, sigma_y = %f"  %(offset_x, offset_y, sigma_x, sigma_y))

        if(sigma_x < SEUIL and sigma_y < SEUIL):
            self.sigmax_square = sigma_x
            self.offset_x = offset_x
            self.sigmay_square = sigma_y
            self.offset_y = offset_y
        
        logger.info("ZERO calibration result : x0=%f, y0=%f, SEUIL = %f, sigmax²=%f, sigmay²=%f" %(self.offset_x, self.offset_y, SEUIL, self.sigmax_square, self.sigmay_square))
        logger.info("[ x_min = %f, x_max = %f ]       [ y_min = %f, y_max = %f ]", self.x_min, self.x_max, self.y_min, self.y_max)

        return self.offset_x, self.offset_y, self.x_min, self.x_max, self.y_min, self.y_max

    
    def range_xy(self, nb_sample):
        logger.info("DEBUT POUR AMPLITUDE X/Y")
        for i in range(nb_sample):
            x, y = self.get_xy()
        logger.info("AMPLITUDE X = [ %f ; %f ]  ; AMPLITUDE Y = [ %f ; %f ] " %(self.x_min, self.x_max, self.y_min, self.y_max))


    def normalize_xy(self, x, y):
        if(x>self.offset_x):
            x_res = (x-self.offset_x)/(self.x_max-self.offset_x) * 0.5 + 0.5
        elif(x<=self.offset_x):
            x_res = (x-self.x_min)/(self.offset_x-self.x_min) * 0.5
        if(y>self.offset_y):
            y_res = (y-self.offset_y)/(self.y_max-self.offset_y) * 0.5 + 0.5
        elif(y<=self.offset_y):
            y_res = (y-self.y_min)/(self.offset_y-self.y_min) * 0.5
        return x_res, y_res


    def scale_xy(self, x, y):
        # Scale ADC range to 8bits range for rnet
        return int(x*255), int(y*255)
    
    def rnet_xy(self, x, y):
        return unsigned2signed(x), unsigned2signed(y)


# # Instanciate joystick 
# joy = Joystick() #default gain = 2.048
# logger.debug("JOY programmable gain = %f" %joy.ads.get_programmable_gain())

''' 
MISE EN BACKGROUND TEST
print("juste avant daemon")
with daemon.DaemonContext():
    time.sleep(60)
    print("hello")
    #joy.calibrate()
print("avant boucle while") '''

# while True:
#     joy.calibrate(0.0001*joy.NB_SAMPLE/30)
#     #value = joy.get_xy()
#     #print(value)
#     #print("")
#     time.sleep(0.5)



if __name__ == "__main__":
    
    state = [0,0,0,0]           #state = [buttons, x, y, long_click]
    save_state = [0,0,0,0]
    diff = 1
    btn1_state_save = False

    client = mqtt.Client()
    client.connect("localhost",1883,60)
    client.loop_start()
    logger.info("Connect MQTT")

    # Instanciate joystick 
    joy = Joystick()
    joy.calibrate(0.0005*joy.NB_SAMPLE/30)
    time.sleep(3)
    joy.range_xy(500)

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
                    print(state)
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
                    print(state)
                    break       
            state[0] = 2 

        state[1], state[2] = joy.get_xy()
        #print("x = %f, y = %f" %(state[1], state[2]))
        state[1], state[2] = joy.normalize_xy(state[1], state[2])
        state[1], state[2] = joy.scale_xy(state[1], state[2])
        
        #tmp_x, tmp_y = joy.normalize_xy(joy.offset_x, joy.offset_y)
        logger.debug("après scale_xy : " + str(state) + '''"      offset : [ %f ; %f ]" %(joy.scale_xy(tmp_x, tmp_y))''')
        state[1], state[2] = joy.rnet_xy(state[1], state[2])
        print("après rnet_xy" + str(state))
        state[1] = unsigned2signed(state[1])
        state[2] = unsigned2signed(state[2])
        print("après conv unsigned to signed" + str(state))

        # if(save_state != state ):
        joy_data = joystick_state(state[0], state[1], state[2], state[3])
        #print(joy_data.serialize())
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            # save_state = state
        time.sleep(0.03)