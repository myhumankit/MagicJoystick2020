import construct as cs
import struct
import binascii

# =============================================================
# Define each known frames here :


"""
FRAME_TYPE are known values for header_s.type
"""
RNET_FRAME_TYPE={
    'CONNECT'       : 0x000C,
    'SERIAL'        : 0x000E,
    'JOY_POSITION'  : 0x0200,
    'MAX_SPEED'     : 0x0A04,
    'HEARTBEAT'     : 0x03c3,
}


# =============================================================
# rnet messages definition

# --------------------------
# Connect message
# --------------------------
class rnet_connect :
    
    def __init__(self): 
        self.subtype = RNET_FRAME_TYPE['CONNECT']
        self.type = 0x0000


    def encode(self):
        frame = raw_frame(False, False, self.type, self.subtype)
        frame.set_data(None)
        return frame.get_raw_frame()


# --------------------------
# Heartbeat message
# --------------------------
class rnet_heartbeat :
    
    def __init__(self): 
        self.type = RNET_FRAME_TYPE['HEARTBEAT']
        self.subtype = 0x0F0F


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)
        frame.set_data(b'\x87\x87\x87\x87\x87\x87\x87')
        return frame.get_raw_frame()


# --------------------------
# periodic serial message
# --------------------------
class rnet_serial:

    serial_s = cs.Struct(
        "serial" / cs.Bytes(8)
    )

    def __init__(self, serialNum=b'\x00\x00\x00\x00\x00\x00\x00\x00'): 
        self.type = 0x0000 
        self.subtype = RNET_FRAME_TYPE['SERIAL']
        self.serialNum = serialNum


    def encode(self):
        frame = raw_frame(False, False, self.type, self.subtype)
        frame.set_data(self.serialNum)
        return frame.get_raw_frame()


# --------------------------
# set motor max speed message
# --------------------------
class rnet_motorMaxSpeed:

    maxSpeed_s = cs.Struct(
        "maxSpeed" / cs.Int8ub,
    )

    def __init__(self, maxSpeed, subtype): 
        self.subtype = subtype
        self.set_data(maxSpeed)


    def set_data(self, maxSpeed):
        # Consider max speed > 100 is a bug, 
        # force it to minimum
        if maxSpeed > 100:
            maxSpeed = 0
        
        self.maxSpeed = maxSpeed


    def encode(self):
        frame = raw_frame(True, False, RNET_FRAME_TYPE['MAX_SPEED'], self.subtype)
        
        data = self.maxSpeed_s.build(
            dict(
                maxSpeed = self.maxSpeed)
        )

        frame.set_data(data)

        return frame.get_raw_frame()


# --------------------------
# set Joystick position message
# --------------------------
class rnet_joyPosition :

    joyPosition_s = cs.Struct(
        "X" / cs.Int8ub,
        "Y" / cs.Int8ub,
    )
    
    def __init__(self, x=0, y=0, jsm_id=0): 
        self.X = x
        self.Y = y
        self.subtype = jsm_id
        self.type = RNET_FRAME_TYPE['JOY_POSITION']


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)

        data = self.joyPosition_s.build(
            dict(
                X = self.X, 
                Y=self.Y)
        )

        frame.set_data(data)
        return frame.get_raw_frame()




# =============================================================
# DO NOT MODIFY
# =============================================================
# RNET raw frame and header definition :
#  
# raw_s has to be decoded from the raw data recieved from 
# can socket, then header can be decoded from raw_s.type

class raw_frame:
    header_s = cs.Struct(

        "subtype" / cs.Int16ul,
        "type" / cs.Int16ul,
    )


    """
    CAN bus raw frame
    """
    raw_s = cs.Struct(
        "type" / cs.Int32ub,
        "length" / cs.Int32ul,
        "value" / cs.Bytes(8),
    )

    def __init__(self, Idl, Rtr, Type, Subtype = 0x0000):
        IDL = 0
        RTR = 0
        if Idl:
            IDL = 0x8000
        if Rtr:
            RTR = 0x4000
        self.header = self.header_s.build(
            dict( 
                type = Type | IDL | RTR,
                subtype = Subtype
                )
        )


    def set_data(self, data):

        # Zero padding of data
        if data == None:
            data_length = 0
            data = b'\00'*8
        else:
            data_length = len(data)
            if data_length < 8:
                data = data + b'\00'*(8-data_length)

        self.raw_frame = self.raw_s.build(
            dict(
                type = struct.unpack(">L", self.header)[0],
                length = data_length,
                value = data,   
            )
        )

    def get_raw_frame(self):
        return self.raw_frame





# TEST functions 

connect = rnet_connect()
print(binascii.hexlify(connect.encode()))

heartbeat = rnet_heartbeat()
print(binascii.hexlify(heartbeat.encode()))

serial = rnet_serial(b'\x01\x02\x03\x04\x05\x06\x07\x08')
print(binascii.hexlify(serial.encode()))

speed = rnet_motorMaxSpeed(100, 0x1100)
print(binascii.hexlify(speed.encode()))

pos =  rnet_joyPosition(255,254,0x1100)
print(binascii.hexlify(pos.encode()))