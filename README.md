MHK: control wheelchair hack based on the can2RNET project 
===========================================================
- This hack exploit is part of "the Magic Joystick" project led by a french solidarity association: MyHumanKit - https://myhumankit.org/ 
- It occured during the Fabrikarium hackaton held in Mureaux, october 2019, with collaboration of MyHumanKit & ArianeGroup.
- Big Thanks to the 'can2RNET' creators (Stephen Chavez & Specter) and their contributors to have documented and shared their hack exploit !

Please refer to :
https://wikilab.myhumankit.org/index.php?title=Projets:Magic_Joystick_2020 for a complete documentation of the project.


Software Installation:
======================

1- install git

2- get MagicJoystick2020 code

3- install all required software and configure raspberry system

<code>
sudo apt-get update

sudo apt-get install git

git clone https://github.com/myhumankit/MagicJoystick2020

cd MagicJoystick2020

sudo ./setup.sh
</code> 


Start MagicJoystick at boot time:
==================================

In order to automatically enable MagicJoystick at boot time (no screen, mouse or keyboard required), run the following script:

<code>
sudo ./joyAutoStart.sh
</code>

On next reboot the raspberry will automatically start Rnet, Joystick and display controllers.
