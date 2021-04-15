#!/python3
import threading
import argparse
import time
import socket
import sys
import logging
import curses


# In case of test mode run on a PC, no 
# ADC or screen will be available
# imports for ADC
try:
    FORCE_JOY_TESTMODE = False
    import Adafruit_ADS1x15
except:
    FORCE_JOY_TESTMODE = True

try:
    # imports for oled screen
    import Adafruit_GPIO.SPI as SPI
    import Adafruit_SSD1306
    from PIL import Image
    from PIL import ImageDraw
    from PIL import ImageFont
except:
    pass


# Constants definition:
DEFAULT_PERIOD = 0.01

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
Test function to control the wheelchair with keyboard arrows
Use UP/DONW/LEF/RIGH keyboards keys to move the wheelchair.
"""
class kbdtest():
    
    def __init__(self):
        self.stdscr = curses.initscr()
        # curses.cbreak()
        self.stdscr.keypad(True)
    
    def get_kbd_arrows(self):
        self.stdscr.refresh()
        x=0
        y=0

        key = self.stdscr.getkey()
        print("%r" %key)
        if key == "KEY_LEFT":
            x = 64
        elif key == "KEY_RIGHT":
            x = 192
        elif key == "KEY_UP":
            y = 64
        elif key == "KEY_DOWN":
            y = 192
        else :
            x=0
            y=0

        return x, y


"""
joystick class implements the interface with hardware and offers 
a 'get_new_data' to the client thread.
'sleeptime' parameters is a timing delay expressed in seconds 
            between each read on the hardware interface
"""
class joystick():

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
               
        self.offset_x = int((x_sum / self.NB_SAMPLE) - 1024)
        self.offset_y = int((y_sum / self.NB_SAMPLE) - 1024)
        logger.debug("ZERO calibration result : x=%d, y=%d" %(self.offset_x, self.offset_y))            



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

        if self.kbdtest is not None:
            rnet_x, rnet_y = self.kbdtest.get_kbd_arrows()
            scr_x = rnet_x
            scr_y = rnet_y

        else:
            # Get magnetometer x/y values from ADC:
            x,y = self.get_xy()

            # Scale ADC range to 8bits range for rnet
            rnet_x_scaled, rnet_y_scaled = self.scale_xy(x - self.offset_x, y - self.offset_y)

            # Scale ADC range for oled screen
            scr_x = self.screen_scale(x - self.offset_x, 0, 2048, 0, 128)
            scr_y = self.screen_scale(y - self.offset_y, 0, 2048, 0, 64)
            if self.invert_x:
                scr_x = unsigned2signed(scr_x, self.invert_x)
            if self.invert_y:
                scr_y = unsigned2signed(scr_y, self.invert_y)

            # Convert unsigned scaled value to signed value, and possibly
            # invert sign if required
            rnet_x = unsigned2signed(rnet_x_scaled, self.invert_x)
            rnet_y = unsigned2signed(rnet_y_scaled, self.invert_y)

            # Filter raw data to create a real zero
            # FIXME : If required, add filter function on x,y
            rnet_x, rnet_y  = self.zero_filter(rnet_x, rnet_y)

            logger.debug(">>>>>> RNET  Scaled  x/y data: %d,%d" %(rnet_x, rnet_y))
            logger.debug(">>>>>> SCREEN Scaled  x/y data: %d,%d" %(scr_x, scr_y))

        return rnet_x, rnet_y, scr_x, scr_y


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



"""
Display screen:
This class will display a feedback of the joy position
"""
class display():

    DISPLAY_FREQUENCY = 0.1

    def __init__(self, joy):
        self.x_previous = 0
        self.y_previous = 0
        self.joy = joy

        self.disp = Adafruit_SSD1306.SSD1306_128_64(rst=0)

        # Initialize library.
        self.disp.begin()

        # Clear display.
        self.disp.clear()
        self.disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        width = self.disp.width
        height = self.disp.height
        self.image = Image.new('1', (width, height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

    def displayAxes(self):
        
        # Draw horizontal axes.
        self.draw.line((0, 32, 128, 32), fill=255)
        # Draw vertical axes
        self.draw.line((64, 0, 64, 64), fill=255)
     

    def start_daemon(self):
        logger.debug("Starting screen daemon")
        daemon = threading.Thread(target=self.screen_daemon, daemon=True)
        daemon.start()
        return daemon


    """
    Endless loop that sends periodically Rnet frames
    """
    def screen_daemon(self):
        logger.info("Screen daemon started")
        # Display joy location on the screen;
        while True:
            _, _, scr_x, scr_y,  = self.joy.get_new_data()
            self.displayPoint(scr_x, scr_y)
            time.sleep(self.DISPLAY_FREQUENCY)


    def deletePoint(self):

        self.draw.ellipse((self.x_previous-5, self.y_previous-5 , self.x_previous+5, self.y_previous+5), outline=0, fill=0)
            
        
    def displayPoint(self, x, y):
    
        self.deletePoint()
        self.displayAxes()
        self.draw.ellipse((x-5, y-5 , x+5, y+5), outline=255, fill=255)
        
        self.x_previous = x
        self.y_previous = y
        
        self.disp.image(self.image)
        self.disp.display()




"""
Client for the Rnet server.
This class will connect to Rnet server and must send 
Periodically (or not) X/Y data positions to the server
once connected. 
On disconnection, the server will automatically set X/Y to [0,0]
"""
class client():

    def __init__(self, ip, port, joy):
        self.ip = ip
        self.port =port
        self.joy = joy
        self.sleeptime = self.joy.sleeptime
        self.server_nopresent = True

        while(self.server_nopresent):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_address = (self.ip, self.port)
                self.sock.connect(server_address)
                self.server_nopresent = False
                logger.info("Connected to Rnet server")
            except:
                logger.error("Connecting to %s:%d failed" %(self.ip, self.port))
                time.sleep(2)



    def start(self):         
        logger.info("Joy client started")
        while True:
            # get x/y
            # 'xx.yy'  where xx and yy are unsigned integer on 8 bits [0..255]
            rnet_x, rnet_y, _, _ = self.joy.get_new_data()
            rnet_data = b'%d.%d' %(rnet_x,rnet_y)
            logger.debug("Get new RNET x/y data: %r" %rnet_data)
            self.sock.send(rnet_data)

            time.sleep(self.sleeptime)
        



"""
Argument parser definition
"""
def parseInputs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Define server IPv4 address to connect, default is 127.0.0.1")
    parser.add_argument("--port", type=int, default="4141", help="Define server port to connect, default is 4141")
    parser.add_argument("--period", type=float, default=DEFAULT_PERIOD, help="Period where X/Y values are updated from hardware in seconds. Default = 0.01")
    parser.add_argument("--invert_x", help="Invert sign of x axis if set, default is false", action="store_true")
    parser.add_argument("--invert_y", help="Invert sign of y axis if set, default is false", action="store_true")
    parser.add_argument("--swap_xy", help="swap x/y inputs", action="store_true")
    parser.add_argument("-d", "--debug", help="Enable debug messages", action="store_true")
    parser.add_argument("-t", "--test", help="Test mode, Use computer keyboard instead of Joysticj inputs", action="store_true")

    return parser.parse_args()



if __name__ == "__main__":

    # Parse input args
    args = parseInputs()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    if FORCE_JOY_TESTMODE is True:
        logger.error("FORCE TEST")
        args.test = True

    # Instanciate joystick 
    joy = joystick(args.period, args.invert_x, args.invert_y, args.swap_xy, args.test)

    # Instanciate display
    try:
        display = display(joy)
        display.start_daemon()
        logger.info("Display interface started")
    except:
        logger.info("Screen error, no screen display")

    cli = client(args.ip, args.port, joy)
    # create client and connect to Rnet server
    cli.start()


