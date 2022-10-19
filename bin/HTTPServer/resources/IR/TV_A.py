import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import MagicResource
from flask_restful import Resource, request
from interactions.IR import IR_interaction

#IR
RECORD_TIME = 10 #in seconds
last = -1 #NUMBER OF LAST TV_A COMMAND
validate = []
NB_COMMAND = 28
IR_PATH = "../IR/raw_command/" #../IR/TV_A_raw_command/
IR_FILE_PREFIX = "" # TV_A_
IR_FILE_EXTENSION = ".txt"


def set_last(id):
    global last
    last = id

class TV_A(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "TV_auto"
        self.commands = {}
        self.recorder = IR_interaction('TV_A', self.client, IR_PATH, RECORD_TIME)
    
    
    '''
        Verify if the raw command file exists
    '''
    def check_files(self):
        state = []
        for i in range (NB_COMMAND):
            state.append(os.path.exists(self.recorder.get_path(i)))
        return state

    def get(self, command):
        if command == "buttons":
            return {"BUTTONS":self.check_files(), "VALIDATE": self.check_files()}
        else:
            return "", 404

    def post(self, command):
        if command == "control": #send the command
            data = request.get_json()
            self.recorder.send(data["id"])

        elif command == "get": #record the command
            data = request.get_json()
            set_last(self.recorder.record(data["id"]))

        elif command == "delete": #delete the command
            data = request.get_json()
            id = data["id"]

            set_last(self.recorder.delete(id))

        elif command == "last-launch": #send the last command recorded
            msg = TV_A_control(last)
            self.client.publish(msg.TOPIC_NAME, msg.serialize())

        elif command == "last-delete": #delete the last command recorded
            set_last(self.recorder.delete(last))

        elif command == "last-modify": #modify the last command recorded
            set_last(self.recorder.record(last))
            
        elif command == "last-validate": #validate the last command recorded
            validate[last] = True

        elif command == "last-get": #get the number of the last command recorded
            pass

        else:
            return "", 404

        return last, 200