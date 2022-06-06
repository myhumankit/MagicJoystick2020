#!/bin/bash

remote()
{
    if [ $# -lt 2 ]; then
        ssh -o LogLevel=QUIET -tt $USER@$IP $1
    else
        ssh -o LogLevel=QUIET -o SendEnv=$2 -tt $USER@$IP $1
    fi
}

remote_cp()
{
    scp -o LogLevel=QUIET -q -r $1 $USER@$IP:$2
}

if [ $# -lt 3 ]; then
    echo "Usage: $0 ip user password"
    exit
fi

IP=$1
USER=$2
PWD=$3

# Get Raspberry Pi version

RASP=`ssh $USER@$IP cat /proc/device-tree/model | tr '\0' '\n'`
RASP_VERSION=`echo $RASP | cut -d ' ' -f 3`
RASP_MODEL=`echo $RASP | cut -d ' ' -f 5`
RASP_REVISION=`echo $RASP | cut -d ' ' -f 7`

echo "Installing on $RASP"

# Add right overlays at startup
echo " -> Updating /boot/config.txt ..."

remote "sudo cp /boot/config.txt /boot/config.txt.bak"

read -r -d '' LC_BOOT << EOF
# MagicJoy config starts =============\n
dtparam=i2c_arm=on\n
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25\n
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=24\n
dtoverlay=spi1-hw-cs\n
dtoverlay=spi0-hw-cs\n
dtparam=krnbt=on\n
# MagicJoy config stops =============\n
EOF

export LC_BOOT

remote 'echo -ne $LC_BOOT | sudo tee -a /boot/config.txt > /dev/null' LC_BOOT

# Add CAN Bus interfaces
echo " -> Updating /etc/network/interfaces for CAN bus ..."

read -r -d '' LC_NETITF << EOF
# pican interface0 configuration\n
allow-hotplug can0\n
iface can0 can static\n
       bitrate 125000\n
       down /sbin/ip link set $IFACE down\n
       up /sbin/ip link set $IFACE up\n
\n
# pican interface1 configuration\n
allow-hotplug can1\n
iface can1 can static\n
       bitrate 125000\n
       down /sbin/ip link set $IFACE down\n
       up /sbin/ip link set $IFACE up\n
EOF

export LC_NETITF

remote 'echo -ne $LC_NETITF | sudo tee /etc/network/interfaces.d/10-can > /dev/null' LC_NETITF

# Add appropriate modules to load
echo " -> Updating /etc/modules"

remote "sudo cp /etc/modules /etc/modules.bak"

read -r -d '' LC_MODULES << EOF
# MagicJoy config starts =============\n
i2c-dev\n
mcp251x\n
can_dev\n
# MagicJoy config stops =============\n
EOF

export LC_MODULES

remote 'echo -ne $LC_MODULES | sudo tee -a /etc/modules > /dev/null' LC_MODULES

# Configure bluetooth daemon startup
echo " -> Modify bluetooth daemon options"
remote 'sudo sed -i "s/ExecStart=.*/ExecStart=\/usr\/libexec\/bluetooth\/bluetoothd --noplugin=\*/g" /lib/systemd/system/bluetooth.service'

# Setup bluetooth configuration
echo " -> Configure bluetooth"
remote 'sudo sed -i "s/\[General\]/\[General\]\nName = MagickJoystick\nClass = 0x002580\nAlwaysPairable = true\nDiscoverableTimeout = 0\n/g" /etc/bluetooth/main.conf'

# Add extra packages
echo " -> Adding extra packages"
remote "sudo apt-get -y update > /dev/null"
remote "sudo apt-get -y install can-utils build-essential python3-dev git python3-pip cmake mosquitto bluez libcap2-bin libdbus-1-dev libglib2.0-dev python3-gi libbluetooth-dev pi-bluetooth > /dev/null"

# Add python packages
echo " -> Adding extra python packages"
remote_cp requirements.txt .
remote "sudo pip3 install -q -r requirements.txt && rm requirements.txt"

# Set python capability to bin to bluetooth even if non root
echo " -> Set python cabability"
remote 'sudo setcap CAP_NET_BIND_SERVICE=+eip $(readlink -f /usr/bin/python3)'

# Install current code
echo " -> Installing Magic Joystick python library"
remote_cp setup.py .
remote_cp magick_joystick .
remote "sudo pip3 install -q -e ."

# Install applications
echo " -> Installing applications"
remote_cp bin .

# Install services
echo " -> Launch applications at startup"
remote_cp start_magick_joystick.sh .
remote_cp supervisord.conf .
remote_cp magick_joystick.service /tmp
remote 'cat /tmp/magick_joystick.service | sed "s|@PWD@|$PWD|g" | sudo tee /lib/systemd/system/magick_joystick.service > /dev/null'
remote 'rm /tmp/magick_joystick.service'
remote 'sudo systemctl daemon-reload > /dev/null'
remote 'sudo systemctl enable magick_joystick > /dev/null'
remote 'sudo systemctl start magick_joystick > /dev/null'

echo " -> Setup done, rebooting"
remote 'sudo reboot'
