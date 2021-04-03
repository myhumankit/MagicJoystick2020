import construct as cs
import struct
import binascii

# =============================================================
# Define each known frames here :


"""
FRAME_TYPE are known values for header_t.type
    NAME :(type, subtype)
    Note: subtype NULL as depends on device ID
    sepecific for each JMS/MOTOR
"""
TYPE = 0
SUBTYPE = 1

RNET_FRAME_TYPE={
    'CONNECT'       : (0x0000, 0x000C),
    'SERIAL'        : (0x0000, 0x000E),
    'END_OF_INIT'   : (0x0000, 0x0060), # Processed as 0x006x with x masked to '0'
    'JOY_POSITION'  : (0x0200, 0x0000),
    'HEARTBEAT'     : (0x03c3, 0x0F0F),
    'MAX_SPEED'     : (0x0A04, 0x0000),
    'PMTX_CONNECT'  : (0x0C28, 0x0000),
    'PMTX_HEATBEAT' : (0x0C14, 0x0000),
    'BATTERY_LEVEL' : (0x1C0C, 0x0000),
}

RNET_FRAME_TYPE_R = RNET_FRAME_TYPE.__class__(map(reversed, RNET_FRAME_TYPE.items()))


def getFrameType(rawFrame):
        raw = raw_frame()
        raw.set_raw_frame(rawFrame)
        frameType = raw.header.type & 0x3FFF
        frameSubtype = raw.header.subtype

        # Case where type is null ('short' headers):
        if frameType == 0:
            try:
                frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype)]
            except:
                # Exception for End of Init, mask subtype 4 LSbits:
                try:
                    frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype & 0xFFFF0)]
                    frameSubtype = frameSubtype & 0xFFFF0
                except:
                    frameName = None
        # Long header case:
        else:
            try:
                frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype)]
            except:
                try:
                    frameName = RNET_FRAME_TYPE_R[(frameType, 0)]
                except:
                    frameName = None

        return frameType, frameSubtype, frameName



# =============================================================
# rnet messages definition

# --------------------------
# Connect message
# --------------------------
class rnet_connect :
    
    def __init__(self): 
        self.type = 0x0000
        self.subtype = RNET_FRAME_TYPE['CONNECT'][SUBTYPE]


    def encode(self):
        frame = raw_frame(False, False, self.type, self.subtype)
        frame.set_data(None)
        return frame.get_raw_frame()


# --------------------------
# Heartbeat message
# --------------------------
class rnet_heartbeat :
    
    def __init__(self): 
        self.type = RNET_FRAME_TYPE['HEARTBEAT'][TYPE]
        self.subtype = 0x0F0F


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)
        frame.set_data(b'\x87\x87\x87\x87\x87\x87\x87')
        return frame.get_raw_frame()


# --------------------------
# periodic serial message
# --------------------------
class rnet_serial:

    serial_t = cs.Struct(
        "serial" / cs.Bytes(8)
    )

    def __init__(self, serialNum=b'\x00\x00\x00\x00\x00\x00\x00\x00'): 
        self.type = 0x0000 
        self.subtype = RNET_FRAME_TYPE['SERIAL'][SUBTYPE]
        self.serialNum = serialNum


    def encode(self):
        frame = raw_frame(False, False, self.type, self.subtype)
        frame.set_data(self.serialNum)
        return frame.get_raw_frame()


# --------------------------
# set motor max speed message
# --------------------------
class rnet_motorMaxSpeed:

    maxSpeed_t = cs.Struct(
        "maxSpeed" / cs.Int8ub,
    )

    def __init__(self, maxSpeed, subtype): 
        self.type = RNET_FRAME_TYPE['MAX_SPEED'][TYPE]
        self.subtype = subtype
        self.set_data(maxSpeed)


    def set_data(self, maxSpeed):
        # Consider max speed > 100 is a bug, 
        # force it to minimum
        if maxSpeed > 100:
            maxSpeed = 0
        
        self.maxSpeed = maxSpeed


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)
        
        data = self.maxSpeed_t.build(
            dict(
                maxSpeed = self.maxSpeed)
        )

        frame.set_data(data)

        return frame.get_raw_frame()


# --------------------------
# set Joystick position message
# --------------------------
class rnet_joyPosition :

    joyPosition_t = cs.Struct(
        "X" / cs.Int8ub,
        "Y" / cs.Int8ub,
    )
    
    def __init__(self, x=0, y=0, jsm_id=0): 
        self.X = x
        self.Y = y
        self.type = RNET_FRAME_TYPE['JOY_POSITION'][TYPE]
        self.subtype = jsm_id


    def set_data(self, x=0, y=0):
        self.X = x
        self.Y = y


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)

        data = self.joyPosition_t.build(
            dict(
                X = self.X, 
                Y=self.Y)
        )

        frame.set_data(data)
        return frame.get_raw_frame()


# --------------------------
# get battery level
# --------------------------
class rnet_batteryLevel :

    batteryLevel_t = cs.Struct(
        "level" / cs.Int8ub,
    )
    
    def __init__(self, level=0): 
        self.level = 0
        self.type = RNET_FRAME_TYPE['BATTERY_LEVEL'][TYPE]
        self.subtype = 0


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)

        data = self.batteryLevel_t.build(
            dict(level = self.level)
        )

        frame.set_data(data)
        return frame.get_raw_frame()


    def set_raw(self, rawFrame):
        self.raw = raw_frame(False, False, self.type, self.subtype)
        self.raw.set_raw_frame(rawFrame)


    def decode(self):
        level = self.batteryLevel_t.parse(self.raw.get_data(1))
        return level.level



# --------------------------
# End of init
# This is a supposed end of
# init frame ...
# => all frames with 0006x from 
# JSM or Motor used to match the end of init
# --------------------------
class rnet_endOfInit :

    endOfInit_t = cs.Struct(
        "data" / cs.Int32ub,
    )
    
    def __init__(self, level=0): 
        self.level = 0
        self.type = RNET_FRAME_TYPE['END_OF_INIT'][TYPE]
        self.subtype = 0


    def set_raw(self, rawFrame):
        self.raw = raw_frame(False, False, self.type, self.subtype)
        self.raw.set_raw_frame(rawFrame)


    def decode(self):
        data = self.endOfInit_t.parse(self.raw.get_data(1))
        return data.data



# --------------------------
# PMTx Connect
# --------------------------
class rnet_pmTxConnect :

    pmTxConnect_t = cs.Struct(
        "data" / cs.Int8ub,
    )
    
    def __init__(self, level=0): 
        self.level = 0
        self.type = RNET_FRAME_TYPE['PMTX_CONNECT'][TYPE]
        self.subtype = 0


    def set_raw(self, rawFrame):
        self.raw = raw_frame(False, False, self.type, self.subtype)
        self.raw.set_raw_frame(rawFrame)


    def decode(self):
        data = self.pmTxConnect_t.parse(self.raw.get_data(1))
        return data.data



# --------------------------
# PMTx Heartbeat
# --------------------------
class rnet_pmTxHeartbeat :

    rnet_pmTxHeartbeat_t = cs.Struct(
        "data" / cs.Int8ub,
    )
    
    def __init__(self, level=0): 
        self.level = 0
        self.type = RNET_FRAME_TYPE['PMTX_HEARTBEAT'][TYPE]
        self.subtype = 0


    def set_raw(self, rawFrame):
        self.raw = raw_frame(False, False, self.type, self.subtype)
        self.raw.set_raw_frame(rawFrame)


    def decode(self):
        data = self.rnet_pmTxHeartbeat_t.parse(self.raw.get_data(1))
        return data.data




# =============================================================
# DO NOT MODIFY
# =============================================================
# RNET raw frame and header definition :
#  
# raw_s has to be decoded from the raw data recieved from 
# can socket, then header can be decoded from raw_s.type

class raw_frame:
    header_t = cs.Struct(

        "subtype" / cs.Int16ul,
        "type" / cs.Int16ul,
    )


    """
    CAN bus raw frame
    """
    raw_t = cs.Struct(
        "type" / cs.Int32ub,
        "length" / cs.Int32ul,
        "value" / cs.Bytes(8),
    )

    def __init__(self, Idl=False, Rtr=False, Type=0x0000, Subtype = 0x0000):
        IDL = 0
        RTR = 0
        if Idl:
            IDL = 0x8000
        if Rtr:
            RTR = 0x4000
        self.header = self.header_t.build(
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

        self.raw_frame = self.raw_t.build(
            dict(
                type = struct.unpack(">L", self.header)[0],
                length = data_length,
                value = data,   
            )
        )

    def get_data(self, length):
        return self.raw_frame_s.value[:length]


    def get_raw_frame(self):
        return self.raw_frame


    def set_raw_frame(self, rawFrame):
        self.raw_frame_s = self.raw_t.parse(rawFrame)
        self.header = self.header_t.parse(rawFrame[:4])



# TEST functions 
if __name__ == "__main__":

    connect = rnet_connect()
    print('rnet_connect: %r' %binascii.hexlify(connect.encode()))

    heartbeat = rnet_heartbeat()
    print('rnet_heartbeat: %r' %binascii.hexlify(heartbeat.encode()))

    serial = rnet_serial(b'\x01\x02\x03\x04\x05\x06\x07\x08')
    print('rnet_serial: %r' %binascii.hexlify(serial.encode()))

    speed = rnet_motorMaxSpeed(100, 0x1100)
    print('rnet_motorMaxSpeed: %r' %binascii.hexlify(speed.encode()))
    # Max speed bug test
    speed = rnet_motorMaxSpeed(255555, 0x1100)
    print('rnet_motorMaxSpeed: %r' %binascii.hexlify(speed.encode()))

    pos =  rnet_joyPosition(255,254,0x1100)
    print('rnet_joyPosition: %r' %binascii.hexlify(pos.encode()))

    vbat = rnet_batteryLevel()
    vbat.set_raw(binascii.unhexlify('00000c9c010000006300000000000000'))
    level = vbat.decode()
    print('battery level: %d' %level)


    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0000288c010000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0000148c010000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))
    
    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('60000000040000001100000200000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0f0fc383070000008787878787878700'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))
    
    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('00000c9c010000006300000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0011008202000000fffe000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0011048a010000006400000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('0c000000000000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName = getFrameType(binascii.unhexlify('ADDEEFBE00000000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))
