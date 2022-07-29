# This python script is used to have a full control of the wheelchair using the keyboard

import time
import paho.mqtt.client as mqtt
from click import getchar
import threading
from magick_joystick.Topics import *

PERIOD_JOY = 1/30
PERIOD_ACT = 1/20
TOUT_VALUE_JOY = 5
TOUT_VALUE_ACT = 5
TOUT_VALUE_CLIC = 5
TIMEOUT_ID = 2
HELPSPACE = "  "

# Movement / Joystick
KEYS_ARROW = ['\x1b[D','\x1b[A','\x1b[C','\x1b[B'] #LEFT UP RIGHT DOWN
ARROW_CHAR = ['\u2190','\u2191','\u2192','\u2193','\u25c9'] #LEFT UP RIGHT DOWN CENTER
VALUES_XY = [[-100,0],[0,100],[100,0],[0,-100]]
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
    'JOY' : [0, 0, -1, -1], # x, y, timeout, id_direction (-1:center, 0:left, 1:up, 2:right, 3:down)
    'SLOW' : False, # Tell if the Joy values in VALUES_XY must be divided by 2
    'CLIC' : [0, 0], # simple left clic, long left clic
    'LIGHT' : [False,False,False,False], # flashing Left/Right, WARNNING, SPOTS
    'AUTO_LIGHT' : False,
    'MAX_SPEED' : 1,
    'HELP' : False,
    'CHAIR_SPEED' : 0.0,
    'BATTERY' : 0.0,
}

# Need to reinit the state
state = state_init.copy() # A real copy, not just reference.

def print_state():
    """Function used to print the current state"""
    global state
    doHelp = state['HELP']

    string = ""
    string += "\x1b[2J\x1b[H\n" # Clear sequence

    string += "MOTOR STATUS : " + state['MOTOR_STATE'] + '\r\n'

    #JOYSTICK
    string += "JOY : " + ARROW_CHAR[state['JOY'][3]] 
    if state['SLOW']:
        string += ' (slowed down)'
    string += '\r\n'

    #CLIC
    clicChar = '\u25cf' if (state['CLIC'][0]==1 or state['CLIC'][1]==1) else '\u25ef'
    string += "CLIC : " + clicChar + '\r\n'

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
    lstr += 'AUTO ' if (state['AUTO_LIGHT']) else '  '
    string += "LIGHT : " + lstr + '\r\n'

    #MAX_SPEED
    speedVal = state['MAX_SPEED']
    speedStr = '\u2595' #Start of the speed bar
    for i in range(1,6): # i € [1,5]
        speedStr += '\u2588' if (i <= speedVal) else '\u2591'
    string += 'MAX_SPEED : ' + speedStr + '\u258f %d/5\r\n' % (speedVal)

    string += "CHAIR_SPEED : %.1f km/h\r\n" % (state['CHAIR_SPEED']*3.6)
    string += "BATTERY : %d\r\n" % state['BATTERY']

    string += "\r\nToggle help with 'h'\r\n"
    if doHelp:
        string += HELPSPACE + "'%c'/'%c' : Turn ON/OFF the wheelchair with " % (KEYS_ONOFF[0],KEYS_ONOFF[1]) + '\r\n'
        string += HELPSPACE + "'d' : Send action_drive command" + '\r\n'
        string += HELPSPACE + "'"
        for k in ARROW_CHAR[0:4]:
            string += str(k)
        string += "' : Move the weelchair/mouse" + '\r\n'
        string += HELPSPACE + "'x' : Go half as fast" + '\r\n'        
        string += HELPSPACE + "'c'/'v' : Do a short clic / Toggle long clic" + '\r\n'
        string += HELPSPACE + "'&' to '=' : Move actuators " + '\r\n'
        string += HELPSPACE + "[%c-\u21E6] [%c-\u21E8] [%c-\u29CB] [%c-\u2600] : Toggle lights" % (KEYS_LIGHT[0],KEYS_LIGHT[1],KEYS_LIGHT[2],KEYS_LIGHT[3]) + '\r\n'
        string += HELPSPACE + "'a' : Toggle automatic lights" + '\r\n'
        string += HELPSPACE + "'s' : Change max speed" + '\r\n'
        string += HELPSPACE + "'k' : Use the horn" + '\r\n'
    print(string + '\r\n') 
    return



def light_handler(client, key):
    """Turns the lights on or off depending on the input key"""
    lid = KEYS_LIGHT.index(key)
    lightMsg = action_light(lid+1) #ID begins with 1

    if lid == FRONT_LIGHTS :
        state['LIGHT'][FRONT_LIGHTS] = not state['LIGHT'][FRONT_LIGHTS]
        client.publish(lightMsg.TOPIC_NAME, lightMsg.serialize())
        return # to Ignore the auto light state

    if lid == WARNING_LIGHT :
        state['LIGHT'][FLASHING_LEFT] = False 
        state['LIGHT'][FLASHING_RIGHT] = False 
        state['LIGHT'][WARNING_LIGHT] = (not state['LIGHT'][WARNING_LIGHT])
    
    elif lid < 2 and not state['LIGHT'][WARNING_LIGHT]: # Flashing (only if no Warn)
        state['LIGHT'][FLASHING_LEFT] = (not state['LIGHT'][FLASHING_LEFT]) and lid==FLASHING_LEFT
        state['LIGHT'][FLASHING_RIGHT] = (not state['LIGHT'][FLASHING_RIGHT]) and lid==FLASHING_RIGHT

    #In case of Flashing change with Warn ON, send a useless frame
    client.publish(lightMsg.TOPIC_NAME, lightMsg.serialize())



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
        
        elif key in KEYS_ARROW:
            id = KEYS_ARROW.index(key)
            if state['SLOW']:
                state['JOY'] = [VALUES_XY[id][X]//2, VALUES_XY[id][Y]//2, TOUT_VALUE_JOY, id]
            else:
                state['JOY'] = [VALUES_XY[id][X], VALUES_XY[id][Y], TOUT_VALUE_JOY, id]
        
        elif key == 'x' :
            state['SLOW'] = not state['SLOW']
        
        elif key in KEYS_LIGHT:
            light_handler(client, key)
        
        elif key == 'a':
            state['AUTO_LIGHT'] = not state['AUTO_LIGHT']
            auto = action_auto_light()
            client.publish(auto.TOPIC_NAME, auto.serialize())
            state['LIGHT'] = [False,False,False,state['LIGHT'][3]]

        elif key == 'd':
            drive = action_drive(True)
            client.publish(drive.TOPIC_NAME, drive.serialize())
            state['MOTOR_STATE'] = 'ON/DRIVE'
        
        elif key == 'c':
            state['CLIC'] = [1, 0]
            state['MOTOR_STATE'] = 'ON/NO_DRIVE'
            drive = action_drive(False)
            client.publish(drive.TOPIC_NAME, drive.serialize())
        
        elif key == 'v': #toggle long clic
            long = state['CLIC'][1]
            long = 1 if (long==0) else 0
            state['CLIC'] = [0, long]
            state['MOTOR_STATE'] = 'ON/NO_DRIVE'
            drive = action_drive(False)
            client.publish(drive.TOPIC_NAME, drive.serialize())
        
        elif key in KEYS_ONOFF:
            if (key == KEYS_ONOFF[0]):
                turn = action_poweron()
                state['MOTOR_STATE'] = "ON/NO_DRIVE"
                drive = action_drive(False)
                client.publish(drive.TOPIC_NAME, drive.serialize())

            else:
                turn = action_poweroff()
                state = state_init.copy()
                state['MOTOR_STATE'] = "OFF"
            client.publish(turn.TOPIC_NAME, turn.serialize())
        
        elif key == 's':
            state['MAX_SPEED'] = state['MAX_SPEED']%5 + 1
            sped = action_max_speed(state['MAX_SPEED'])
            client.publish(sped.TOPIC_NAME, sped.serialize())
        
        elif key == 'k':
            horn = action_horn()
            client.publish(horn.TOPIC_NAME, horn.serialize())
        
        elif key == 'h':
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
        x, y, watchDog_XY, _ = state['JOY']
        if watchDog_XY == 0:
            state['JOY'] = [0,0,0,-1] # To stop moving after 0.5s
            print_state()
        if watchDog_XY >= 0:
            state['JOY'][TIMEOUT_ID] -= 1

        clic, long = state['CLIC']
        clic = 1 if (long==1) else clic #long_clic implique clic

        joy_data = joystick_state(clic, x, y, long)
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())

        if (state['CLIC'][0] != state['CLIC'][1]): #Short clic
            state['CLIC'][0] = 0 #Only one clic
            print_state()
        
        time.sleep(PERIOD_JOY)

def on_connect(client, userdata, flags, rc):
    client.subscribe(status_chair_speed.TOPIC_NAME)
    client.subscribe(status_battery_level.TOPIC_NAME)
    client.subscribe(action_drive.TOPIC_NAME)

def on_message(client, userdata, msg):
    global state
    data = deserialize(msg.payload)
    if msg.topic == status_battery_level.TOPIC_NAME:
        if state['BATTERY'] == data.battery_level:
            return # To not re print the state
        state['BATTERY'] = data.battery_level
    elif msg.topic == status_chair_speed.TOPIC_NAME:
        if state['CHAIR_SPEED'] == data.speedMps:
            return
        state['CHAIR_SPEED'] = data.speedMps
    elif msg.topic == action_drive:
        state['MOTOR_STATE'] = data.doDrive
    print_state()

client = mqtt.Client()
client.on_connect = on_connect 
client.on_message = on_message
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
