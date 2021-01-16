# This setup will install all packages and configure the raspberry-pi
# to run MagicJoy software
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
echo "# MagicJoy config starts ============="  >> /boot/config.txt
echo "dtparam=i2c_arm=on" >> /boot/config.txt
echo "dtparam=spi=on"  >> /boot/config.txt
echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25"  >> /boot/config.txt
echo "dtoverlay=spi-bcm2835"  >> /boot/config.txt
echo "dtoverlay=spi1-1cs"  >> /boot/config.txt
echo "# MagicJoy config stops ============="  >> /boot/config.txt

echo "Updating /etc/network/interfaces ..."
# ==============================================
cp /etc/network/interfaces /etc/network/interfaces.bak
echo "# MagicJoy config starts ============="  >> /etc/network/interfaces
echo "# pican interface configuration "  >> /etc/network/interfaces
echo "allow-hotplug can0" >> /etc/network/interfaces
echo "iface can0 can static" >> /etc/network/interfaces
echo "       bitrate 125000" >> /etc/network/interfaces
echo "       down /sbin/ip link set $IFACE down" >> /etc/network/interfaces
echo "       up /sbin/ip link set $IFACE up" >> /etc/network/interfaces
echo "# MagicJoy config stops ============="  >> /etc/network/interfaces

echo "Updating /etc/modules ..."
# ==============================================
cp /etc/modules /etc/modules.bak
echo "# MagicJoy config starts ============="  >> /etc/modules
echo "i2c-dev"  >> /etc/modules
echo "mcp251x"  >> /etc/modules
echo "can_dev"  >> /etc/modules
echo "# MagicJoy config stops ============="  >> /etc/modules

echo "running apt-update and installing required modules ..."
# ===========================================================
sudo apt-get update
sudo apt-get -y install can-utils build-essential python3-dev python3-smbus git python3-pip cmake
echo "running pip3 and installing required modules ..."
# ===========================================================
pip3 install wheel
pip3 install setuptools
pip3 -y install Adafruit-SSD1306 
pip3 -y install RPi.GPIO
pip3 -y install Adafruit-ADS1x15
pip3 -y install spidev

echo "Installing can2RNET python library"
python3 ./can2RNET/setup.py install

echo "Setup done"
echo ""
echo "Reboot your raspberry now."