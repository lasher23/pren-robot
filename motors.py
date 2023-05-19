import threading

import asyncio

import numpy as np


class Motors:

    def move_to(self, alpha, beta, gamma, callback):
        # TODO call robot
        print("TODO move_to")
        timer = threading.Timer(max(alpha[1], beta[1], gamma[1]) / 1000, callback)
        timer.start()
