#!/bin/bash

# Start Bluetooth
hciconfig hci0 up

# Set device name
hciconfig hci0 name MagickJoystick

# Configure device as HID Mouse
hciconfig hci0 class 2580

# Make the device discoverable
hciconfig hci0 piscan

# Set the right capability to python interpreter to be able to run scripts as non-root
setcap CAP_NET_BIND_SERVICE=+eip $(readlink -f /usr/bin/python3)
