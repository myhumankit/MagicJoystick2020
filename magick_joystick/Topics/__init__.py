import jsonpickle

def deserialize(arrray):
    return jsonpickle.decode(arrray)

# Base class for MQTT messages
class base_mqtt_message:
    def __init__(self):
        pass

    def serialize(self):
        """ returns json-string representation of this object """
        return jsonpickle.dumps(self)

# Data format for each topic
class joystick_state(base_mqtt_message):
    TOPIC_NAME = "joystick/state"
    def __init__(self, buttons=0, x=0, y=0, long_click=0):
        self.buttons = buttons  # 0: no button, 1: Left click, 2: Right click
        self.x = x
        self.y = y
        self.long_click = long_click    # 0: Short click, 1: lobg click

class action_actuator_ctrl(base_mqtt_message):
    # Publication shall be 2Hz periodic
    TOPIC_NAME = "action/actuator_ctrl"
    def __init__(self, actuator_num, direction):
        self.direction = direction
        self.actuator_num = actuator_num

class action_drive(base_mqtt_message):
    TOPIC_NAME = "action/drive"
    def __init__(self, doDrive):
        self.doDrive = doDrive

class action_max_speed(base_mqtt_message):
    TOPIC_NAME = "action/max_speed"
    def __init__(self, max_speed):
        self.max_speed = max_speed

class action_horn(base_mqtt_message):
    TOPIC_NAME = "action/horn"
    def __init__(self):
        pass

class action_poweroff(base_mqtt_message):
    TOPIC_NAME = "action/poweroff"
    def __init__(self):
        pass

class action_poweron(base_mqtt_message):
    TOPIC_NAME = "action/poweron"
    def __init__(self):
        pass

class action_light(base_mqtt_message):
    TOPIC_NAME = "action/light"
    def __init__(self, light_id): 
        # ID of the light (headlights, flashing left/right, warnning... )
        #No need of a enable/disable variable because the frames are the same to swich on/off
        self.light_id = light_id

class action_auto_light(base_mqtt_message):
    TOPIC_NAME = "action/auto_light"
    def __init__(self): 
       pass
    # def __init__(self, doAutoLight): #si publish de l'etat auto toutes les demi-secondes
    #    self.doAutoLight = doAutoLight

class status_battery_level(base_mqtt_message):
    TOPIC_NAME = "status/battery_level"
    def __init__(self, battery_level):
        self.battery_level = battery_level

class status_chair_speed(base_mqtt_message):
    TOPIC_NAME = "status/chair_speed"
    def __init__(self, speedMps):
        self.speedMps = speedMps


class TV_power(base_mqtt_message):
    TOPIC_NAME = "TV/power"
    def __init__(self):
        pass
        #self.state = state

class TV_mute(base_mqtt_message):
    TOPIC_NAME = "TV/mute"
    def __init__(self):
        pass

