- Install Raspberry Pi OS (Legacy 64-bits) Lite, options:
    - Hostname: magickcontrol.local
    - Enable SSH, allow public key authentication only
    - Set user name: `mjoy` and password: `mjoy`
    - Configure wireless LAN
    - Set locale settings
- Boot Raspi board
- When booted log one first time using SSH key
- If everything is OK, run:
```
./setup.sh <RASPI_IP> <USER> <PWD>
```
