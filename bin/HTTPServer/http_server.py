from flask import Flask, send_from_directory, request
from flask_restful import Resource, Api
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

app = Flask(__name__)
lights = [False, False, False, False]
drive_mode = False
battery_level = 7 #valeur d'init (fausse)
chair_speed = -1.0 #valeur d'init (fausse)

#Lights
FLASHING_LEFT = 0
FLASHING_RIGHT = 1
WARNING_LIGHT = 2
FRONT_LIGHTS = 3

class StaticPages(Resource):
    def get(self, filename = "index.html"):
        files = ["index.html", "wheelchair.html", "style.css",
                 "script.js", "button_default.svg",
                 "button_wheelchair.svg", "button_horn.svg", "button_light.svg", 
                 "button_speed.svg", "button_drive_mode.svg", "button_drive_mode_on.svg", "button_back.svg",
                 "jquery-3.6.0.min.js", "all.min.css",
                 "IR.html", "IR.svg", "TV.html", "TV.svg", 
                 "button_power.svg", "button_0.svg", "button_1.svg", "button_2.svg", "button_3.svg", 
                 "button_4.svg", "button_5.svg", "button_6.svg", 
                 "button_7.svg", "button_8.svg", "button_9.svg", 
                 "mute.svg", "volume_up.svg", "volume_down.svg",
                 "left.svg", "down.svg", "right.svg", "up.svg", "ok.svg", 
                 "TV_exit.svg", "TV_home.svg", "TV_info.svg", "TV_menu.svg", "TV_return.svg", "TV_source.svg", "TV_tools.svg",
                 "actuator.html", "actuator_0_0.svg", "actuator_0_1.svg",
                 "actuator_1_0.svg", "actuator_1_1.svg", "actuator_2_0.svg",
                 "actuator_2_1.svg", "actuator_3_0.svg", "actuator_3_1.svg",
                 "actuator_4_0.svg", "actuator_4_1.svg", "actuator_5_0.svg",
                 "actuator_5_1.svg", "actuator.svg", "light.html"]

        fonts = ["fa-solid-900.woff2", "fa-brands-400.woff2"]

        print(filename)

        if (filename in files) or (filename in fonts):
            return send_from_directory("html", filename)
        else:
            print("%s: file not found" % filename)
            return "", 404

class Actions(Resource):
    def __init__(self):
        self.client = mqtt.Client() 
        self.client.on_connect = self.__on_connect 
        self.client.connect("localhost", 1883, 60) 
        self.client.loop_start()

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
        else:
            print(f"Connection failed with code {rc}")

    def post(self, action):
        if action == "light":
            data = request.get_json()
            msg = action_light(data["light_id"])
        elif action == "auto_light":
            msg = action_auto_light()
        elif action == "max_speed":
            data = request.get_json()
            msg = action_max_speed(data["max_speed"])
        elif action == "drive":
            msg = action_drive(True)
        elif action == "horn":
            msg = action_horn()
        elif action == "actuator_ctrl":
            data = request.get_json()
            msg = action_actuator_ctrl(data["actuator_num"], data["direction"])
        elif action == "poweroff":
            msg = action_poweroff()
        elif action == "poweron":
            msg = action_poweron()
        else:
            return "", 404
            
        self.client.publish(msg.TOPIC_NAME, msg.serialize())
        return "", 200


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


class TV(Resource):
    def __init__(self):
        self.client = mqtt.Client() 
        self.client.on_connect = self.__on_connect 
        self.client.connect("localhost", 1883, 60) 
        self.client.loop_start()
    
    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
        else:
            print(f"Connection failed with code {rc}")

    def post(self, command):
        if command == "power":
            msg = TV_power()
        # if command == "power_on":
        #     msg = TV_power(True)
        # if command == "power_off":
        #     msg = TV_power(False)
        elif command == "mute":
            msg = TV_mute()

        else:
            return "", 404

        self.client.publish(msg.TOPIC_NAME, msg.serialize())
        return "", 200



def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
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
        #self.battery_level = json.dumps({"BATTERY_LEVEL": data_current.battery_level}).encode("utf8")
        battery_level = data_current.battery_level

    elif msg.topic == status_chair_speed.TOPIC_NAME:
        #self.chair_speed = json.dumps({"CHAIR_SPEED": data_current.speedMps*3.6}).encode("utf8")
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

api.add_resource(StaticPages, "/<string:filename>", "/", "/webfonts/<string:filename>")
api.add_resource(Actions, "/action/<string:action>")
api.add_resource(CurrentValues, "/current/<string:topic>")
api.add_resource(TV, "/TV/<string:command>")

if __name__ == "__main__":
    client = mqtt.Client() 
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.loop_start()

    app.run(debug = True, host = "0.0.0.0", port = 8080)
