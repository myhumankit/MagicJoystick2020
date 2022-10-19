from base import MagicResource
from magick_joystick.Topics import *

max_speed_level = 1 #valeur par défaut à au power on

class Actions(MagicResource):
    def __init__(self):
        super().__init__()
        self.name = "Action"
        self.commands = {
            "light":         lambda data: action_light(data["light_id"]),
            "auto_light":    lambda data: action_auto_light(),
            "max_speed":     lambda data: action_max_speed(data["max_speed"]),
            "drive":         lambda data: action_drive(True),
            "horn":          lambda data: action_horn(),
            "actuator_ctrl": lambda data: action_actuator_ctrl(data["actuator_num"], data["direction"]),
            "poweroff":      lambda data: action_poweroff(),
            "poweron":       lambda data: action_poweron()
        }

    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.client.subscribe(action_max_speed.TOPIC_NAME)
            print("Connection successful to Action")
        else:
            print(f"Connection failed with code {rc}")
    
    def get(self, action):
        global max_speed_level
        if action == "max_speed":
            return {"MAX_SPEED": max_speed_level}

    def post(self, action):
        global max_speed_level

        if action == "max_speed":
            max_speed_level = request.get_json()["max_speed"]

        return super().post(action)