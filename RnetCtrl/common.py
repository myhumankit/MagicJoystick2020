import logging


# Instanciate logger:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.StreamHandler()
    ])
logger = logging.getLogger()


def dec2hex(dec, hexlen):  # convert dec to hex with leading 0s and no '0x'
    h = hex(int(dec))[2:]
    l = len(h)
    if h[l-1] == "L":
        l -= 1  # strip the 'L' that python int sticks on
    if h[l-2] == "x":
        h = '0'+hex(int(dec))[1:]
    return ('0'*hexlen+h)[l:l+hexlen]


def createJoyFrame(id_control, joystick_x, joystick_y):
    joyframe = id_control+'#' + \
        dec2hex(joystick_x, 2)+dec2hex(joystick_y, 2)
    return joyframe

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