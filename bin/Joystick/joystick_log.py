import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import os
from datetime import datetime


class JoyLogger():


    def __init__(self):
        """
        JoyLogger class will log in './logs' folder all datas published on topic 'joystick/log'\n
        It will create one files for each section of drive mode ON. 
        If an 'action/drive' message with False value is recieved, the file is writen with the 'joyLog_HH:MM:SS_DD:MM:YY.csv' formated name.\n
        So, you can make multiple test and truncate logs by simply turning the drive mode ON/OFF.\n
        The file 'logs/joy_log.csv' is a temporary file flushed every second. It will contain datas if a big crash happend.
        """
        
        self.createDirLog()

        self.cpt = 0
        self.doSave = False

        self.f = open("logs/joy_log.csv", "w")

        self.f.write("#x y m1 m2\n")
 
        self.client = mqtt.Client() 
        self.client.on_connect = self.on_connect 
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60) 
        
    def getTimeString(self):
        #Hour-minute-second_day-month-year
        return datetime.now().strftime("%H-%M-%S_%d-%m-%Y")

    def startMe(self):
        """"Start the JoyLogger"""
        self.client.loop_forever()

    def createDirLog(self):
        try:
            os.mkdir("logs")
        except: # Ignore any failure (most of the time the dir is already created)
            pass

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connection successful")
            self.client.subscribe(joy_log.TOPIC_NAME)
            self.client.subscribe(action_drive.TOPIC_NAME)
        else:
            print(f"Connection failed with code {rc}")

    def saveFile(self):
        """Log a file as described on class documentation"""
        self.f.close()
        heure = self.getTimeString()
        try:
            os.rename("logs/joy_log.csv","logs/joyLog_%s.csv"%(heure))
            print("File saved in 'logs/joy_log_%s.csv'" % (heure))
        except:
            print("Could not save the log file as 'logs/joyLog_%s.csv'"%(heure))
            self.createDirLog() # May have been deleted

        self.f = open("logs/joy_log.csv", "w")
        self.doSave = False
        return

    def on_message(self, client, userdata, msg):

        if msg.topic == joy_log.TOPIC_NAME:
            self.cpt += 1 
            state = deserialize(msg.payload)
            self.f.write("%d %d %d %d\n" % (state.x, state.y, state.m1, state.m2))
            if self.cpt%100 == 0:
                print("100 values flushed...")
                self.doSave = True
                self.f.flush()

        elif msg.topic == action_drive.TOPIC_NAME: # A drive False action is send when there is a PowerOff

            doDrive = deserialize(msg.payload).doDrive

            if doDrive: #Change file when drive is false
                return
            
            if self.doSave is False: # Only save more than 1 second of logs
                return
            
            self.saveFile()
            
            


if __name__ == "__main__":
    print(" ===== START LOY JOGGER ===== ")
    jl = JoyLogger()
    jl.startMe()

