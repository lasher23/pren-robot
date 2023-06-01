class HeightSensor:
    def __init__(self, serial):
        self.serial = serial

    def sensor_on(self):
        self.serial.write(bytes("input mz", 'ascii'))
        result = self.serial.readline().decode().strip()
        return result == "on"


class MockHeightSensor:
    def __init__(self):
        self.count = 0

    def sensor_on(self):
        self.count += 1
        return self.count % 10 == 0
