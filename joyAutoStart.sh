# This script will add a startup script to /etc/contab
# so joy client nd Rnet serve will start at raspberry boot automatically
#
# THIS SCRIPT MUST BE RUN WITH: sudo joyAutoStart.sh
#
if [ "$EUID" -ne 0 ]
  then echo "Must run as root: 'sudo ./joyAutoStart.sh'"
  exit
fi


echo "Creating startup script ..."
# ==============================================
export CURPATH=$(pwd)

echo "python3 $CURPATH/RnetCtrl/RnetCtrl.py --ip 127.0.0.1 &" > $CURPATH/MagicJoy2020StartAll.sh
echo "sleep 3" >> $CURPATH/MagicJoy2020StartAll.sh
echo "python3 $CURPATH/RnetCtrl/joyClient.py" >> $CURPATH/MagicJoy2020StartAll.sh
chmod +x $CURPATH/MagicJoy2020StartAll.sh
chown $USER:$USER $CURPATH/MagicJoy2020StartAll.sh

echo "Updating crontab ..."
# ==============================================
cp /etc/crontab /etc/crontab.bak
echo "@reboot pi $CURPATH/MagicJoy2020StartAll.sh" >> /etc/crontab

echo "Done, MagicJoy2020 will automatically start on next boot"

