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
    global running
    global timeCpt
    while running:
        #print("(X=%d,Y=%d) %d" % (x,y, timeCpt))
        key = getchar()
        timeCpt = 15
        if (key == ARR_U):
            #print("Move UP")
            dx = 0
            dy = -10
            print("up : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_D):
            #print("Move DOWN")
            dx = 0
            dy = 10
            print("down : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_L):
            #print("Move LEFT")
            dx = -10
            dy = 0
            print("left : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == ARR_R):
            #print("Move RIGHT")
            dx = 10
            dy = 0
            print("right : [" + str(dx) + ";" + str(dy) + "]")
        elif (key == 'q'):
            dx = 0
            dy = 0
            button = 0x00
            long_click = 0
        
    # print(button, dx, dy, long_click)
    # joy_data = joystick_state(button, dx, dy, long_click)
    # client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    # time.sleep(PERIOD)


#After some time without any key, reset x and y to 0
def stopContinuousMove():
    global dx
    global dy
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
        time.sleep(PERIOD)


def get_clik():
    global running
    global button
    while running:
        if Button(GPIO_RIGHT_BUTTON).is_pressed: 
            start_btn1 = time.monotonic()
            while(Button(GPIO_RIGHT_BUTTON).is_active):
                current = time.monotonic()
                delai = current - start_btn1
                #print("Delai: ", delai)
                if  delai > diff:
                    print("Appui long sur bouton 1 detecté", "\r")
                    long_clic = 1
                    break                   
            button = button | 0x02
            joy_data = joystick_state(button, dx, dy, long_click)
            client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    
        elif Button(GPIO_LEFT_BUTTON).is_pressed:
            start_btn2 = time.monotonic()
            while(Button(GPIO_LEFT_BUTTON).is_active):
                current = time.monotonic()
                delai = current - start_btn2
                #print("Delai: ", delai)
                if  delai > diff:
                    print("Appui long sur bouton 2 detecté", "\r")
                    long_clic = 1
                    break       
            button = button | 0x01
            joy_data = joystick_state(button, dx, dy, long_click)
            client.publish(joy_data.TOPIC_NAME, joy_data.serialize())

        button = 0x00



client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("Mqtt connection opened")
time.sleep(0.5)

daemon = threading.Thread(target=get_kbd_mouve, daemon=True)
daemon.start()
daemon2 = threading.Thread(target=stopContinuousMove, daemon=True)
daemon2.start()
daemon_click = threading.Thread(target=get_clik, daemon=True)
daemon_click.start()

previous_state = joystick_state(button, dx, dy, long_click)
client.publish(previous_state.TOPIC_NAME, previous_state.serialize())
time.sleep(PERIOD)

while running:
    joy_data = joystick_state(button, dx, dy, long_click)
    if(previous_state != joy_data):
        client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    previous_state = joy_data
    time.sleep(PERIOD)

joy_data = joystick_state(button, 0, 0, long_click)