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
    echo "You can change Wifi SSID & Password by editing $0"
    exit
fi

IP=$1
USER=$2
PWD=$3
IPRESO="192.168.42"
SSID="MagicJostick-$2"
WIFIPSWD="rpimagic123456"
CHANNEL="1"

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
       post-up /sbin/ip link set can0 txqueuelen 1000
       down /sbin/ip link set $IFACE down\n
       up /sbin/ip link set $IFACE up\n
\n
# pican interface1 configuration\n
allow-hotplug can1\n
iface can1 can static\n
       bitrate 125000\n
       post-up /sbin/ip link set can1 txqueuelen 1000
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
remote "sudo apt-get -y install can-utils build-essential python3-venv python3-dev git python3-pip cmake mosquitto bluez libcap2-bin libdbus-1-dev libglib2.0-dev python3-gi libbluetooth-dev pi-bluetooth hostapd dnsmasq v4l-utils > /dev/null"

#config IR
remote "sudo cp /boot/config.txt /boot/config.txt.bak"
read -r -d '' LC_IR_CONFIG << EOF
# MagicJoy IR config starts =========
# Uncomment this to enable the infrared module
#for receiver, enable to receive IR signals
dtoverlay=gpio-ir,gpio_pin=18,rc-map-name=ir-keytable
#for transmitter, enable to send IR signals
dtoverlay=gpio-ir-tx,gpio_pin=17
# MagicJoy IR config stops ==========
EOF
export LC_IR_CONFIG

# Create python virtualenv
echo " -> Creating python virtualenv"
remote 'python -m venv .venv'

# Add python packages
echo " -> Adding extra python packages"
remote_cp requirements.txt .
remote "source .venv/bin/activate && pip3 install -q -r requirements.txt && rm requirements.txt"

# Set python capability to bin to bluetooth even if non root
echo " -> Set python cabability"
remote 'sudo setcap CAP_NET_BIND_SERVICE=+eip $(readlink -f /usr/bin/python3)'

# Install current code
echo " -> Installing Magic Joystick python library"
remote_cp setup.py .
remote_cp magick_joystick .
remote "source .venv/bin/activate && pip3 install -q -e ."

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

# Setup Acces Point Configuration
echo " -> Configure acces point files..."
remote "sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.bak"
read -r -d '' LC_AP_DHCPCD << EOF
# MagicJoy config starts =============\n
# RaspAP wlan0 configuration\n
interface wlan0\n
static ip_address=$IPRESO.1/24\n
static router=$IPRESO.1\n
static domain_name_servers=$IPRESO.1 8.8.8.8\n
# MagicJoy config stops =============\n
EOF
export LC_AP_DHCPCD
remote 'echo -ne $LC_AP_DHCPCD | sudo tee -a /etc/dhcpcd.conf > /dev/null' LC_AP_DHCPCD
remote 'sudo sed -i "s/^[ \t]*//" /etc/dhcpcd.conf' # Remove spaces that begin a line

remote "sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.bak"
read -r -d '' LC_AP_DNSMASQ << EOF
# MagicJoy config starts =============\n
# Listening interface\n
interface=wlan0\n
# Pool of IP addresses served via DHCP\n
dhcp-range=$IPRESO.2,$IPRESO.20,255.255.255.0,24h\n
# Local wireless DNS domain\n
domain=wlan\n
# Alias for this router\n
address=/gw.wlan/$IPRESO.1\n
# MagicJoy config stops =============\n
EOF
export LC_AP_DNSMASQ
remote 'echo -ne $LC_AP_DNSMASQ | sudo tee /etc/dnsmasq.conf > /dev/null' LC_AP_DNSMASQ
remote 'sudo sed -i "s/^[ \t]*//" /etc/dnsmasq.conf' # Remove spaces that begin a line

remote "sudo touch /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.bak"
read -r -d '' LC_AP_HOSTAPD << EOF
# MagicJoy config starts =============\n
driver=nl80211\n
ctrl_interface=/var/run/hostapd\n
ctrl_interface_group=0\n
beacon_int=100\n
auth_algs=1\n
wpa_key_mgmt=WPA-PSK\n
wpa=2\n
wpa_pairwise=CCMP\n
wpa_pairwise=TKIP\n
wpa_passphrase=$WIFIPSWD\n
ssid=$SSID\n
channel=$CHANNEL\n
hw_mode=g\n
interface=wlan0\n
country_code=FR\n
macaddr_acl=0\n
ignore_broadcast_ssid=0\n
# MagicJoy config stops =============\n
EOF
export LC_AP_HOSTAPD
remote 'echo -ne $LC_AP_HOSTAPD | sudo tee /etc/hostapd/hostapd.conf > /dev/null' LC_AP_HOSTAPD
remote 'sudo sed -i "s/^[ \t]*//" /etc/hostapd/hostapd.conf' # Remove spaces that begin a line

remote "sudo cp /etc/default/hostapd /etc/default/hostapd.bak"
read -r -d '' LC_AP_DEFHOSTAPD << EOF
DAEMON_CONF="/etc/hostapd/hostapd.conf"\n
EOF
export LC_AP_DEFHOSTAPD
remote 'echo -ne $LC_AP_DEFHOSTAPD | sudo tee /etc/default/hostapd > /dev/null' LC_AP_DEFHOSTAPD

remote "sudo cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf.bak"
remote 'echo -ne "" | sudo tee /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null'
echo " -> Done configuring acces point files"

echo " -> Lauching Hostapd service"
remote 'sudo systemctl unmask hostapd'
remote 'sudo systemctl enable hostapd'
remote 'sudo rfkill unblock wlan'
remote 'sudo service hostapd start && sudo reboot'

echo " -> Setup done, rebooting"
remote 'sudo reboot'