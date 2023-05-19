import base64

import cv2

IMAGE_RESOLUTION_HEIGHT = 640
IMAGE_RESOLUTION_WIDTH = 640


class Detection:

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, IMAGE_RESOLUTION_WIDTH)
        self.cap.set(4, IMAGE_RESOLUTION_HEIGHT)

    def detect(self):
        _, img = self.cap.read()
        img = cv2.flip(img, 1)

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        retval, buffer = cv2.imencode('.jpg', rgb_img)
        jpg_as_text = base64.b64encode(buffer)
        # TODO REST Call
        return {"x": 320, "y": 320}
