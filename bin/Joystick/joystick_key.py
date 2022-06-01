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

PERIOD = 1/30

ARR_U = '\x1b[A'
ARR_D = '\x1b[B'
ARR_R = '\x1b[C'
ARR_L = '\x1b[D'



x = 0
y = 0
running = True
timeCpt = 0

def get_kbd_arrows():
    global x
    global y
    global running
    global timeCpt
    while running:
        key = getchar()
        timeCpt = 15
        if (key == ARR_U):
            #print("Move UP")
            y = 127
        elif (key == ARR_D):
            #print("Move DOWN")
            y = 128
        elif (key == ARR_L):
            #print("Move LEFT")
            x = 128
        elif (key == ARR_R):
            #print("Move RIGHT")
            x = 127
        elif (key == 'q'):
            running = False
    return

#After some time without any key, reset x and y to 0
def stopContinuousMove():
    global x
    global y
    global running
    global timeCpt
    while running:
        if timeCpt > 0:
            timeCpt -= 1
        else:
            #print("Reseted")
            x = 0
            y = 0
        time.sleep(PERIOD)


client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

print("Mqtt connection opened")
time.sleep(0.5)

#On envoit le fait que l'on souhaite piloter
msg = action_drive(True)
client.publish(msg.TOPIC_NAME, msg.serialize())

time.sleep(0.5)
print("Action drive sended, starting loop...")

daemon = threading.Thread(target=get_kbd_arrows, daemon=True)
daemon.start()
daemon2 = threading.Thread(target=stopContinuousMove, daemon=True)
daemon2.start()


button = 0
long_click = 0
while running:
    #print("(X=%d,Y=%d) %d" % (x,y, timeCpt))

    joy_data = joystick_state(button, x, y, long_click)
    client.publish(joy_data.TOPIC_NAME, joy_data.serialize())
    time.sleep(PERIOD)

joy_data = joystick_state(button, 0, 0, long_click)