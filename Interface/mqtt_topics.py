import pickle

# Base class for MQTT messages
class base_mqtt_message:
    def __init__(self):
        pass

    """ returns byte array representation of this object """
    def serialize(self):
        return pickle.dumps(self.__dict__)

# Data format for each topic
class joystick_state(base_mqtt_message):
    TOPIC_NAME = "joystick/state"
    def __init__(self, buttons, x, y, long_click):
        self.buttons = buttons
        self.x = x
        self.y = y
        self.long_click = long_click

class action_drive(base_mqtt_message):
    TOPIC_NAME = "action/drive"
    def __init__(self, on):
        self.on = on

class action_max_speed(base_mqtt_message):
    TOPIC_NAME = "action/max_speed"
    def __init__(self, max_speed):
        self.max_speed = max_speed

class action_horn(base_mqtt_message):
    TOPIC_NAME = "action/horn"
    def __init__(self):
        pass

class action_light(base_mqtt_message):
    TOPIC_NAME = "action/light"
    def __init__(self):
        pass
