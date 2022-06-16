"""
This Python script is used to control the wheelchair using the keyboard arrows.
You must have launched the whole project except the Joystick part.
Then run this script and use the arrows to move and 'q' to quit.
WARNNING : When you release a key, the chair takes around 0.5s to stop.
"""


import threading
import time
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
from click import getchar
from gpiozero import Button

PERIOD = 1/30
GPIO_RIGHT_BUTTON = 23
GPIO_LEFT_BUTTON = 26
diff = 1

ARR_U = '\x1b[A'
ARR_D = '\x1b[B'
ARR_R = '\x1b[C'
ARR_L = '\x1b[D'

button = 0x00
long_click = 0
dx = 0
dy = 0
running = True
timeCpt = 0


def get_kbd_mouve():
    global dx
    global dy
    global button
    global running
    global timeCpt
    while running:
        #print("(X=%d,Y=%d) %d" % (x,y, timeCpt))
        key = getchar()
        timeCpt = 8
        if (key == ARR_U):
            dx = 0
            dy = -100
            print("up : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_D):
            dx = 0
            dy = 100
            print("down : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_L):
            dx = -100
            dy = 0
            print("left : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_R):
            dx = 100
            dy = 0
            print("right : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == 'q'):
            dx = 0
            dy = 0
            button = 0x00

        elif (key == 's'): #normalement on utilise pas
            dx = 0
            dy = 0
            button = 0x00
            running = False
            joy_data = joystick_state(button, dx, dy, long_click)
            client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            time.sleep(PERIOD)
        
    # print(button, dx, dy, long_click)
    # joy_data = joystick_state(button, dx, dy, long_click)
    # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    # time.sleep(PERIOD)


#After some time without any key, reset x and y to 0
def stopContinuousMove():
    global dx
    global dy
    global button
    global running
    global timeCpt
    while running:
        if timeCpt > 0:
            timeCpt -= 1
        else:
            #print("Reseted")
            dx = 0
            dy = 0
            button = 0x00
            # joy_data = joystick_state(button, dx, dy, long_click)
            # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            # time.sleep(PERIOD)
        time.sleep(PERIOD)


def get_click():
    global running
    global button
    global timeCpt
    global long_click
    btn_droite = Button(GPIO_RIGHT_BUTTON)
    btn_gauche = Button(GPIO_LEFT_BUTTON)
    while running:
        if btn_droite.is_pressed:
            button = button | 0x02
            # joy_data = joystick_state(button, dx, dy, long_click)
            # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            timeCpt = 1
            start_btn1 = time.monotonic()
            while(btn_droite.is_active):
                timeCpt = 2
                current = time.monotonic()
                delai = current - start_btn1
                #print("Delai: ", delai)
                if delai > diff:
                    print("Appui long sur bouton 1 detecté", "\r")
                    long_clic = 1
                    break
                # joy_data = joystick_state(button, dx, dy, long_click)
                # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    
        elif btn_gauche.is_pressed:
            button = button | 0x01
            # joy_data = joystick_state(button, dx, dy, long_click)
            # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
            timeCpt = 1
            start_btn2 = time.monotonic()
            while(btn_gauche.is_active):
                timeCpt = 2
                current = time.monotonic()
                delai = current - start_btn2
                #print("Delai: ", delai)
                if delai > diff:
                    print("Appui long sur bouton 2 detecté", "\r")
                    long_click = 1
                    break
                # joy_data = joystick_state(button, dx, dy, long_click)
                # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        else:
            button = 0x00
            long_click = 0
            continue #on ne fait rien

        # button = 0x00
        # joy_data = joystick_state(button, dx, dy, long_click)
        # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
        # time.sleep(PERIOD)



client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("Mqtt connection opened")
time.sleep(0.5)

daemon = threading.Thread(target=get_kbd_mouve, daemon=True)
daemon.start()
daemon2 = threading.Thread(target=stopContinuousMove, daemon=True)
daemon2.start()
daemon_click = threading.Thread(target=get_click, daemon=True)
daemon_click.start()


while running:
    joy_data = joystick_state(button, dx, dy, long_click)
    # if(not(button==0x00 and dx==0 and dy==0)):
    #     client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    #     time.sleep(PERIOD)
    client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    time.sleep(PERIOD)

joy_data = joystick_state(button, 0, 0, long_click)