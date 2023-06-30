import threading
import numpy as np


class Motors:
    def __init__(self, serial):
        self.serial = serial

    def move_to(self, alpha, beta, gamma, callback, order, init=False, ignore_check=False, speed=None, ):
        print("Starting move thread")
        threading.Thread(target=self.move_to_internal,
                         args=(alpha, beta, gamma, callback, init, ignore_check, speed, order)).start()

    def move_to_internal(self, alpha, beta, gamma, callback, init, ignore_check, speed, order):
        try:
            print("Moving in order " + str(order))
            for element in order:
                print("Moving " + element)
                self.move_one_angle(element, alpha if element == "A" else beta if element == "B" else gamma, init,
                                    ignore_check, speed=speed)
            # print("Moving alpha")
            # self.move_one_angle("A", alpha, init, ignore_check, speed=speed)
            # print("Moving beta")
            # self.move_one_angle("B", beta, init, ignore_check, speed=speed)
            # print("Moving gamma")
            # self.move_one_angle("C", gamma, init, ignore_check, beta, speed)
            callback()
        except Exception as e:
            print(e)

    def move_one_angle(self, code, angle, init, ignore_check, beta=None, speed=None):
        delta = np.rad2deg(angle[1]) - np.rad2deg(angle[0])
        if beta is not None and not init and not ignore_check:
            delta -= np.rad2deg(beta[1]) - np.rad2deg(beta[0])
        print("Delta: " + str(delta))
        if delta == 0:
            return
        if speed is None:
            speed = int(np.round(np.abs(np.rad2deg(angle[2]) / delta)))
            speed = 5
        right_code = "R" if code == "A" else "D" if code == "B" else "U"
        left_code = "L" if code == "A" else "U" if code == "B" else "D"
        check = "D" if ignore_check else "E"
        command = "step m" + code + ".d" + (right_code if (delta < 0) else left_code) + ".v" + str(
            speed) + ".w" + str(
            int(np.round(np.abs(delta) * 100))) + ".c" + check + "\n"
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
