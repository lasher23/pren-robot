import math
import sys
import time
import numpy as np
from detection import Detection, IMAGE_RESOLUTION_WIDTH, IMAGE_RESOLUTION_HEIGHT
from motors import Motors
from positions_calculation import calculate_new_angles_movement, add_angles
from web_api import post_move

MOVEMENT_DURATION = 10000


def calculate_target_coordinates_from_pixels(current_robot_position, on_camera_position):
    pi_cam_alpha = np.deg2rad(62.2)
    pi_cam_beta = np.deg2rad(48.8)

    camera_height = current_robot_position["z"]
    total_view_x = camera_height * np.tan(pi_cam_alpha / 2) * 2
    total_view_y = camera_height * np.tan(pi_cam_beta / 2) * 2
    camera_top_left_corner_x = current_robot_position["x"] - total_view_x / 2
    camera_top_left_corner_y = current_robot_position["y"] - total_view_y / 2
    pixel_per_coordinate_x = IMAGE_RESOLUTION_WIDTH / total_view_x
    pixel_per_coordinate_y = IMAGE_RESOLUTION_HEIGHT / total_view_y
    coordinate_x = camera_top_left_corner_x + on_camera_position["x"] / pixel_per_coordinate_x
    coordinate_y = camera_top_left_corner_y + on_camera_position["y"] / pixel_per_coordinate_y
    return {"x": coordinate_x, "y": coordinate_y, "z": current_robot_position["z"]}


class Robot:
    state = "INIT"
    detection = Detection()
    motors = Motors()
    current_robot_position = None
    target_position = None
    current_angles = {"alpha": None, "beta": None, "gamma": None}
    moving_to_angles = {"alpha": None, "beta": None, "gamma": None}

    def loop(self):
        while self.state != "STOP":
            # print("Current state: " + state)
            if self.state == "INIT":
                self.current_robot_position = {"x": 0, "y": 200, "z": 0}
                self.current_angles = {"alpha": 0, "beta": 0, "gamma": 0}
                print("Initialized Robot at Position: " + str(self.current_robot_position))
                self.state = "DETECT_IMAGE"
            elif self.state == "DETECT_IMAGE":
                camera_pixel_position = self.detection.detect()
                print("Detected Object at Position: " + str(camera_pixel_position))
                # self.target_p = calculate_target_coordinates_from_pixels(current_robot_position,
                #                                                                camera_pixel_position)
                self.target_position = {"x": 60, "y": 800, "z": 200}  # 200 hardcoded height for image detection
                self.log_target_position()
                angles_delta = calculate_new_angles_movement(self.current_robot_position, self.target_position)
                self.moving_to_angles = add_angles(self.current_angles, angles_delta)

                self.log_moving_to_angles()

                # TODO Motor probably needs the delta of the angle and not the new target angle
                self.motors.move_to((self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                                    (self.moving_to_angles["beta"], MOVEMENT_DURATION),
                                    (self.moving_to_angles["gamma"], MOVEMENT_DURATION),
                                    self.on_x_y_moved)
                self.state = "MOVING"
                post_move((self.current_angles["alpha"], self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                          (self.current_angles["beta"], self.moving_to_angles["beta"], MOVEMENT_DURATION),
                          (self.current_angles["gamma"], self.moving_to_angles["gamma"], MOVEMENT_DURATION))
            elif self.state == "MOVING":
                time.sleep(0)
            elif self.state == "X_Y_MOVED":
                self.target_position = {**self.target_position, "z": 0}
                self.log_target_position()
                self.moving_to_angles = add_angles(
                    self.current_angles,
                    calculate_new_angles_movement(self.current_robot_position, self.target_position)
                )
                self.log_moving_to_angles()
                self.motors.move_to((self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                                    (self.moving_to_angles["beta"], MOVEMENT_DURATION),
                                    (self.moving_to_angles["gamma"], MOVEMENT_DURATION),
                                    self.on_z_moved)
                post_move((self.current_angles["alpha"], self.moving_to_angles["alpha"], MOVEMENT_DURATION),
                          (self.current_angles["beta"], self.moving_to_angles["beta"], MOVEMENT_DURATION),
                          (self.current_angles["gamma"], self.moving_to_angles["gamma"], MOVEMENT_DURATION))
                self.state = "MOVING"

        print("stoping robot")
        sys.exit(0)

    def on_x_y_moved(self):
        self.state = "X_Y_MOVED"
        self.current_angles = self.moving_to_angles
        self.current_robot_position = self.target_position

    def on_z_moved(self):
        self.state = "STOP"
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


if __name__ == "__main__":
    Robot().loop()
