
import time
import paho.mqtt.client as mqtt
from click import getchar
import threading
from magick_joystick.Topics import *


PERIOD = 1/20 #Attention! Freq de 20Hz pour les verrins


dicKey = {
    '&':0,
    'é':1, 
    '"':2, 
    '\'':3, 
    '(':4, 
    '-':5, 
    'è':6, 
    '_':7, 
    'ç':8, 
    'à':9, 
    ')':10, 
    '=':11
}

running = True
frameToSend = -1
isMoving = False

def handle_keyboard():
    global dicKey
    global running
    global frameToSend
    global isMoving
    while running:
        print("Wait input <-- ", end=' ', flush=True)
        key = getchar(echo=True)
        print()
        if(key=='q') :
            running = False
            print("Stopped")
            break
        new = dicKey[key]
        isMoving = (frameToSend != new)
        frameToSend = new
    return

def sendFrames():
    global running
    global frameToSend
    global isMoving

    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    client.loop_start()

    while running:
        if isMoving:
            act = action_actuator_ctrl(frameToSend//2,frameToSend%2)
            print("Sending act=%d, dir=%d" % (frameToSend//2,frameToSend%2))
            client.publish(act.TOPIC_NAME, act.serialize())
        time.sleep(PERIOD)
    return

d1 = threading.Thread(target=handle_keyboard, daemon=True)
d2 = threading.Thread(target=sendFrames, daemon=True)
d1.start()
d2.start()


d1.join()
d2.join()

print("End")
