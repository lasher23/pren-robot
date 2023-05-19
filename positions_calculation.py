# alpha is a difference calculation and the other ones are absolut calculations
import numpy as np

ZERO_COORDINATE = {"x": 0, "y": 0, "z": 0}
ROBOT_ARM_LENGTH_FIRST = 585
ROBOT_ARM_LENGTH_SECOND = 585


def add_angles(angles1, angles2):
    return {
        "alpha": angles1["alpha"] + angles2["alpha"],
        "beta": angles2["beta"],
        "gamma": angles2["gamma"]
    }


def calculate_distance_between_coordinates(point1, point2):
    return np.sqrt((point2["x"] - point1["x"]) ** 2 + (point2["y"] - point1["y"]) ** 2)


def calculate_cos(a, b, c):
    return np.arccos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c))


def calculate_new_angles_movement(current_robot_position, target_position):
    alpha_target_angle = calculate_cos(
        calculate_distance_between_coordinates(current_robot_position, target_position),
        calculate_distance_between_coordinates(ZERO_COORDINATE, target_position),
        calculate_distance_between_coordinates(ZERO_COORDINATE, current_robot_position)
    )
    height = target_position["z"]

    distance_on_height = np.sqrt(
        calculate_distance_between_coordinates(ZERO_COORDINATE, target_position) ** 2
        + height ** 2
    )

    beta_height = np.tanh(
        height / calculate_distance_between_coordinates(ZERO_COORDINATE, target_position))

    beta_target_angle = calculate_cos(
        ROBOT_ARM_LENGTH_SECOND,
        ROBOT_ARM_LENGTH_FIRST,
        distance_on_height
    ) + beta_height

    gamma_target_angle = 3.14159 - calculate_cos(  # 180 degree minus
        distance_on_height,
        ROBOT_ARM_LENGTH_SECOND,
        ROBOT_ARM_LENGTH_FIRST
    )
    return {"alpha": alpha_target_angle, "beta": beta_target_angle, "gamma": gamma_target_angle}
