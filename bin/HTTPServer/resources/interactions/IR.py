import subprocess
from os import path
import time
from magick_joystick.Topics import *

IR_FILE_EXTENSION = '.txt'

class IR_interaction:
    """
    This class is used to interact with the IR module.
    She is defined by a name who give the group of IR commands and the raw_command file for saving files.

    :param name: The name of the group of IR commands
    :param client: The client who is using the IR module
    :param path: The path of the raw_command file
    """
    def __init__(self, name, client, path, record_time=10):
        self.client = client
        self.name = name
        self.path = path
        self.record_time = record_time

    def get_path(self, id):
        """
        Get the file path of the IR command with the correspondent id

        :param id: The id of the IR command
        """
        return  self.path + self.name + '/' + str(id) + IR_FILE_EXTENSION

    def send(self, id):
        """
        Send the IR command to execute by the module with the correspondent id

        :param id: The id of the IR command
        """
        msg = TV_A_control(id)
        self.client.publish(msg.TOPIC_NAME, msg.serialize())

    def record(self, id):
        """
        Record the IR command with the correspondent id
        A callback is called when the record is done with the id.

        :param id: The id of the IR command
        :param callback: The callback function
        """
        f_string = self.get_path(id)
        print("Path : " + path.abspath(f_string))
        file = open(f_string, "w")
        print('Recording...')
        process = subprocess.Popen(["ir-ctl", "-r",  "-d", "/dev/lirc1", "--mode2", "--one-shot"], stdout=file)   # pass cmd and args to the function
        process.wait(timeout=10)
        print('Done !')  # send Ctrl-C signal
        file.close()

        return id

    def delete(self, id):
        """
        Delete the IR command with the correspondent id

        :param id: The id of the IR command
        """
        os.remove(self.get_path(id))

        return -1