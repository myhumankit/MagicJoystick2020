from flask import Flask, send_from_directory, request
from flask_restful import Resource, Api
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *

app = Flask(__name__)

class StaticPages(Resource):
    def get(self, filename = "index.html"):
        files = ["index.html", "wheelchair.html", "style.css",
                 "script.js", "button_default.svg",
                 "button_wheelchair.svg", "button_horn.svg", "button_light.svg", 
                 "button_speed.svg", "button_drive_mode.svg", "button_back.svg",
                 "jquery-3.6.0.min.js", "all.min.css",
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
        elif action == "max_speed":
            data = request.get_json()
            msg = action_max_speed(data["max_speed"])
        elif action == "drive":
            msg = action_drive()
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
        self.client = mqtt.Client() 
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60) 
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
            client.subscribe(status_chair_speed.TOPIC_NAME)
            client.subscribe(status_battery_level.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        global battery_level, chair_speed
        data_current = deserialize(msg.payload)
        if msg.topic == status_battery_level.TOPIC_NAME:
            #self.battery_level = json.dumps({"BATTERY_LEVEL": data_current.battery_level}).encode("utf8")
            battery_level = data_current.battery_level

        elif msg.topic == status_chair_speed.TOPIC_NAME:
            #self.chair_speed = json.dumps({"CHAIR_SPEED": data_current.speedMps*3.6}).encode("utf8")
            chair_speed = data_current.speedMps*3.6

    def get(self):
        global battery_level, chair_speed
        return {"BATTERY_LEVEL": battery_level, "CHAIR_SPEED" : chair_speed}


app = Flask(__name__)
api = Api(app)

api.add_resource(StaticPages, "/<string:filename>", "/", "/webfonts/<string:filename>")
api.add_resource(Actions, "/action/<string:action>")
api.add_resource(CurrentValues, "/current")

if __name__ == "__main__":
    app.run(debug = True, host = "0.0.0.0", port = 8080)
