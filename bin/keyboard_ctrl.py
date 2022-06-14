# This python script is used to have a full control of the wheelchair using the keyboard

import time
import paho.mqtt.client as mqtt
from click import getchar
import threading
from magick_joystick.Topics import *

PERIOD_JOY = 1/30
PERIOD_ACT = 1/20
TOUT_VALUE_JOY = 15
TOUT_VALUE_ACT = 10
TIMEOUT_ID = 2
HELPSPACE = "  "

# Movement / Joystick
KEYS_ARROW = ['\x1b[D','\x1b[A','\x1b[C','\x1b[B'] #LEFT UP RIGHT DOWN
ARROW_CHAR = ['\u2190','\u2191','\u2192','\u2193','\u25c9'] #LEFT UP RIGHT DOWN CENTER
VALUES_XY = [[155,0],[0,100],[100,0],[0,155]]
X = 0
Y = 1

# Lights
KEYS_LIGHT = ['o','p','w','l'] # LIGHTS (in order) :  flashing left/right, warn, spots
FLASHING_LEFT = 0
FLASHING_RIGHT = 1
WARNING_LIGHT = 2
FRONT_LIGHTS = 3

# On/Off
KEYS_ONOFF = ['n','f']

# Actuators
KEYS_ACT = ['&','é','"','\'','(','-','è','_','ç','à',')','=']
ACT_NAME = 0
ACT_DIR = 1
ACT_INFO = [ #Pour la fct print_state()
    ["Seat",('Up','Down')],
    ["Back",('Up','Down')],
    ["Seat",('Front-Rotation','Back-Rotation')],
    ["Legs",('Up','Down')],
    ["Bed mode",('Down','???')],
    ["???",('???','???')],
    ["None",('','')]
]

state_init = {
    'RUNNING' : True,
    'MOTOR_STATE' : "?", #Can be [?, OFF, ON/DRIVE, ON/NO_DRIVE]
    'ACT' : [-1, -1, -1], #Numero, direction, timeout
    'JOY' : [0, 0, 0, -1], # x, y, timeout, id_direction (-1:center, 0:left, 1:up, 2:right, 3:down)
    'LIGHT' : [False,False,False,False], # flashing Left/Right, WARNNING, SPOTS
    'MAX_SPEED' : 1,
    'HELP' : False
}

# Need to reinit the state
state = state_init.copy() # A real copy, not just reference.

def print_state():
    """Function used to print the current state"""
    global state
    doHelp = state['HELP']

    string = "\x1b[2J\x1b[H\n" # Clear sequence

    string += "MOTOR STATUS : " + state['MOTOR_STATE'] + '\r\n'

    #JOYSTICK
    string += "JOY : " + ARROW_CHAR[state['JOY'][3]] + '\r\n'

    #ACTUATORS
    act_id, direction_id, _ = state['ACT']
    act_name = ACT_INFO[act_id][ACT_NAME]
    direction = ACT_INFO[act_id][ACT_DIR][direction_id]
    string += "ACT : " + act_name + ' ' + direction + '\r\n'

    #LIGHTS
    lstr = '\u21E6 ' if (state['LIGHT'][FLASHING_LEFT]) else '  '
    lstr += '\u21E8 ' if (state['LIGHT'][FLASHING_RIGHT]) else '  '
    lstr += '\u29CB ' if (state['LIGHT'][WARNING_LIGHT]) else '  '
    lstr += '\u2600 ' if (state['LIGHT'][FRONT_LIGHTS]) else '  '
    string += "LIGHT : " + lstr + '\r\n'

    #MAX_SPEED
    speedVal = state['MAX_SPEED']
    speedStr = '\u2595' #Start of the speed bar
    for i in range(1,6): # i € [1,5]
        speedStr += '\u2588' if (i <= speedVal) else '\u2591'
    string += 'MAX_SPEED : ' + speedStr + '\u258f %d/5\r\n' % (speedVal)

    string += "\r\nToggle help with 'h'\r\n"
    if doHelp:
        string += HELPSPACE + "Turn ON/OFF the wheelchair with '%c'/'%c'" % (KEYS_ONOFF[0],KEYS_ONOFF[1]) + '\r\n'
        string += HELPSPACE + "Send drive action command with 'd'" + '\r\n'
        string += HELPSPACE + "Move the weelchair with " + str(ARROW_CHAR[0:4]) + '\r\n'
        string += HELPSPACE + "Move actuators with keys from '&' to '='" + '\r\n'
        string += HELPSPACE + "Toggle Lights [%c-\u21E6] [%c-\u21E8] [%c-\u29CB] [%c-\u2600]" % (KEYS_LIGHT[0],KEYS_LIGHT[1],KEYS_LIGHT[2],KEYS_LIGHT[3]) + '\r\n'
        string += HELPSPACE + "Change max speed with 's'" + '\r\n'
        string += HELPSPACE + "Use the Horn with 'k'" + '\r\n'
    print(string + '\r\n') 
    return



def light_handler(client, key):
    """Turns the lights on or off depending on the input key"""
    lid = KEYS_LIGHT.index(key)
    if lid == FRONT_LIGHTS :
        state['LIGHT'][FRONT_LIGHTS] = not state['LIGHT'][FRONT_LIGHTS]
    if lid == WARNING_LIGHT :
        state['LIGHT'][FLASHING_LEFT] = False 
        state['LIGHT'][FLASHING_RIGHT] = False 
        state['LIGHT'][WARNING_LIGHT] = (not state['LIGHT'][WARNING_LIGHT])
    if lid < 2 and not state['LIGHT'][WARNING_LIGHT]: # Flashing (only if no Warn)
        state['LIGHT'][FLASHING_LEFT] = (not state['LIGHT'][FLASHING_LEFT]) and lid==FLASHING_LEFT
        state['LIGHT'][FLASHING_RIGHT] = (not state['LIGHT'][FLASHING_RIGHT]) and lid==FLASHING_RIGHT
    
    #In case of Flash change with Warn ON, send a useless frame
    light = action_light(lid+1) #ID begins with 1
    client.publish(light.TOPIC_NAME, light.serialize())



def get_kbd(client):
    """Get an input keys in a loop, and performs the corresponding actions"""
    global state
    global state_init
    while state['RUNNING']:

        print_state()
        key = getchar()

        if key in KEYS_ACT:
            id = KEYS_ACT.index(key)
            num, direction = id//2, id%2
            state['ACT'] = [num, direction,TOUT_VALUE_ACT]
        
        if key in KEYS_ARROW:
            id = KEYS_ARROW.index(key)            
            state['JOY'] = [VALUES_XY[id][X], VALUES_XY[id][Y], TOUT_VALUE_JOY, id]
        
        if key in KEYS_LIGHT:
            light_handler(client, key)

        if key == 'd':
            drive = action_drive(True)
            client.publish(drive.TOPIC_NAME, drive.serialize())
            state['MOTOR_STATE'] = 'ON/DRIVE'
        
        if key in KEYS_ONOFF:
            if (key == KEYS_ONOFF[0]):
                turn = action_poweron()
                state['MOTOR_STATE'] = "ON/NO_DRIVE"
            else:
                turn = action_poweroff()
                state = state_init.copy()
                state['MOTOR_STATE'] = "OFF"
            client.publish(turn.TOPIC_NAME, turn.serialize())
        
        if key == 's':
            state['MAX_SPEED'] = state['MAX_SPEED']%5 + 1
            sped = action_max_speed(state['MAX_SPEED'])
            client.publish(sped.TOPIC_NAME, sped.serialize())
        
        if key == 'k':
            horn = action_horn()
            client.publish(horn.TOPIC_NAME, horn.serialize())
        
        if key == 'h':
            state['HELP'] = not state['HELP']

        elif (key == 'q'):
            state['RUNNING'] = False
    return



def actuator_thread(client):
    """Sends the frames of the actuators in a loop as long as the corresponding key remains pressed."""
    global state
    while state['RUNNING']:
        num, direction, watchDog = state['ACT']
        if watchDog >= 0:
            act_data =  action_actuator_ctrl(actuator_num=num, direction=direction)
            client.publish(act_data.TOPIC_NAME, act_data.serialize())
            if watchDog == 0:
                state['ACT'] = [-1, -1, 0] # Reinit
                print_state()
            state['ACT'][TIMEOUT_ID] -= 1
        time.sleep(PERIOD_ACT)



def joystick_thread(client):
    """Sends the frames of the joystick in a loop as long as the corresponding key remains pressed."""
    global state
    while state['RUNNING']:
        x, y, watchDog, _ = state['JOY']
        if watchDog <= 0:
            state['JOY'] = [0,0,0,-1] # To stop moving after 0.5s
            if watchDog == 0: # Only actualize once the screen
                print_state()
        joy_data = joystick_state(0, x, y, 0)
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        state['JOY'][TIMEOUT_ID] -= 1
        time.sleep(PERIOD_JOY)


client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()
time.sleep(0.1)


daemon_kbd = threading.Thread(target=get_kbd, args=[client], daemon=True)
daemon_act = threading.Thread(target=actuator_thread, args=[client], daemon=True)
daemon_joy = threading.Thread(target=joystick_thread, args=[client], daemon=True)

daemon_kbd.start()
daemon_act.start()
daemon_joy.start()

daemon_kbd.join()
daemon_act.join()
daemon_joy.join()
