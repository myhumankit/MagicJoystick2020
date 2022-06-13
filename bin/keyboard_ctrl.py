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
HELPSPACE = "  "

KEYS_ACT = ['&','é','"','\'','(','-','è','_','ç','à',')','=']
KEYS_ARROW = ['\x1b[D','\x1b[A','\x1b[C','\x1b[B'] #LEFT UP RIGHT DOWN
ARROW_XY = [[155,0],[0,100],[100,0],[0,155]]
KEYS_LIGHT = ['o','p','w','l'] # LIGHTS (in order) :  flashing left/right, warn, spots

ARROW_CHAR = ['\u2190','\u2191','\u2192','\u2193','\u25c9'] #LEFT UP RIGHT DOWN CENTER
ACT_NAME = 0
ACT_DIR = 1
ACT_INFO = [ #Pour la fct print_state()
    ["Seat",('Down','Up')],
    ["Back",('Down','Up')],
    ["Seat",('Back-Rotation','Front-Rotation')],
    ["Legs",('Down','Up')],
    ["Bed mode",('???','Down')],
    ["???",('???','???')],
    ["None",('','')]
]

state = {
    'RUNNING' : True,
    'ACT' : [-1, -1, -1], #Numero, direction, timeout
    'JOY' : [0, 0, 0, -1], # x, y, timeout, id_direction (-1 center, 0 left, 1 up...)
    'LIGHT' : [False,False,False,False], # flashing Left/Right, WARNNING, SPOTS
    'MAX_SPEED' : 1,
    'HELP' : False
}


def print_state():
    """Function used to print the current state"""
    global state
    doHelp = state['HELP']

    string = "\x1b[2J\x1b[H\n" # Clear sequence

    #JOYSTICK
    string += "JOY : " + ARROW_CHAR[state['JOY'][3]] + '\r\n'

    #ACTUATORS
    act_id, direction_id, _ = state['ACT']
    act_name = ACT_INFO[act_id][ACT_NAME]
    direction = ACT_INFO[act_id][ACT_DIR][direction_id]
    string += "ACT : " + act_name + ' ' + direction + '\r\n'

    #LIGHTS
    lstr = '\u21E6 ' if (state['LIGHT'][0]) else '  '
    lstr += '\u21E8 ' if (state['LIGHT'][1]) else '  '
    lstr += '\u29CB ' if (state['LIGHT'][2]) else '  '
    lstr += '\u2600 ' if (state['LIGHT'][3]) else '  '
    string += "LIGHT : " + lstr + '\r\n'

    #MAX_SPEED
    speedVal = state['MAX_SPEED']
    speedStr = '\u2595' #Start of the speed bar
    for i in range(1,6): # i € [1,5]
        speedStr += '\u2588' if (i <= speedVal) else '\u2591'
    string += 'MAX_SPEED : ' + speedStr + '\u258f %d/5\r\n' % (speedVal)

    string += "\r\nToggle help with 'h'\r\n"
    if doHelp:
        string += HELPSPACE + "Move the weelchair with " + str(ARROW_CHAR[0:4]) + '\r\n'
        string += HELPSPACE + "Move actuators with keys from '&' to '='" + '\r\n'
        string += HELPSPACE + "Toggle Lights [o-\u21E6] [p-\u21E8] [w-\u29CB] [l-\u2600]" + '\r\n'
        string += HELPSPACE + "Change max speed with 's'" + '\r\n'
        string += HELPSPACE + "Use the Horn with 'k'" + '\r\n'
    print(string + '\r\n') 
    return



def light_handler(client, key):
    """Turns the lights on or off depending on the input key"""
    lid = KEYS_LIGHT.index(key)
    light = action_light(lid+1) #ID begins with 1
    if lid <= 2: # Turn off flashing left/right or warn when one of them is changed
        state['LIGHT'][0] = (not state['LIGHT'][0]) and lid==0 # flashing Left
        state['LIGHT'][1] = (not state['LIGHT'][1]) and lid==1 # flashing Right
        state['LIGHT'][2] = (not state['LIGHT'][2]) and lid==2 # Warn
    else :
        state['LIGHT'][lid] = not state['LIGHT'][lid]
    client.publish(light.TOPIC_NAME, light.serialize())



def get_kbd(client):
    """Get an input keys in a loop, and performs the corresponding actions"""
    global state
    while state['RUNNING']:

        print_state()
        key = getchar()

        if key in KEYS_ACT:
            id = KEYS_ACT.index(key)
            num, direction = id//2, id%2
            state['ACT'] = [num, direction,TOUT_VALUE_ACT]
        
        if key in KEYS_ARROW:
            id = KEYS_ARROW.index(key)            
            state['JOY'] = [ARROW_XY[id][0], ARROW_XY[id][1], TOUT_VALUE_JOY, id]
        
        if key in KEYS_LIGHT:
            light_handler(client, key)
        
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
            state['ACT'][2] -= 1 #Reduce the watchdog
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
        state['JOY'][2] -= 1 #Reduce the watchdog
        time.sleep(PERIOD_JOY)


client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()
time.sleep(0.2)

msg = action_drive(True)
client.publish(msg.TOPIC_NAME, msg.serialize())
time.sleep(0.2)

daemon_kbd = threading.Thread(target=get_kbd, args=[client], daemon=True)
daemon_act = threading.Thread(target=actuator_thread, args=[client], daemon=True)
daemon_joy = threading.Thread(target=joystick_thread, args=[client], daemon=True)

daemon_kbd.start()
daemon_act.start()
daemon_joy.start()

daemon_kbd.join()
daemon_act.join()
daemon_joy.join()
