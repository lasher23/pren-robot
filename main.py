import sys
import time
from datetime import datetime, timedelta

from height_sensor import MockHeightSensor, HeightSensor
from vacuum_picker import VacuumPicker

try:
    import serial
except:
    print("Not on Raspi")
import numpy as np

from detection import IMAGE_RESOLUTION_WIDTH, IMAGE_RESOLUTION_HEIGHT, MockDetection, Detection
from motors import MockMotors, Motors
from positions_calculation import calculate_new_angles_movement, add_angles
from web_api import post_move, start_run, post_object, stop_run, should_run

HEIGHT_SENSOR_DELTA = 10

MOVEMENT_DURATION = 2000

WAIT_START = "WAIT_START"
INIT = "INIT"
INIT_BACK = "INIT_BACK"
INIT_SLOW = "INIT_SLOW"
INIT_FINISH = "INIT_FINISH"
NEW_SECTOR = "NEW_SECTOR"
DETECT_IMAGE = "DETECT_IMAGE"
DETECT_IMAGE_SECOND = "DETECT_IMAGE_SECOND"
MOVING = "MOVING"
ABOVE_ELEMENT = "ABOVE_ELEMENT"
AT_ELEMENT = "AT_ELEMENT"
TO_DROP = "TO_DROP"
DROP_ELEMENT = "DROP_ELEMENT"
CURRENT_SECTOR = "CURRENT_SECTOR"
STOP_ROBOT = "STOP_ROBOT"
STOPPED = "STOPPED"
MOVE_STEP_DOWN = "MOVE_STEP_DOWN"
CHECK_FURTHER_DOWN = "CHECK_FURTHER_DOWN"
INIT_DONE = "INIT_DONE"
CIGARETTES_DROP = {"x": 180, "y": 200, "z": 100}
PET_DROP = {"x": 90, "y": 200, "z": 100}
KRONKORKEN_DROP = {"x": -90, "y": 200, "z": 100}
VALUABLE_DROP = {"x": -180, "y": 200, "z": 100}

CAMERA_OFFSET = 30


def calculate_target_coordinates_from_pixels(current_robot_position, on_camera_position_pixels, current_angles):
    pi_cam_alpha = np.deg2rad(27)
    pi_cam_beta = np.deg2rad(27)

    height_to_object = current_robot_position["z"] + 105
    # todo measure height of object must be robot height + height of 0 to bottom

    # total_view_x = height_to_object * np.tan(pi_cam_alpha / 2) * 2
    # total_view_y = height_to_object * np.tan(pi_cam_beta / 2) * 2
    #
    # pixel_per_coordinate_x = IMAGE_RESOLUTION_WIDTH / total_view_x
    # pixel_per_coordinate_y = IMAGE_RESOLUTION_HEIGHT / total_view_y

    alpha = current_angles["alpha"]

    pixel_from_middle_x = -IMAGE_RESOLUTION_WIDTH / 2 + on_camera_position_pixels["x"]
    print("pixel_from_middle_x: " + str(pixel_from_middle_x))
    pixel_from_middle_y = -IMAGE_RESOLUTION_HEIGHT / 2 + (640 - on_camera_position_pixels["y"])
    print("pixel_from_middle_y: " + str(pixel_from_middle_y))

    dummy_x = height_to_object * np.tan(pi_cam_alpha) * pixel_from_middle_x / 320
    print("dummy_x: " + str(dummy_x))
    dummy_y = height_to_object * np.tan(pi_cam_beta) * pixel_from_middle_y / 320
    print("dummy_y: " + str(dummy_y))

    distance = np.sqrt(dummy_x ** 2 + dummy_y ** 2)
    print("distance: " + str(distance))
    angle = (np.arctan2(-dummy_y, dummy_x) + np.deg2rad(90)) % np.deg2rad(360) - np.deg2rad(180)
    print("angle: " + str(angle))

    total_angle = alpha + angle
    print("total_angle: " + str(total_angle))

    minus_delta_x = distance * np.sin(total_angle)
    print("minus_delta_x: " + str(minus_delta_x))
    minus_delta_y = distance * np.cos(total_angle)
    print("minus_delta_y: " + str(minus_delta_y))

    return {
        "x": current_robot_position["x"] + minus_delta_x,
        "y": current_robot_position["y"] + minus_delta_y - CAMERA_OFFSET,
        "z": current_robot_position["z"]
    }


class Robot:
    state = WAIT_START
    #    motors = MockMotors()
    #     height_sensor = MockHeightSensor()
    # /dev/ttyACM0
    ser = serial.Serial('/dev/ttyACM0', 57600, timeout=10000)
    motors = Motors(ser)
    height_sensor = HeightSensor(ser)
    vacuum_picker = VacuumPicker(ser)
    current_robot_position = None
    target_position = None
    current_angles = {"alpha": None, "beta": None, "gamma": None}
    moving_to_angles = {"alpha": None, "beta": None, "gamma": None}
    current_type = None
    # detection = MockDetection([
    #     {"x": 400, "y": 200, "type": "PET"},
    #     None,
    #     {"x": 200, "y": 400, "type": "Kronkorken"},
    #     None,
    #     {"x": 100, "y": 0, "type": "Cigarette"},
    #     None,
    #     {"x": 320, "y": 320, "type": "Valuable"},
    #     None,
    #     {"x": 320, "y": 320, "type": "PET"},
    #     None,
    #     {"x": 320, "y": 320, "type": "Kronkorken"},
    #     None,
    #     {"x": 320, "y": 320, "type": "Cigarette"},
    #     None,
    #     {"x": 320, "y": 320, "type": "Valuable"},
    #     None,
    # ])
    detection = Detection()
    current_sector = None
    sectors = [
        {
            "position": {
                "x": 100,
                "y": 600,
                "z": 100
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
        wait_until_not_moving_for_stopping = False
        self.start_time = datetime.now()
        while self.state != STOPPED:
            if wait_until_not_moving_for_stopping:
                if self.state == MOVING:
                    time.sleep(0)
                    continue
                else:
                    self.state = STOP_ROBOT

            self.log_state()
            if self.state != WAIT_START and not should_run():
                if self.state == MOVING:
                    wait_until_not_moving_for_stopping = True
                else:
                    self.state = STOP_ROBOT
            # print("Current state: " + state)
            if self.state == WAIT_START:
                if should_run():
                    self.state = INIT
            if self.state == INIT:
                start_run()
                self.motors.move_to((0, 90, MOVEMENT_DURATION),
                                    (0, 90, MOVEMENT_DURATION),
                                    (0, 90, MOVEMENT_DURATION), self.init_back, True)
                self.moving()
            elif self.state == INIT_BACK:
                self.motors.move_to((0, -0.02, MOVEMENT_DURATION),
                                    (0, -0.02, MOVEMENT_DURATION),
                                    (0, -0.02, MOVEMENT_DURATION), self.init_slow, False, True)
                self.moving()
            elif self.state == INIT_SLOW:
                start_run()
                self.motors.move_to((0, 90, MOVEMENT_DURATION),
                                    (0, 90, MOVEMENT_DURATION),
                                    (0, 90, MOVEMENT_DURATION), self.init_done, True, speed=1)
                self.moving()
            elif self.state == INIT_DONE:
                self.motors.move_to((0, -0.0174533, MOVEMENT_DURATION),
                                    (0, -0.0174533, MOVEMENT_DURATION),
                                    (0, -0.0174533, MOVEMENT_DURATION), self.new_sector, False, True)
                self.current_robot_position = {"x": 115.14, "y": 115.14, "z": 0}
                self.current_angles = {"alpha": 0.785398 - 0.0174533, "beta": 1.43117 - 0.0174533,
                                       "gamma": 2.86234 - 0.0174533}
                self.moving()
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
                if not self.detect_and_move_above(self.detect_image_second):
                    self.state = NEW_SECTOR
            elif self.state == DETECT_IMAGE_SECOND:
                if not self.detect_and_move_above(self.above_element):
                    self.state = NEW_SECTOR
            elif self.state == MOVING:
                time.sleep(0)
            elif self.state == ABOVE_ELEMENT:
                self.check_further_down()
            elif self.state == MOVE_STEP_DOWN:
                self.move_to_coordinates({**self.current_robot_position, "z": self.current_robot_position["z"] - 10},
                                         self.check_further_down)
                self.moving()
            elif self.state == CHECK_FURTHER_DOWN:
                if self.height_sensor.sensor_on():
                    self.at_element()
                else:
                    self.move_step_down()
            elif self.state == AT_ELEMENT:
                self.vacuum_picker.pick_up()
                self.move_to_coordinates(
                    {**self.current_robot_position, "z": self.current_robot_position["z"] - HEIGHT_SENSOR_DELTA},
                    self.to_drop)

                self.moving()
            elif self.state == TO_DROP:
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
                self.vacuum_picker.drop_down()
                post_object(self.current_type)
                self.state = CURRENT_SECTOR
            elif self.state == STOP_ROBOT:
                self.move_to_coordinates({"x": 0, "y": 100, "z": 100}, self.stopped)
                self.moving()

        print("stoping robot")
        stop_run()
        sys.exit(0)

    def to_drop(self):
        self.state = TO_DROP

    def init_back(self):
        self.state = INIT_BACK

    def init_slow(self):
        self.state = INIT_SLOW

    def new_sector(self):
        self.state = NEW_SECTOR

    def init_done(self):
        self.state = INIT_DONE

    def move_step_down(self):
        self.state = MOVE_STEP_DOWN

    def check_further_down(self):
        self.state = CHECK_FURTHER_DOWN

    def moving(self):
        self.state = MOVING

    def stopped(self):
        self.state = STOPPED

    def drop_element(self):
        self.state = DROP_ELEMENT

    def move_to_coordinates(self, coordinates, state_change_callback):
        self.target_position = coordinates
        self.log_current_position()
        self.log_current_angles()
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

    def detect_image_second(self):
        self.state = DETECT_IMAGE_SECOND

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

    def log_current_angles(self):
        print(
            "Current anlges RAD: alpha(" + str(self.current_angles["alpha"]) + "), beta(" + str(
                self.current_angles["beta"]) + "), gamma(" + str(self.current_angles["gamma"]) + ")")
        print(
            "Current anlges DEG: alpha(" + str(np.rad2deg(self.current_angles["alpha"])) + "), beta(" + str(
                np.rad2deg(self.current_angles["beta"])) + ") , gamma(" + str(
                np.rad2deg(self.current_angles["gamma"])) + ")")

    def log_target_position(self):
        print("Target Position: x(" + str(self.target_position["x"]) + "), y("
              + str(self.target_position["y"]) + "), z(" + str(self.target_position["z"]) + ")")

    def log_current_position(self):
        print("Current position: x(" + str(self.current_robot_position["x"]) + "), y("
              + str(self.current_robot_position["y"]) + "), z(" + str(self.current_robot_position["z"]) + ")")

    def log_state(self):
        if self.state != MOVING:
            print("State: " + self.state)

    def detect_and_move_above(self, next_state):
        camera_pixel_position = self.detection.detect()
        if camera_pixel_position is None:
            print("No Image Detected")
            return False
        print("Detected Object at Position: " + str(camera_pixel_position))
        new_coordinates = calculate_target_coordinates_from_pixels(self.current_robot_position,
                                                                   camera_pixel_position,
                                                                   self.current_angles)
        new_coordinates["z"] = 100
        self.move_to_coordinates(new_coordinates, next_state)
        self.moving()
        return True


def combine_functions(func1, func2):
    def combined():
        func1()
        func2()

    return combined


if __name__ == "__main__":
    Robot().loop()
