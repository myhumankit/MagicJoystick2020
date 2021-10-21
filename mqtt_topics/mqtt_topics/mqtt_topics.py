import pickle


def deserialize(arrray):
    return pickle.loads(arrray)


# Base class for MQTT messages
class base_mqtt_message:
    def __init__(self):
        pass

    """ returns byte array representation of this object """
    def serialize(self):
        # TODO : optimize serialization size
        return pickle.dumps(self)



# Data format for each topic
class joystick_state(base_mqtt_message):
    TOPIC_NAME = "joystick/state"
    def __init__(self, buttons=0, x=0, y=0, long_click=0):
        self.buttons = buttons  # 0: no button, 1: Left click, 2: Right click
        self.x = x
        self.y = y
        self.long_click = long_click    # 0: Short click, 1: lobg click

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
