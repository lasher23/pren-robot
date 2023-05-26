import threading
import serial
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
        delta = angle[1] - angle[0]
        self.serial.write(code + "." + np.abs(delta) + "." + angle[2] / delta + "." + delta < 0)
        result = self.serial.readline().decode().strip()
        print(result)


class MockMotors:
    def __init__(self):

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        timer = threading.Timer(max(alpha[2], beta[2], gamma[2]) / 1000, callback)
        timer.start()
