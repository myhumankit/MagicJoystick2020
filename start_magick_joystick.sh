#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "This script must be run as root"
  exit
fi

./bin/Bluetooth/prepare_bluetooth.sh

# Create log directory
export MAGICK_JOY_LOG = `mktemp -d -p /var/log/magick_joy/log`

supervisord -c supervisord.conf
