import threading
import numpy as np


class Motors:
    def __init__(self, serial):
        self.serial = serial

    def move_to(self, alpha, beta, gamma, callback):
        print("Starting move thread")
        threading.Thread(target=self.move_to_internal, args=(alpha, beta, gamma, callback)).start()

    def move_to_internal(self, alpha, beta, gamma, callback):
        try:
            print("Moving alpha")
            self.move_one_angle("a", alpha)
            print("Moving beta")
            self.move_one_angle("b", beta)
            print("Moving gamma")
            self.move_one_angle("c", gamma)
            callback()
        except Exception as e:
            print(e)

    def move_one_angle(self, code, angle):
        delta = np.rad2deg(angle[1]) - np.rad2deg(angle[0])
        command = "step m" + code + ".d" + ("R" if (delta < 0) else "L") + ".v" + str(
            np.rad2deg(angle[2]) / delta) + ".w" + str(np.abs(delta) * 100)
        self.serial.write(bytes(command, 'ascii'))
        print("Command is")
        print(command)
        result = self.serial.readline().decode().strip()
        print("result is:")
        print(result)


class MockMotors:

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        timer = threading.Timer(max(alpha[2], beta[2], gamma[2]) / 1000, callback)
        timer.start()
