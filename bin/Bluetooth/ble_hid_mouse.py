import dbus
import dbus.service
import os
import socket
from bluetooth import BluetoothSocket, L2CAP
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import paho.mqtt.client as mqtt
from magick_joystick.Topics import *
import struct

class BluetoothHIDProfile(dbus.service.Object):
    def __init__(self, bus, path):
        super(BluetoothHIDProfile, self).__init__(bus, path)
        self.fd = -1

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        dbus.mainloop.quit()

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Cancel(self):
        raise NotImplementedError("Cancel")

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("New Connection from (%s, %d)" % (path, self.fd))
        for k, v in properties.items():
            if k == "Version" or k == "Features":
                print("    %s = 0x%04x " % (k, v))
            else:
                print("    %s = %s" % (k, v))

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))

        if (self.fd > 0):
            os.close(self.fd)
            self.fd = -1

class BluetoothHIDService(object):
    PROFILE_PATH = "/org/bluez/bthid_profile"

    HOST = 0
    PORT = 1

    def __init__(self):
        self.P_CTRL = 0x0011 # Must match sdp_record.xml
        self.P_INTR = 0x0013 # Must match sdp_record.xml
        bus = dbus.SystemBus()
        bluez_obj = bus.get_object("org.bluez", "/org/bluez")
        manager = dbus.Interface(bluez_obj, "org.bluez.ProfileManager1")

        BluetoothHIDProfile(bus, self.PROFILE_PATH)
        opts = {
            "AutoConnect": True,
            "ServiceRecord": open("sdp_record.xml", "r").read(),
            "RequireAuthentication": False,
            "RequireAuthorization": False,
            "Role": "server"
        }
        
        manager.RegisterProfile(self.PROFILE_PATH, "00001124-0000-1000-8000-00805f9b34fb", opts)

        
    def wait_connect_device(self):
        sock_control = BluetoothSocket(L2CAP)
        sock_control.bind((socket.BDADDR_ANY, self.P_CTRL))

        sock_inter = BluetoothSocket(L2CAP)
        sock_inter.bind((socket.BDADDR_ANY, self.P_INTR))

        print("Registered")
        sock_control.listen(5)
        sock_inter.listen(5)
        print("waiting for connection")
        self.ccontrol, cinfo = sock_control.accept()
        print("Control channel connected to " + cinfo[self.HOST])
        self.cinter, cinfo = sock_inter.accept()
        print("Interrupt channel connected to " + cinfo[self.HOST])
        

    def send(self, bytes_buf):
        try :
            self.cinter.send(bytes_buf)
        except Exception:
            self.wait_connect_device()

drive_state = False
mouse_x = 0
mouse_y = 0
mouse_buttons = 0
speed = 0.25

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(joystick_state.TOPIC_NAME)
    client.subscribe(action_drive.TOPIC_NAME)


def on_message(client, userdata, msg):
    global drive_state, mouse_buttons, mouse_x, mouse_y, speed
    data = deserialize(msg.payload)
    if msg.topic == action_drive.TOPIC_NAME:
        drive_state = data.doDrive
        print("[recv %s] Switch to drive mode %s" %(msg.topic, drive_state))
        
    elif msg.topic == joystick_state.TOPIC_NAME:
        joy_position = data

        if drive_state:
            if joy_position.buttons == 1:
                print("[CLIC] Switch to drive mode OFF")
                drive_state = False
                drive = action_drive(False)
                client.publish(drive.TOPIC_NAME, drive.serialize())
                
            mouse_x = 0
            mouse_y = 0
            mouse_buttons = 0
        else:
            mouse_buttons = joy_position.buttons
            mouse_x = int(speed * joy_position.x)
            mouse_y = -int(speed * joy_position.y)

if __name__ == "__main__":
    # MQTT connexion
    client = mqtt.Client()

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect('localhost',1883,60)
    client.loop_start()

    # BT DBUS connexion
    DBusGMainLoop(set_as_default = True)
    
    bthid_srv = BluetoothHIDService()
    bthid_srv.wait_connect_device()

    def send_mouse():
        global mouse_x, mouse_y, mouse_buttons
        if( (mouse_x != 0) | (mouse_y != 0)| (mouse_buttons!=0) ):
            print("mouse_send", mouse_buttons, mouse_x, mouse_y)
        bthid_srv.send(struct.pack("BBbb", 0xA1, mouse_buttons, mouse_x, mouse_y))
        return True

    GLib.timeout_add(30, send_mouse)

    loop = GLib.MainLoop()
    loop.run()
