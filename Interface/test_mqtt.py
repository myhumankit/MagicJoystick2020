import paho.mqtt.client as mqtt
        
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection successful")
        client.subscribe("rnet/light")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"{msg.topic} {msg.payload}")

client = mqtt.Client() 
client.on_connect = on_connect 
client.on_message = on_message
client.connect("localhost", 1883, 60) 
client.loop_forever()
