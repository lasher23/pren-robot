import base64
import datetime

import cv2
import requests
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

IMAGE_RESOLUTION_HEIGHT = 640
IMAGE_RESOLUTION_WIDTH = 640
url = "http://prenh22-naufdenb.el.eee.intern:443/detect"
detectionStrategy = "nocam"

class_type_mapping = {
    2: "PET",
    1: "Kronkorken",
    3: "Cigarette",
    4: "Valuable"
}


def image_to_binary(image_path):
    with open(image_path, 'rb') as image_file:
        binary_data = base64.b64encode(image_file.read())
    return binary_data.decode('utf-8')


class Detection:

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, IMAGE_RESOLUTION_WIDTH)
        self.cap.set(4, IMAGE_RESOLUTION_HEIGHT)
        self.image_names = ["IMG_7913.JPG", "IMG_7914.JPG", "IMG_7915.JPG", "IMG_7916.JPG", "IMG_7917.JPG"]
        self.images = []
        for name in self.image_names:
            self.images.append(image_to_binary("images/" + name))

    def detect(self):
        if detectionStrategy == "camera":
            _, img = self.cap.read()
            img = cv2.flip(img, 1)

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            retval, image = cv2.imencode('.jpg', rgb_img)
            tmp_file_path = "/tmp/image"
            cv2.imwrite(tmp_file_path, image)
            with open(tmp_file_path, "rb") as file:
                file.write(image)
                response = requests.post(url, files={"image": file}, data={"deltaX": 20, "deltaY": 20})
        else:
            image = "images/" + self.image_names.pop(0)
            with open(image, "rb") as file:
                response = requests.post(url, files={"image": file}, data={"deltaX": 20, "deltaY": 20})

        # send the POST request with the image file as the payload

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

            plt.savefig("/tmp/" + datetime.datetime.now().isoformat() + ".png")

            print(parsed)
            center_object = min(parsed,
                                key=lambda r: abs(r["box"][1] + r["box"][3]) / 2 + abs(r["box"][0] + r["box"][2]) / 2)
            type = class_type_mapping[center_object["class"]]
            x = (center_object["box"][1] + center_object["box"][3]) / 2
            y = (center_object["box"][0] + center_object["box"][2]) / 2
            return {"x": x, "y": y, "type": type}
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
