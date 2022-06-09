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

KEYS_ACT = ['&','é','"','\'','(','-','è','_','ç','à',')','=']
KEYS_ARROW = ['\x1b[D','\x1b[A','\x1b[C','\x1b[B'] #LEFT UP RIGHT DOWN
ARROW_XY = [[155,0],[0,100],[100,0],[0,155]]
KEYS_LIGHT = ['o','p','w','l'] # LIGHTS : left right warn spots

ARROW_CHAR = ['\u2190','\u2191','\u2192','\u2193','\u25c9'] #LEFT UP RIGHT DOWN CENTER
ACT_NAME = [ #Pour la fct print_state()
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
    'LIGHT' : [False,False,False,False] # Left Right WARNNING SPOTS
}


def print_state(doHelp=False):
    global state

    string = "\x1b[2J\x1b[H\n" # Clear sequence
    string += "JOY : " + ARROW_CHAR[state['JOY'][3]] + '\r\n'

    act_id, direction_id, _ = state['ACT']
    act = ACT_NAME[act_id][0]
    direction = ACT_NAME[act_id][1][direction_id]
    string += "ACT : " + act + ' ' + direction + '\r\n'

    lstr = '\u21E6 ' if (state['LIGHT'][0]) else '  '
    lstr += '\u21E8 ' if (state['LIGHT'][1]) else '  '
    lstr += '\u29CB ' if (state['LIGHT'][2]) else '  '
    lstr += '\u2600 ' if (state['LIGHT'][3]) else '  '
    string += "LIGHT : " + lstr + '\r\n'

    print(string + '\n') 
    return

def light_handler(client, key):
    lid = KEYS_LIGHT.index(key)
    light = action_light(lid)
    if lid <= 2: # Turn off left right or warn when one of them is changed
        state['LIGHT'][0] = (not state['LIGHT'][0]) and lid==0
        state['LIGHT'][1] = (not state['LIGHT'][1]) and lid==1
        state['LIGHT'][2] = (not state['LIGHT'][2]) and lid==2
    else :
        state['LIGHT'][lid] = not state['LIGHT'][lid]
    client.publish(light.TOPIC_NAME, light.serialize())

def get_kbd(client):
    global state
    while state['RUNNING']:

        print_state()
        key = getchar()

        if key in KEYS_ACT:
            id = KEYS_ACT.index(key)
            num, direction = id//2, id%2
            state['ACT'] = [num, direction,TOUT_VALUE_ACT]
            #print("[GET INPUT] : ACT No=%d,Dir=%d" % (num, direction))
        
        if key in KEYS_ARROW:
            id = KEYS_ARROW.index(key)            
            state['JOY'] = [ARROW_XY[id][0], ARROW_XY[id][1], TOUT_VALUE_JOY, id]
        
        if key in KEYS_LIGHT:
            light_handler(client, key)

        elif (key == 'q'):
            state['RUNNING'] = False
    return



def actuator_thread(client):
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
