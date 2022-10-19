import paho.mqtt.client as mqtt
from flask import request
from flask_restful import Resource

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