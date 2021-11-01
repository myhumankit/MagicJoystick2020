# This setup will install all packages and configure the raspberry-pi
# to run MagicJoy software with a Pican-Dual board.
#
# THIS SCRIPT MUST BE RUN WITH: sudo setup.sh
#
#
# 1- update /boot/config.txt file to enable SPI (PiCan board) and I2C
#    (joy ADC and display)
#
# 2- update /etc/network/interfaces to add PiCan net interface
#
# 3- update /etc/modules to load PiCan modules at raspberry startup 
#
# 4- apt install all required packages
#
# 5- pip3 install all python packages (ADC, Screen, ...)
#
#
if [ "$EUID" -ne 0 ]
  then echo "Must run as root: 'sudo ./setup.sh'"
  exit
fi

echo "Updating /boot/config.txt ..."
# ==============================================
cp /boot/config.txt /boot/config.txt.bak
read -r -d '' BOOT_CFG << EOF

# MagicJoy config starts =============
dtparam=i2c_arm=on
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=24
dtoverlay=spi1-hw-cs
dtoverlay=spi0-hw-cs
# MagicJoy config stops =============
EOF
echo $BOOT_CFG >> /boot/config.txt

echo "Updating /etc/network/interfaces ..."
# ==============================================
cp /etc/network/interfaces /etc/network/interfaces.bak
read -r -d '' NET_ITF << EOF
# MagicJoy config starts =============
# pican interface0 configuration
allow-hotplug can0
iface can0 can static
       bitrate 125000
       down /sbin/ip link set $IFACE down
       up /sbin/ip link set $IFACE up

# pican interface1 configuration
allow-hotplug can1
iface can1 can static
       bitrate 125000
       down /sbin/ip link set $IFACE down
       up /sbin/ip link set $IFACE up
# MagicJoy config stops =============
EOF
echo "$NET_IF" >> /etc/network/interfaces


echo "Updating /etc/modules ..."
# ==============================================
cp /etc/modules /etc/modules.bak
read -r -d '' MODULES << EOF
# MagicJoy config starts =============
i2c-dev
mcp251x
can_dev
# MagicJoy config stops =============
EOF
echo "$MODULES" >> /etc/modules

echo "running apt-update and installing required modules ..."
# ===========================================================
apt-get -y update
apt-get -y install can-utils build-essential python3-dev git python3-pip cmake
apt-get -y install mosquitto bluez libcap2-bin
echo "running pip3 and installing required modules ..."
# ===========================================================
pip3 install -r requirements.txt

echo "Installing Magick Joystick python library"
pip3 install -e .

echo "Installing service startup"
cat magick_joystick.service | sed "s|@PWD@|$PWD|g" > /etc/systemd/system/magick_joystick.service

echo "Setup done"
echo ""
echo "Reboot your raspberry now."
