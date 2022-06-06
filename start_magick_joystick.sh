#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "This script must be run as root"
  exit
fi

# TODO: see if we can make this the default behaviour in bluetooth configuration
# Make bluetooth discoverable
hciconfig hci0 name MagickJoystick
hciconfig hci0 class 0x2580
hciconfig hci0 noauth
hciconfig hci0 piscan

# Create log directory
mkdir -p /var/log/magick_joy/log
export MAGICK_JOY_LOG=`mktemp -d -p /dev/shm/log/magick_joy/log`
chown -R 1000:1000 $MAGICK_JOY_LOG

supervisord -c supervisord.conf
