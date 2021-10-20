import RPi.GPIO as GPIO
from gpiozero import Button


GPIO_BUTTON1 = Button.GPIO23
GPIO_BUTTON2 = Button.GPIO26

def button1_event():
    pass 

def button2_event():
    pass 

button1 = Button(GPIO_BUTTON1)
button2 = Button(GPIO_BUTTON2)

button1.when_pressed = button1_event
button2.when_pressed = button2_event

