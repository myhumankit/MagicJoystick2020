import os
import subprocess
from os import path

# Configuration
IR_FILE_EXTENSION = 'txt'
IR_PATH = "../IR/raw_command/"

def get_path(folder, action):
    return "%s%s/%s.%s"%(IR_PATH, folder, action, IR_FILE_EXTENSION)

def record(folder, action, callback):
    f_string = get_path(folder, action)
    print("Path : " + path.abspath(f_string))

    print('Recording...')
    file = open(f_string, "w")
    process = subprocess.Popen(["ir-ctl", "-r",  "-d", "/dev/lirc1", "--mode2", "--one-shot"], stdout=file)
    process.wait()
    file.close()
    print('Done !')

    callback([folder, action, True])

def execute(folder, action):
    os.system("sudo ir-ctl -d /dev/lirc0 -s %s"%(get_path(folder, action)))

def delete(folder, action):
    os.remove(get_path(folder, action))
