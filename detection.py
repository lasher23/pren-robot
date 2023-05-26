import base64

import cv2
import requests
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

IMAGE_RESOLUTION_HEIGHT = 640
IMAGE_RESOLUTION_WIDTH = 640
url = "http://prenh22-naufdenb.el.eee.intern:443/detect"


class Detection:

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, IMAGE_RESOLUTION_WIDTH)
        self.cap.set(4, IMAGE_RESOLUTION_HEIGHT)

    def detect(self):
        _, img = self.cap.read()
        img = cv2.flip(img, 1)

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        retval, image = cv2.imencode('.jpg', rgb_img)
        # TODO REST Call
        files = {"image": image}

        # Send the POST request with the image file as the payload
        response = requests.post(url, files=files)

        # Check the response status code
        if response.status_code == 200:
            parsed = response.json()

            im = Image.open(image)

            # Display the image
            plt.imshow(im)

            # Get the current reference
            ax = plt.gca()
            ax.invert_yaxis()

            for detection in parsed:
                print(detection)

                x = detection["box"][0]
                y = detection["box"][1]
                width = abs(x - detection["box"][2])
                height = abs(detection["box"][1] - detection["box"][3])

                # Create a Rectangle patch
                rect = Rectangle((y, x), height, width, linewidth=1, edgecolor="r", facecolor="none")
                ax.add_patch(rect)

            plt.show()

            print(parsed)
        else:
            print("Failed to upload image. Status code:", response.status_code)
        return {"x": 320, "y": 320}


class MockDetection:

    def __init__(self, mock_responses):
        self.mock_responses = mock_responses

    def detect(self):
        if len(self.mock_responses) == 0:
            return None
        return self.mock_responses.pop(0)
