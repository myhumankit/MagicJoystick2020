from flask_restful import Resource

lights = [False, False, False, False]
drive_mode = False #pas en mode drive au démarrage
battery_level = 7 #valeur d'init (fausse)
chair_speed = -1.0 #valeur d'init (fausse)
ir_response = -1

class CurrentValues(Resource):
    def __init__(self):
        pass
    
    def get(self, topic):
        global battery_level, chair_speed, drive_mode
        if topic == "time-battery":
            return {"BATTERY_LEVEL": battery_level}
        elif topic == "lights-speed-driveMode":
            print("get request", lights)
            return {"DRIVE_MODE": drive_mode, "CHAIR_SPEED" : chair_speed, "LIGHTS": lights}
        elif topic == "ir_response":
            return {"IR_RESPONSE": ir_response}


def update_current_values(msg):
    global battery_level, chair_speed, drive_mode, ir_response
    
    data_current = deserialize(msg.payload)
    if msg.topic == status_battery_level.TOPIC_NAME:
        battery_level = data_current.battery_level

    elif msg.topic == status_chair_speed.TOPIC_NAME:
        chair_speed = data_current.speedMps*3.6
    
    elif msg.topic == action_drive.TOPIC_NAME:
        drive_mode = deserialize(msg.payload).doDrive

    elif msg.topic == action_light.TOPIC_NAME:
        lid = data_current.light_id-1
        if lid == FRONT_LIGHTS :
            lights[lid] = not lights[lid] #light_ID begins at 1
            return

        if lid == WARNING_LIGHT :
            lights[FLASHING_LEFT] = False 
            lights[FLASHING_RIGHT] = False 
            lights[lid] = not lights[lid]
    
        elif lid < 2 and not lights[WARNING_LIGHT]: # Flashing (only if no Warn)
            lights[FLASHING_LEFT] = (not lights[FLASHING_LEFT]) and lid==FLASHING_LEFT
            lights[FLASHING_RIGHT] = (not lights[FLASHING_RIGHT]) and lid==FLASHING_RIGHT

    elif msg.topic == IR_response.TOPIC_NAME:
        ir_response = data_current.ir_response