from sys import stdin
from flask import Flask, send_from_directory, request, render_template, make_response
from flask_restful import Resource, Api
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import os
import time
import subprocess
import signal

app = Flask(__name__)
lights = [False, False, False, False]
drive_mode = False #pas en mode drive au démarrage
battery_level = 7 #valeur d'init (fausse)
chair_speed = -1.0 #valeur d'init (fausse)
max_speed_level = 1 #valeur par défaut à au power on

#Lights
FLASHING_LEFT = 0
FLASHING_RIGHT = 1
WARNING_LIGHT = 2
FRONT_LIGHTS = 3

#IR
RECORD_TIME = 10 #in seconds
last = -1 #NUMBER OF LAST TV_A COMMAND
validate = []
NB_COMMAND = 28

def init_validate():
    global validate
    for i in range (NB_COMMAND):
        validate.append(os.path.exists("../IR/TV_A_raw_command/TV_A_" + str(i) + ".txt"))
    return validate

'''
    Verify if the raw command file exists
'''
def check_files_TV_A():
    global validate
    state = []
    for i in range (NB_COMMAND):
        state.append(os.path.exists("../IR/TV_A_raw_command/TV_A_" + str(i) + ".txt"))
        if(validate[i]==True and state[i]==False):
            validate[i] = False
    return state

class StaticPages(Resource):
    def get(self, folder = "", filename = "index.html"):
        """
        Return the static page requested from folder and filename
        If folder is null, return the file from the views folder
        """
        print(folder, filename)

        if folder == "":
            if filename in os.listdir("templates"):
                return make_response(render_template(filename))
            
            print("%s: file not found" % filename)
            return "", 404

        folders = ["css", "js", "img", "fonts", "fonts", "svg_icon"]

        if folder in folders and filename in os.listdir(folder):
            return send_from_directory(folder,filename)

        print("%s: file not found" % filename)
        return "", 404


class MagicResource(Resource):
    def __init__(self):
        self.client = mqtt.Client() 
        self.client.on_connect = self.__on_connect 
        self.client.connect("localhost", 1883, 60) 
        self.client.loop_start()
        self.name = "topic_name"
        self.commands = {}

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful to "+self.name)
        else:
            print(f"Connection failed with code {rc}")
        
    def post(self, command):
        if command in self.commands:
            msg = self.commands[command](request.get_json())
            self.client.publish(msg.TOPIC_NAME, msg.serialize())
            return "", 200
        
        return "", 404

class Actions(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "Action"
        self.commands = {
            "light": lambda data: action_light(data["light_id"]),
            "auto_light": lambda data: action_auto_light(),
            "max_speed": lambda data: action_max_speed(data["max_speed"]),
            "drive": lambda data: action_drive(True),
            "horn": lambda data: action_horn(),
            "actuator_ctrl": lambda data: action_actuator_ctrl(data["actuator_num"], data["direction"]),
            "poweroff": lambda data: action_poweroff(),
            "poweron": lambda data: action_poweron()
        }

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.subscribe(action_max_speed.TOPIC_NAME)
            print("Connection successful to Action")
        else:
            print(f"Connection failed with code {rc}")
    
    def get(self, action):
        global max_speed_level
        if action == "max_speed":
            return {"MAX_SPEED": max_speed_level}

    def post(self, action):
        global max_speed_level

        if action == "max_speed":
            max_speed_level = request.get_json()["max_speed"]

        return super().post(action)


class CurrentValues(Resource):
    def __init__(self):
        pass
    
    def get(self, topic):
        global battery_level, chair_speed, drive_mode
        if topic == "time-battery":
            return {"BATTERY_LEVEL": battery_level}
        elif topic == "lights-speed-driveMode":
            print("get request", lights)
            return {"DRIVE_MODE": drive_mode, "CHAIR_SPEED" : chair_speed, "LIGHTS": lights}
            #return {"CHAIR_SPEED" : chair_speed, "LIGHTS": lights}


class TV(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "TV"
        self.commands = {
            "power":      lambda data: TV_power(),
            "volume":     lambda data: TV_volume(data["type"]),
            "param":      lambda data: TV_param(data["type"]),
            "direction":  lambda data: TV_direction(data["type"]),
            "number":     lambda data: TV_number(data["nb"]),
        }


class TV_A(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "TV_auto"
        self.commands = {}
    
    def get(self, command):
        if command == "buttons":
            return {"BUTTONS":check_files_TV_A(), "VALIDATE": validate}
        else:
            return "", 404

    def post(self, command):
        global last

        if command == "control": #send the command
            data = request.get_json()
            msg = TV_A_control(data["id"])
            self.client.publish(msg.TOPIC_NAME, msg.serialize())
        elif command == "get": #record the command
            data = request.get_json()
            id = data["id"]
            f_string = "../IR/TV_A_raw_command/" + "TV_A_" + str(id) +  ".txt"
            file = open(f_string, "w")
            process = subprocess.Popen(["ir-ctl", "-r",  "-d", "/dev/lirc1", "--mode2"], stdout=file)   # pass cmd and args to the function
            time.sleep(RECORD_TIME)
            process.send_signal(signal.SIGINT)   # send Ctrl-C signal
            file.close()
            if(os.stat(f_string).st_size == 0):
                os.remove(f_string)
                return data["id"], 449
            else:
                last = data["id"]
        elif command == "delete": #delete the command
            data = request.get_json()
            id = data["id"]
            f_string = "../IR/TV_A_raw_command/" + "TV_A_" + str(id) +  ".txt"
            os.remove(f_string)
            last = -1
        elif command == "last-launch": #send the last command recorded
            msg = TV_A_control(last)
            self.client.publish(msg.TOPIC_NAME, msg.serialize())
        elif command == "last-delete": #delete the last command recorded
            f_string = "../IR/TV_A_raw_command/" + "TV_A_" + str(last) +  ".txt"
            os.remove(f_string)
            last = -1
        elif command == "last-modify": #modify the last command recorded
            f_string = "../IR/TV_A_raw_command/" + "TV_A_" + str(last) +  ".txt"
            file = open(f_string, "w")
            process = subprocess.Popen(["ir-ctl", "-r",  "-d", "/dev/lirc1", "--mode2"], stdout=file)   # pass cmd and args to the function
            time.sleep(RECORD_TIME)
            process.send_signal(signal.SIGINT)   # send Ctrl-C signal
            file.close()
            if(os.stat(f_string).st_size == 0):
                os.remove(f_string)
                return data["id"], 449
        elif command == "last-validate": #validate the last command recorded
            validate[last] = True
        elif command == "last-get": #get the number of the last command recorded
            pass

        else:
            return "", 404

        return last, 200



def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful to chair_speed, battery, light, drive_mode")
            client.subscribe(status_chair_speed.TOPIC_NAME)
            client.subscribe(status_battery_level.TOPIC_NAME)
            client.subscribe(action_light.TOPIC_NAME)
            client.subscribe(action_drive.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    global battery_level, chair_speed, drive_mode
    data_current = deserialize(msg.payload)
    if msg.topic == status_battery_level.TOPIC_NAME:
        battery_level = data_current.battery_level

    elif msg.topic == status_chair_speed.TOPIC_NAME:
        chair_speed = data_current.speedMps*3.6
    
    elif msg.topic == action_drive.TOPIC_NAME:
        drive_mode = deserialize(msg.payload).doDrive

    elif msg.topic == action_light.TOPIC_NAME:
        lid = data_current.light_id-1
        if lid == FRONT_LIGHTS :
            lights[lid] = not lights[lid] #light_ID begins at 1
            return

        if lid == WARNING_LIGHT :
            lights[FLASHING_LEFT] = False 
            lights[FLASHING_RIGHT] = False 
            lights[lid] = not lights[lid]
    
        elif lid < 2 and not lights[WARNING_LIGHT]: # Flashing (only if no Warn)
            lights[FLASHING_LEFT] = (not lights[FLASHING_LEFT]) and lid==FLASHING_LEFT
            lights[FLASHING_RIGHT] = (not lights[FLASHING_RIGHT]) and lid==FLASHING_RIGHT


app = Flask(__name__)
api = Api(app)

api.add_resource(StaticPages,
    "/v/",
    "/v/<string:filename>",
    "/v/<string:folder>/<string:filename>",)
api.add_resource(Actions, "/action/<string:action>")
api.add_resource(CurrentValues, "/current/<string:topic>")
api.add_resource(TV, "/TV/<string:command>")
api.add_resource(TV_A, "/TV_A/<string:command>")

if __name__ == "__main__":
    validate = init_validate()
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_start()

    app.run(debug = True, host = "0.0.0.0", port = 8080)
