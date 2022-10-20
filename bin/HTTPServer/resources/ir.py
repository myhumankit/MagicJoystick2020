from flask_restful import Resource, request
from base import MagicResource
import sys
import os
from magick_joystick.Topics import *

# from interactions.IR import IR_interaction

#IR
RECORD_TIME = 10 #in seconds
last = -1 #NUMBER OF LAST TV_A COMMAND
validate = []
NB_COMMAND = 28
IR_PATH = "../IR/raw_command/"
IR_FILE_PREFIX = "" # TV_A_
IR_FILE_EXTENSION = ".txt"


def set_last(id):
    global last
    last = id

class IR(MagicResource):
    
    def __init__(self):
        super().__init__()
        self.name = "IR"
        self.commands = {}

    def get(self, folder, action):
        msg = IR_execute(folder, action)
        self.client.publish(msg.TOPIC_NAME, msg.serialize())

        
    def post(self, folder, action):
        msg = IR_write(folder, action)
        self.client.publish(msg.TOPIC_NAME, msg.serialize())
