import time

import numpy as np
import serial

print(str(np.arctan2(-45, -36)))

ser = serial.Serial('/dev/ttyACM0', 57600, timeout=10000)

ser.write(bytes("gpio mZ.sX\n", 'ascii'))
result = ser.readline().decode().strip()

time.sleep(10)

command = "gpio pV.sH\n"
ser.write(bytes(command, 'ascii'))
time.sleep(10)
command = "gpio pV.sL\n"
ser.write(bytes(command, 'ascii'))
