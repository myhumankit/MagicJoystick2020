# MLX90393 Sensor

## Pinout
This sensor is an I2C sensor. It's default I2C address is 0x0C

<pre>
MLX VCC -> RPI +3.3V  (pin 01)  
MLX SDA -> RPI SDA1   (pin 03)  
MLX SDL -> RPI SDL1   (pin 05)  
NC      -> NC         (pin 07)  
MLX GND -> RPI GND    (pin 09)  
</pre>

The I2C interface need to be enabled in the RPI config (using raspi-config)  
   
<br/>   

## Pyhton libraries

2 python libraries can be used to communicate with this sensor  
* the smbus library: smbus==1.1.post2
* The adafruit library: adafruit-circuitpython-mlx90393==2.0.12
  
<br/>

### SMBUS
This library is a low level library that allows to communicate using low level I2C bus commands.

```python
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
```


### Adafruit
This library is a higher level library that allows to interract with a SENSOR object, hiding the I2C communication.

```python

import time
import board
import adafruit_mlx90393

i2c = board.I2C()  # uses board.SCL and board.SDA
SENSOR = adafruit_mlx90393.MLX90393(i2c, gain=adafruit_mlx90393.GAIN_1X, filt = adafruit_mlx90393.FILTER_5, resolution= adafruit_mlx90393.RESOLUTION_19)

#SENSOR._debug=True

SENSOR.gain = adafruit_mlx90393.GAIN_5X
SENSOR.resolution_x= adafruit_mlx90393.RESOLUTION_19
SENSOR.resolution_y= adafruit_mlx90393.RESOLUTION_19
SENSOR.resolution_z= adafruit_mlx90393.RESOLUTION_19

```

