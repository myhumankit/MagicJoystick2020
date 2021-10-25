#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "This script must be run as root"
  exit
fi

./bin/Bluetooth/prepare_bluetooth.sh

# Create log directory
mkdir -p /var/log/magick_joy/log
export MAGICK_JOY_LOG=`mktemp -d -p /var/log/magick_joy/log`
chown -R pi:pi $MAGICK_JOY_LOG

supervisord -c supervisord.conf
