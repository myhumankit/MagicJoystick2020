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
    'HORN'          : (0x0C04, 0x0000),
    'PLAY_TONE'     : (0x181c, 0x0D00),
    'ACTUATOR_CTRL' : (0x0808, 0x0000),
}

RNET_FRAME_TYPE_R = RNET_FRAME_TYPE.__class__(map(reversed, RNET_FRAME_TYPE.items()))


def getFrameType(rawFrame):
        raw = raw_frame()
        raw.set_raw_frame(rawFrame)

        idl = raw.header.type & 0x8000
        rtr = raw.header.type & 0x4000

        frameType = raw.header.type & 0x3FFF
        frameSubtype = raw.header.subtype
        allData  =raw.get_data(8)

        # Case where type is null ('short' headers):
        if frameType == 0:
            try:
                frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype)]
            except:
                # Exception for End of Init, mask subtype 4 LSbits:
                try:
                    frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype & 0xFFF0)]
                    frameSubtype = frameSubtype & 0xFFF0
                except:
                    frameName = 'Unknown'
        # Long header case:
        else:
            try:
                frameName = RNET_FRAME_TYPE_R[(frameType, frameSubtype)]
            except:
                try:
                    frameName = RNET_FRAME_TYPE_R[(frameType, 0)]
                except:
                    frameName = 'Unknown'

        return frameType, frameSubtype, frameName, allData, idl, rtr



def printFrame(rawFrame):

    frameType, frameSubtype, frameName, allData, idl, rtr = getFrameType(rawFrame)
    if idl:
        idl = True
    else:
        idl = False
    if rtr:
        rtr = True
    else:
        rtr = False

    data = binascii.hexlify(allData)
    return "[%s]\t\t0x%x\t-\t0x%x\t\tDATA: %s - RAW: %s (idl=%r, rtr=%r)" % (frameName, frameType, frameSubtype, data, binascii.hexlify(rawFrame), idl, rtr)



# =============================================================
# rnet messages definition

# --------------------------
# Connect message
# --------------------------
class RnetConnect :
    
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
class RnetHeartbeat :
    
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
class RnetSerial:

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
class RnetMotorMaxSpeed:

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
        if (maxSpeed > 100) or (maxSpeed < 0):
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
# Actuator Control
# Controls the different wheelchair actuators
# Input: 
#   - Actuator number : 0x00..0x7F
#   - Direction       : 0 / 1
#   - Subtype_ID      : Depends on the wheelchair config
# --------------------------
class RnetActuatorCtrl :

    Actuator_t = cs.Struct(
        "ctrl" / cs.Int8ub
    )
    
    def __init__(self, act_number=0, direction = 0, subtype=0): 
        
        # Manage error case:
        self.set_data(act_number, direction)        
        self.type = RNET_FRAME_TYPE['ACTUATOR_CTRL'][TYPE]
        self.subtype = subtype


    def set_data(self, act_number=0, direction=0):
        if act_number > 0x7F:
            self.act_number = 0
        else:
            self.act_number = act_number

        if direction not in [0,1]:
            self.act_number = 0
        else:
            self.direction = direction


    def get_data(self):
        return self.act_number,self.direction


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)
        print("actuator: %r, %r" %(self.act_number, self.direction))
        data = self.Actuator_t.build(
            dict(
                ctrl = self.act_number + (self.direction<<7))
        )

        frame.set_data(data)
        return frame.get_raw_frame()


# --------------------------
# set Joystick position message
# --------------------------
class RnetJoyPosition :

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

    def get_data(self):
        return self.X,self.Y

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
# control Horn
#
# First send '0' to motor every 100ms, then send '1'to stop.
# JSM -   [HORN]		0xc04	-	0x100		DATA: b'0000000000000000'
# MOTOR - [HORN]		0xc04	-	0x401		DATA: b'0000000000000000'
# JSM -   [HORN]		0xc04	-	0x100		DATA: b'0000000000000000'
# MOTOR - [HORN]		0xc04	-	0x401		DATA: b'0000000000000000'
# ...
# JSM -   [HORN]		0xc04	-	0x100		DATA: b'0000000000000000'
# JSM -   [HORN]		0xc04	-	0x101		DATA: b'0000000000000000' 
# --------------------------
class RnetHorn :

    def __init__(self, jsm_id=0): 
        self.state = 0
        self.type = RNET_FRAME_TYPE['HORN'][TYPE]
        self.subtype = 0x100 # ?? Seens not to be JSM ID...

    def toogle_state(self):
        if self.state == 0:
            self.state = 1
        else:
            self.state = 0

    def get_state(self):
        return self.state


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype + self.state)
        frame.set_data(None)
        return frame.get_raw_frame()


# --------------------------
# control PlayTone
# --------------------------
class RnetPlayTone :

    tone_t = cs.Struct(
        "tone0_length" / cs.Int8ub,
        "tone0_note" / cs.Int8ub,
        "tone1_length" / cs.Int8ub,
        "tone1_note" / cs.Int8ub,
        "tone2_length" / cs.Int8ub,
        "tone2_note" / cs.Int8ub,
        "tone3_length" / cs.Int8ub,
        "tone3_note" / cs.Int8ub
    )

    def __init__(self): 
        self.type = RNET_FRAME_TYPE['PLAY_TONE'][TYPE]
        self.subtype = RNET_FRAME_TYPE['PLAY_TONE'][SUBTYPE]


    def encode(self):
        frame = raw_frame(True, False, self.type, self.subtype)
        data = self.tone_t.build(
            dict(
            tone0_length = 10,
            tone0_note   = 70,
            tone1_length = 10,
            tone1_note   = 80,
            tone2_length = 10,
            tone2_note   = 90,
            tone3_length = 10,
            tone3_note   = 100)
        )

        frame.set_data(data)
        return frame.get_raw_frame()


# --------------------------
# get battery level
# --------------------------
class RnetBatteryLevel :

    batteryLevel_t = cs.Struct(
        "level" / cs.Int8ub,
    )
    
    def __init__(self, level=0): 
        self.level = 0
        self.raw = None
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
        if self.raw is not None:
            level = self.batteryLevel_t.parse(self.raw.get_data(1))
        return level.level



# --------------------------
# End of init
# This is a supposed end of
# init frame ...
# => all frames with 0006x from 
# JSM or Motor used to match the end of init
# --------------------------
class RnetEndOfInit :

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
class RnetPmTxConnect :

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
class RnetPmTxHeartbeat :

    RnetPmTxHeartbeat_t = cs.Struct(
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
        data = self.RnetPmTxHeartbeat_t.parse(self.raw.get_data(1))
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

    connect = RnetConnect()
    print('RnetConnect: %r' %binascii.hexlify(connect.encode()))

    heartbeat = RnetHeartbeat()
    print('RnetHeartbeat: %r' %binascii.hexlify(heartbeat.encode()))

    serial = RnetSerial(b'\x01\x02\x03\x04\x05\x06\x07\x08')
    print('RnetSerial: %r' %binascii.hexlify(serial.encode()))

    speed = RnetMotorMaxSpeed(100, 0x1100)
    print('RnetMotorMaxSpeed: %r' %binascii.hexlify(speed.encode()))
    # Max speed bug test
    speed = RnetMotorMaxSpeed(255555, 0x1100)
    print('RnetMotorMaxSpeed: %r' %binascii.hexlify(speed.encode()))

    pos =  RnetJoyPosition(255,254,0x1100)
    print('RnetJoyPosition: %r' %binascii.hexlify(pos.encode()))

    vbat = RnetBatteryLevel()
    vbat.set_raw(binascii.unhexlify('00000c9c010000006300000000000000'))
    level = vbat.decode()
    print('battery level: %d' %level)


    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('0000288c010000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('0000148c010000000000000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))
    
    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('60000000040000001100000200000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('0f0fc383070000008787878787878700'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))
    
    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('00000c9c010000006300000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('0011008202000000fffe000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r' %(frameType, frameSubtype, frameName))

    frameType, frameSubtype, frameName, _ = getFrameType(binascii.unhexlify('0011048a010000006400000000000000'))
    print('Frame type: 0x%x, subtype: 0x%x, Frame name: %r\n' %(frameType, frameSubtype, frameName))

    printFrame(binascii.unhexlify('0c000000000000000000000000000000'))
    printFrame(binascii.unhexlify('ADDEEFBE00000000000000000000000000'))
    printFrame(binascii.unhexlify('0000288c010000000000000000000000'))
    printFrame(binascii.unhexlify('0000148c010000000000000000000000'))
    printFrame(binascii.unhexlify('60000000040000001100000200000000'))
    printFrame(binascii.unhexlify('0f0fc383070000008787878787878700'))
    printFrame(binascii.unhexlify('00000c9c010000006300000000000000'))
    printFrame(binascii.unhexlify('0011008202000000fffe000000000000'))
    printFrame(binascii.unhexlify('0011048a010000006400000000000000'))
    printFrame(binascii.unhexlify('0c000000000000000000000000000000'))

