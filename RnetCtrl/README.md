MHK: control wheelchair hack based on the can2RNET project 
================================================
- This hack exploit is part of "the Magic Joystick" project led by a french solidarity association: MyHumanKit - https://myhumankit.org/ 
- It occured during the Fabrikarium hackaton held in Mureaux, october 2019, with collaboration of MyHumanKit & ArianeGroup.
- Big Thanks to the 'can2RNET' creators (Stephen Chavez & Specter) and their contributors to have documented and shared their hack exploit !

Script serveur Rnet:

<code>

python3 RnetCtrl.py  --help

usage: RnetCtrl.py [-h] [--ip IP] [--port PORT] [--rnetaddr RNETADDR] [-d]
                   [-t]

optional arguments:

  -h, --help           show this help message and exit

  --ip IP              Define server IPv4 address to listen, default is
                       '0.0.0.0'

  --port PORT          Define server portto listen, default is 4141

  --rnetaddr RNETADDR  Define Rnet wheelchair JSM address, default is 02001100

  -d, --debug          Enable debug messages

  -t, --test           Test mode, do not connect to CAN bus

</code>


Script client Joystick:

<code>

python3 joyClient.py --help

usage: joyClient.py [-h] [--ip IP] [--port PORT] [--period PERIOD]
                    [--invert_x] [--invert_y] [--swap_xy] [-d] [-t]

optional arguments:

  -h, --help       show this help message and exit

  --ip IP          Define server IPv4 address to connect, default is 127.0.0.1

  --port PORT      Define server port to connect, default is 4141

  --period PERIOD  Period where X/Y values are updated from hardware in
                   seconds. Default = 0.01

  --invert_x       Invert sign of x axis if set, default is false

  --invert_y       Invert sign of y axis if set, default is false

  --swap_xy        swap x/y inputs

  -d, --debug      Enable debug messages

  -t, --test       Test mode, do not connect to R-NET server

</code>

