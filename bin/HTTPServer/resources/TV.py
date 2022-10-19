from base import MagicResource
from magick_joystick.Topics import *

class TV(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "TV"
        self.commands = {
            "power":      lambda data: TV_power(),
            "volume":     lambda data: TV_volume(data["type"]),
            "param":      lambda data: TV_param(data["type"]),
            "direction":  lambda data: TV_direction(data["type"]),
            "number":     lambda data: TV_number(data["nb"]),
        }