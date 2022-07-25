# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

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


t = time.time()
cnt = 0
offset_X = 0
offset_Y = 0
offset_Z = 0

print("Computing sensor offset:", end='', flush=True)

while True:
    if time.time() - t > 5:
      break
          
    MX, MY, MZ = SENSOR.magnetic

    offset_X += MX
    offset_Y += MY
    offset_Z += MZ
    cnt += 1
    print(".", end='', flush=True)
    time.sleep(0.5)


offset_X/= cnt
offset_Y/= cnt
offset_Z/= cnt
print("Done...")


print("Sensing...")
while True:
    MX, MY, MZ = SENSOR.magnetic

    MX-=offset_X
    MY-=offset_Y
    MZ-=offset_Z

    print("{:+10.3f} | {:+10.3f} | {:+10.3f}".format(MX, MY, MZ), end='\r')
    # Display the status field if an error occured, etc.
    if SENSOR.last_status > adafruit_mlx90393.STATUS_OK:
        SENSOR.display_status()
    time.sleep(0.5)
