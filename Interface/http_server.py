from flask import Flask, send_from_directory, request
from flask_restful import Resource, Api
import paho.mqtt.client as mqtt
from mqtt_topics import *

app = Flask(__name__)

class StaticPages(Resource):
    def get(self, filename = "index.html"):
        files = ["index.html", "wheelchair.html", "style.css",
                 "script.js", "button_default.png",
                 "button_wheelchair.png", "button_back.png",
                 "jquery-3.6.0.min.js", "all.min.css"]

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
        data = request.get_json()

        if action == "light":
            msg = action_light()
        elif action == "max_speed":
            msg = action_max_speed(data["max_speed"])
        elif action == "drive":
            msg = action_drive(True)
        elif action == "horn":
            msg = action_horn()
        else:
            return "", 404
            
        self.client.publish(msg.TOPIC_NAME, msg.serialize())
        return "", 200

app = Flask(__name__)
api = Api(app)

api.add_resource(StaticPages, "/<string:filename>", "/", "/webfonts/<string:filename>")
api.add_resource(Actions, "/action/<string:action>")

if __name__ == "__main__":
    app.run(debug = True, host = "0.0.0.0", port = 8080)
