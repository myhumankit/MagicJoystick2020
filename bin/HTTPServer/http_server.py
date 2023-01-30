from sys import stdin
from flask import Flask, send_from_directory, request, render_template, make_response
from flask_restful import Resource, Api
from flask_cors import CORS
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import os
import time
import subprocess
import signal
from urllib.request import urlopen

from resources.static_pages import StaticPages

from resources.IR.TV_A import TV_A
from resources.TV import TV
from resources.ir import IR

from resources.base import MagicResource
from resources.actions import Actions
from resources.current_values import CurrentValues, update_current_values

app = Flask(__name__)
CORS(app)

#Resource loading system
LOADING_METHOD = 'static'
SCRIPT_PATH = './js/'
STYLE_PATH = './css/'
ICON_PATH = './svg_icon/'
#API_PATH = 'localhost:8080'
API_PATH = ''

#Lights
FLASHING_LEFT = 0
FLASHING_RIGHT = 1
WARNING_LIGHT = 2
FRONT_LIGHTS = 3

def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful to chair_speed, battery, light, drive_mode")
            client.subscribe(status_chair_speed.TOPIC_NAME)
            client.subscribe(status_battery_level.TOPIC_NAME)
            client.subscribe(action_light.TOPIC_NAME)
            client.subscribe(action_drive.TOPIC_NAME)
            client.subscribe(IR_response.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    update_current_values(msg)

# Static loading functions
def get_content(filename):
    with open(filename, "r") as f:
        return f.read()

def static_load_script(src):
    return get_content(SCRIPT_PATH + src)

def static_load_style(href):
    return get_content(STYLE_PATH + href)

def static_load_icon(src):
    return get_content(ICON_PATH + src)
    

api = Api(app)

api.add_resource(StaticPages,
    "/v/",
    "/v/<string:filename>",
    "/v/<string:folder>/<string:filename>",)
api.add_resource(Actions, "/action/<string:action>")
api.add_resource(CurrentValues, "/current/<string:topic>")

api.add_resource(IR, "/IR/<string:folder>/<string:action>")

api.add_resource(TV, "/TV/<string:command>")
api.add_resource(TV_A, "/TV_A/<string:command>")

app.jinja_env.globals.update(static_load_script=static_load_script)
app.jinja_env.globals.update(static_load_style=static_load_style)
app.jinja_env.globals.update(static_load_icon=static_load_icon)
app.jinja_env.globals.update(LOADING_METHOD=LOADING_METHOD)
app.jinja_env.globals.update(API_PATH=API_PATH)
app.jinja_env.globals.update(MQTT_HOSTNAME="192.168.42.1")
app.jinja_env.globals.update(MQTT_PORT="1883")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_start()

    app.run(debug = True, host = "0.0.0.0", port = 8080)

