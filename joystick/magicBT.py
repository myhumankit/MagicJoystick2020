#!/usr/bin/python3

import os
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import paho.mqtt.client as mqtt
import json

# Global variables
state = [0, 0, 0, 0]
waiting_left_click = 0
waiting_right_click = 0

class MouseClient():
    
    def __init__(self):
        super().__init__()
        self.state = [0, 0, 0, 0]
        self.bus = dbus.SystemBus()
        self.btkservice = self.bus.get_object(
            'org.thanhle.btkbservice', '/org/thanhle/btkbservice')
        self.iface = dbus.Interface(self.btkservice, 'org.thanhle.btkbservice')

    def send_current(self):
        try:
            print(self.state)
            self.iface.send_mouse(0, bytes(self.state))
        except OSError as err:
            error(err)

    
DEFAULT_MOUSE_SPEED = 0.4
# This is the Subscriber
speed = DEFAULT_MOUSE_SPEED
def get_mouse_position(rnet_x, rnet_y):

    # Map rnet value between -128 and 127
    t = lambda x: x if x <= 127 else 127-x
    # And back to 2 complement (positive [0; 127], negative [255; 128])
    tinv = lambda x : x if x >= 0 else 255-(127+x)
    
    dx = int(tinv(t(rnet_x) * speed)) & 255
    dy = int(tinv(t(rnet_y) * speed)) & 255

    return dx, dy

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.subscribe("joystick/state")

def on_message(client, userdata, msg):
    global state
    global waiting_left_click
    global waiting_right_click
    
    new_state = json.loads(msg.payload.decode("utf-8"))
    if state[0] == 0:
        if new_state[0] == 1:
            waiting_left_click += 1
        elif new_state[0] == 2:
            waiting_right_click += 1
    
    dx, dy = get_mouse_position(new_state[1], new_state[2])
    new_state[1] = dx
    new_state[2] = dy
    state = new_state.copy()

if __name__ == "__main__":
    bt_mouse_client = MouseClient()
    
    client = mqtt.Client()
    client.connect('localhost',1883,60)

    client.on_connect = on_connect
    
    client.on_message = on_message
    client.loop_start()

    while True:
        if waiting_left_click > 0:
            bt_mouse_client.state[0] = 1
            waiting_left_click -= 1
        else:
            bt_mouse_client.state[0] = 0
        if waiting_right_click > 0:
            bt_mouse_client.state[0] = 2
            waiting_right_click -= 1
        else:
            bt_mouse_client.state[0] = 0
        bt_mouse_client.state[1] = state[1]
        bt_mouse_client.state[2] = state[2]
        bt_mouse_client.state[3] = state[3]
        print("state:", bt_mouse_client.state)
        bt_mouse_client.send_current()

        time.sleep(1/30) 

