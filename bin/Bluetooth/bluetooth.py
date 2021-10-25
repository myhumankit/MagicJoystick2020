import dbus
import dbus.service
import os
import socket
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
        self.P_CTRL = 0x0011
        self.P_INTR = 0x0013
        bus = dbus.SystemBus()
        bluez_obj = bus.get_object("org.bluez", "/org/bluez")
        manager = dbus.Interface(bluez_obj, "org.bluez.ProfileManager1")

        BluetoothHIDProfile(bus, self.PROFILE_PATH)
        opts = {
            "AutoConnect": True,
            "ServiceRecord": open("sdp_record.xml", "r").read(),
            "Name": "BTKeyboardProfile",
            "RequireAuthentication": False,
            "RequireAuthorization": False,
            "Service": "MY BTKBD",
            "Role": "server"
        }

        sock_control = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        sock_control.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_inter = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        sock_inter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_control.bind((socket.BDADDR_ANY, self.P_CTRL))
        sock_inter.bind((socket.BDADDR_ANY, self.P_INTR))
        manager.RegisterProfile(self.PROFILE_PATH, "00001124-0000-1000-8000-00805f9b34fb", opts)
        print("Registered")
        sock_control.listen(1)
        sock_inter.listen(1)
        print("waiting for connection")
        self.ccontrol, cinfo = sock_control.accept()
        print("Control channel connected to " + cinfo[self.HOST])
        self.cinter, cinfo = sock_inter.accept()
        print("Interrupt channel connected to " + cinfo[self.HOST])

    def send(self, bytes_buf):
        self.cinter.send(bytes_buf)

drive_state = False
mouse_x = 0
mouse_y = 0
mouse_buttons = 0
speed = 0.1

def on_connect(client, userdata, flags, rc):
  print("Connected to MQTT broker with result code " + str(rc))
  client.subscribe(joystick_state.TOPIC_NAME)
  client.subscribe(action_drive.TOPIC_NAME)


def on_message(client, userdata, msg):
    global drive_state, mouse_x, mouse_y, mouse_buttons, speed

    if msg.topic == action_drive.TOPIC_NAME:
        drive_state = True
    elif msg.topic == joystick_state.TOPIC_NAME:
        joy_position = deserialize(msg.payload)

        if drive_state:
            if joy_position.buttons == 1:
                drive_state = False
            mouse_x = 0
            mouse_y = 0
            mouse_buttons = 0
        else:
            mouse_x = int(joy_position.x * speed)
            mouse_y = int(joy_position.y * speed)
            mouse_buttons = joy_position.buttons

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

    def send_mouse():
        global mouse_x, mouse_y, mouse_buttons
        bthid_srv.send(struct.pack("BBBbb", 0xA1, 0x02, mouse_buttons, mouse_x, mouse_y))
        return True

    GLib.timeout_add(30, send_mouse)

    loop = GLib.MainLoop()
    loop.run()
