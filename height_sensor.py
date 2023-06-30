class HeightSensor:
    def __init__(self, serial):
        self.serial = serial

    def sensor_on(self):
        self.serial.write(bytes("gpio mZ.sX\n", 'ascii'))
        result = self.serial.readline().decode().strip()
        print("RESULT: " + result)
        return "OFF" in result


class MockHeightSensor:
    def __init__(self):
        self.count = 0

    def sensor_on(self):
        self.count += 1
        return self.count % 10 == 0
