from flask_restful import Resource

lights = [False, False, False, False]
drive_mode = False #pas en mode drive au démarrage
battery_level = 7 #valeur d'init (fausse)
chair_speed = -1.0 #valeur d'init (fausse)

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
