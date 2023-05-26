from datetime import datetime, timedelta
import sys
import sys
import time

import numpy as np

from detection import IMAGE_RESOLUTION_WIDTH, IMAGE_RESOLUTION_HEIGHT, MockDetection
from motors import Motors, MockMotors
from positions_calculation import calculate_new_angles_movement, add_angles
from web_api import post_move, start_run, post_object, stop_run

MOVEMENT_DURATION = 2000

MOVING = "MOVING"
NEW_SECTOR = "NEW_SECTOR"
DETECT_IMAGE = "DETECT_IMAGE"
ABOVE_ELEMENT = "ABOVE_ELEMENT"
AT_ELEMENT = "AT_ELEMENT"
DROP_ELEMENT = "DROP_ELEMENT"
CURRENT_SECTOR = "CURRENT_SECTOR"
STOP_ROBOT = "STOP_ROBOT"
STOPPED = "STOPPED"

CIGARETTES_DROP = {"x": 180, "y": 200, "z": 100}
PET_DROP = {"x": 90, "y": 200, "z": 100}
KRONKORKEN_DROP = {"x": -90, "y": 200, "z": 100}
VALUABLE_DROP = {"x": -180, "y": 200, "z": 100}


def calculate_target_coordinates_from_pixels(current_robot_position, on_camera_position_pixels, current_angles):
    pi_cam_alpha = np.deg2rad(20.5)
    pi_cam_beta = np.deg2rad(33)

    height_to_object = current_robot_position[
        "z"]  # todo measure height of object must be robot height + height of 0 to bottom

    total_view_x = height_to_object * np.tan(pi_cam_alpha / 2) * 2
    total_view_y = height_to_object * np.tan(pi_cam_beta / 2) * 2

    pixel_per_coordinate_x = IMAGE_RESOLUTION_WIDTH / total_view_x
    pixel_per_coordinate_y = IMAGE_RESOLUTION_HEIGHT / total_view_y

    alpha = current_angles["alpha"]

    pixel_from_middle_x = -IMAGE_RESOLUTION_WIDTH / 2 + on_camera_position_pixels["x"]
    pixel_from_middle_y = -IMAGE_RESOLUTION_HEIGHT / 2 + on_camera_position_pixels["y"]

    dummy_x = height_to_object * np.tan(pi_cam_alpha) * pixel_from_middle_x / 320
    dummy_y = height_to_object * np.tan(pi_cam_beta) * pixel_from_middle_y / 320

    distance = np.sqrt(dummy_x ** 2 + dummy_y ** 2)
    angle = np.arctan2(dummy_x, -dummy_y)

    total_angle = alpha + angle

    minus_delta_x = distance * np.sin(total_angle)
    minus_delta_y = distance * np.cos(total_angle)

    return {
        "x": current_robot_position["x"] - minus_delta_x,
        "y": current_robot_position["y"] - minus_delta_y,
        "z": current_robot_position["z"]
    }


class Robot:
    state = "INIT"
    # detection = Detection()
    motors = MockMotors()
    current_robot_position = None
    target_position = None
    current_angles = {"alpha": None, "beta": None, "gamma": None}
    moving_to_angles = {"alpha": None, "beta": None, "gamma": None}
    current_type = None
    detection = MockDetection([
        {"x": 400, "y": 200, "type": "PET"},
        None,
        {"x": 200, "y": 400, "type": "Kronkorken"},
        None,
        {"x": 100, "y": 0, "type": "Cigarette"},
        None,
        {"x": 320, "y": 320, "type": "Valuable"},
        None,
        {"x": 320, "y": 320, "type": "PET"},
        None,
        {"x": 320, "y": 320, "type": "Kronkorken"},
        None,
        {"x": 320, "y": 320, "type": "Cigarette"},
        None,
        {"x": 320, "y": 320, "type": "Valuable"},
        None,
    ])
    current_sector = None
    sectors = [
        {
            "position": {
                "x": 200,
                "y": 400,
                "z": 200
            }
        },
        {
            "position": {
                "x": 200,
                "y": 600,
                "z": 200
            }
        },
        {
            "position": {
                "x": 200,
                "y": 800,
                "z": 200
            }
        },
        {
            "position": {
                "x": -200,
                "y": 400,
                "z": 200
            }
        },
        {
            "position": {
                "x": -200,
                "y": 600,
                "z": 200
            }
        },
        {
            "position": {
                "x": -200,
                "y": 800,
                "z": 200
            }
        },
    ]

    def loop(self):
        self.start_time = datetime.now()
        while self.state != STOPPED:
            self.log_state()
            if datetime.now() - self.start_time >= timedelta(minutes=1):
                self.state = STOP_ROBOT
            # print("Current state: " + state)
            if self.state == "INIT":
                self.target_position = {"x": 0, "y": 400, "z": 200}
                self.current_robot_position = {"x": 0, "y": 585 * 2, "z": 0}
                self.current_angles = {"alpha": 0, "beta": 0, "gamma": 0}
                additional_angles = calculate_new_angles_movement(self.current_robot_position, self.target_position)
                self.moving_to_angles = add_angles(self.current_angles, additional_angles)
                print("Initialized Robot at Position: " + str(self.current_robot_position))
                post_move((self.current_angles["alpha"], self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                          (self.current_angles["beta"], self.moving_to_angles["beta"], MOVEMENT_DURATION),
                          (self.current_angles["gamma"], self.moving_to_angles["gamma"], MOVEMENT_DURATION))
                self.current_angles = self.moving_to_angles
                self.current_robot_position = self.target_position
                time.sleep(MOVEMENT_DURATION / 1000)
                self.state = NEW_SECTOR
                start_run()
                # TODO Stuff above is shit beautify
            elif self.state == NEW_SECTOR:
                if self.current_sector is None or self.current_sector >= len(self.sectors) - 1:
                    self.current_sector = -1
                self.current_sector = self.current_sector + 1
                self.move_to_coordinates(self.sectors[self.current_sector]["position"], self.detect_image)
                self.moving()
            elif self.state == CURRENT_SECTOR:
                self.move_to_coordinates(self.sectors[self.current_sector]["position"], self.detect_image)
                self.moving()
            elif self.state == DETECT_IMAGE:
                camera_pixel_position = self.detection.detect()
                if camera_pixel_position is None:
                    print("No Image Detected")
                    self.state = NEW_SECTOR
                    continue
                print("Detected Object at Position: " + str(camera_pixel_position))
                new_coordinates = calculate_target_coordinates_from_pixels(self.current_robot_position,
                                                                           camera_pixel_position,
                                                                           self.current_angles)
                self.move_to_coordinates(new_coordinates, self.above_element)
                self.moving()
            elif self.state == MOVING:
                time.sleep(0)
            elif self.state == ABOVE_ELEMENT:
                # TODO height sensor
                self.move_to_coordinates({**self.target_position, "z": 0}, self.at_element)
                self.moving()
            elif self.state == AT_ELEMENT:
                # todo grab element
                if self.current_type == "Kronkorken":
                    drop = KRONKORKEN_DROP
                elif self.current_type == "PET":
                    drop = KRONKORKEN_DROP
                elif self.current_type == "Cigarette":
                    drop = CIGARETTES_DROP
                else:
                    drop = VALUABLE_DROP

                self.move_to_coordinates(drop, self.drop_element)
                self.moving()
            elif self.state == DROP_ELEMENT:
                # TODO drop element
                post_object(self.current_type)
                self.state = CURRENT_SECTOR
            elif self.state == STOP_ROBOT:
                self.move_to_coordinates({"x": 0, "y": 100, "z": 200}, self.stopped)

        print("stoping robot")
        stop_run()
        sys.exit(0)

    def moving(self):
        self.state = MOVING

    def stopped(self):
        self.state = STOPPED

    def drop_element(self):
        self.state = DROP_ELEMENT

    def move_to_coordinates(self, coordinates, state_change_callback):
        self.target_position = coordinates
        self.log_target_position()
        self.moving_to_angles = add_angles(
            self.current_angles,
            calculate_new_angles_movement(self.current_robot_position, self.target_position)
        )
        self.log_moving_to_angles()
        self.motors.move_to((self.current_angles["alpha"], self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                            (self.current_angles["beta"], self.moving_to_angles["beta"], MOVEMENT_DURATION),
                            (self.current_angles["gamma"], self.moving_to_angles["gamma"], MOVEMENT_DURATION),
                            combine_functions(self.on_moved, state_change_callback))
        post_move((self.current_angles["alpha"], self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                  (self.current_angles["beta"], self.moving_to_angles["beta"], MOVEMENT_DURATION),
                  (self.current_angles["gamma"], self.moving_to_angles["gamma"], MOVEMENT_DURATION))

    def detect_image(self):
        self.state = DETECT_IMAGE

    def above_element(self):
        self.state = ABOVE_ELEMENT

    def at_element(self):
        self.state = AT_ELEMENT

    def on_moved(self):
        self.current_angles = self.moving_to_angles
        self.current_robot_position = self.target_position

    def log_moving_to_angles(self):
        print(
            "Moving Robot to anlges RAD: alpha(" + str(self.moving_to_angles["alpha"]) + "), beta(" + str(
                self.moving_to_angles["beta"]) + "), gamma(" + str(self.moving_to_angles["gamma"]) + ")")
        print(
            "Moving Robot to anlges DEG: alpha(" + str(np.rad2deg(self.moving_to_angles["alpha"])) + "), beta(" + str(
                np.rad2deg(self.moving_to_angles["beta"])) + ") , gamma(" + str(
                np.rad2deg(self.moving_to_angles["gamma"])) + ")")

    def log_target_position(self):
        print("Target Position calculated: x(" + str(self.target_position["x"]) + "), y("
              + str(self.target_position["y"]) + "), z(" + str(self.target_position["z"]) + ")")

    def log_current_position(self):
        print("Current position: x(" + str(self.current_robot_position["x"]) + "), y("
              + str(self.current_robot_position["y"]) + "), z(" + str(self.current_robot_position["z"]) + ")")

    def log_state(self):
        if self.state != MOVING:
            print("State: " + self.state)


def combine_functions(func1, func2):
    def combined():
        func1()
        func2()

    return combined


if __name__ == "__main__":
    Robot().loop()
