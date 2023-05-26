import threading

try:
    import serial
except:
    print("Not on Raspi")
import numpy as np


class Motors:
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyACM0', 57600, timeout=1)

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        threading.Thread(target=self.move_to_internal, args=(alpha, beta, gamma, callback))

    def move_to_internal(self, alpha, beta, gamma, callback):
        self.move_one_angle("a", alpha)
        self.move_one_angle("b", beta)
        self.move_one_angle("c", gamma)
        callback()

    def move_one_angle(self, code, angle):
        delta = np.rad2deg(angle[1]) - np.rad2deg(angle[0])
        self.serial.write("step m" + code + ".d" + "R" if (delta < 0) else "L" + ".v" + np.rad2deg(
            angle[2]) / delta + ".w" + np.abs(delta) * 100)
        self.serial.write(
            code + "." + np.abs(delta) + "." + np.rad2deg(angle[2]) / delta + "." + "R" if (delta < 0) else "L")
        result = self.serial.readline().decode().strip()
        print(result)


class MockMotors:

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        timer = threading.Timer(max(alpha[2], beta[2], gamma[2]) / 1000, callback)
        timer.start()
