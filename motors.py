import threading
import numpy as np


class Motors:
    def __init__(self, serial):
        self.serial = serial

    def move_to(self, alpha, beta, gamma, callback, init=False):
        print("Starting move thread")
        threading.Thread(target=self.move_to_internal, args=(alpha, beta, gamma, callback, init)).start()

    def move_to_internal(self, alpha, beta, gamma, callback, init):
        try:
            print("Moving alpha")
            self.move_one_angle("A", alpha, init)
            print("Moving beta")
            self.move_one_angle("B", beta, init)
            print("Moving gamma")
            self.move_one_angle("C", gamma, init)
            callback()
        except Exception as e:
            print(e)

    def move_one_angle(self, code, angle, init):
        delta = np.rad2deg(angle[1]) - np.rad2deg(angle[0])
        speed = int(np.round(np.abs(np.rad2deg(angle[2]) / delta)))
        speed = 5
        rightCode = "R" if code == "A" else "U"
        leftCode = "L" if code == "A" else "D"
        command = "step m" + code + ".d" + (rightCode if (delta < 0) else leftCode) + ".v" + str(
            speed) + ".w" + str(
            int(np.round(np.abs(delta) * 100))) + ".cE\n"
        print("Command is")
        print(command)
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result or (init and "move failed" in result):
                print("result is:")
                print(result)
                break
            else:
                print("Not Result:")
                print(result)


class MockMotors:

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        timer = threading.Timer(max(alpha[2], beta[2], gamma[2]) / 1000, callback)
        timer.start()
