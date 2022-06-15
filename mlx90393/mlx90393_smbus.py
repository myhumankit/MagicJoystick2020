# Distributed with a free-will license.
# Use it any way you want, profit or free, provided it fits in the licenses of its associated works.
# MLX90393
# This code is designed to work with the MLX90393_I2CS I2C Mini Module available from ControlEverything.com.
# https://www.controleverything.com/products
import smbus
import time
import struct

# Get I2C bus
bus = smbus.SMBus(1)
# MLX90393 address, 0x0C(12)
# Select write register command, 0x60(96)
# REG = 0x00
# AH = 0x00, AL = 0x5C ( GAIN_SEL = 0x50 | HALFCONF = 0x0C) , REG = 0x00 << 2 
config = [0x00, 0x5C, 0x00]
bus.write_i2c_block_data(0x0C, 0x60, config)
# Read data back, 1 byte
# Status byte
data = bus.read_byte(0x0C)

# MLX90393 address, 0x0C(12)
# Select write register command, 0x60(96)
# REG = 0x02
# AH = (OSR2[1:0] << 3) | (RES_Z[1:0] << 1) | (RES_Y[1])
# AH =  ( 0 0 ) ( 1 1 ) ( 1 ) = 0x07
  
# AL = (RES_Y[0] << 7) | (RES_X[1:0] << 5) | (DIG_FILT[3:0] << 2) | (OSR[1:0])
# AL = ( 1 ) ( 1 1 ) ( 1 0 1 ) ( 0 0 ) =  0xFC 

config = [0x07, 0xF4, 0x08]
bus.write_i2c_block_data(0x0C, 0x60, config)
# Read data back, 1 byte
# Status byte
data = bus.read_byte(0x0C)






while True:
  # MLX90393 address, 0x0C(12)
  # Start single meaurement mode, X, Y, Z-Axis enabled
  bus.write_byte(0x0C, 0x3E)
  # Read data back, 1 byte
  # Status byte
  data = bus.read_byte(0x0C)
  time.sleep(0.5)
  # MLX90393 address, 0x0C(12)
  # Read data back from 0x4E(78), 7 bytes
  # Status, xMag msb, xMag lsb, yMag msb, yMag lsb, zMag msb, zMag lsb
  data = bus.read_i2c_block_data(0x0C, 0x4E, 7)
  
  # Convert the data
  
  (xMag,) = struct.unpack(">H", bytearray(data[1:3]))
  (yMag,) = struct.unpack(">H", bytearray(data[3:5]))
  (zMag,) = struct.unpack(">H", bytearray(data[5:7]))
  xMag -= 0x4000
  yMag -= 0x4000
  zMag -= 0x4000
  # Output data to screen
  #print ("Magnetic Field in X-Axis : %d" %xMag)
  #print ("Magnetic Field in Y-Axis : %d" %yMag)
  #print ("Magnetic Field in Z-Axis : %d" %zMag)

  print(' {: 8} | {: 8} | {: 8}'.format(xMag,yMag,zMag), end='\r')

  time.sleep(0.5)

