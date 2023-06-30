class VacuumPicker:
    def __init__(self, serial):
        self.serial = serial

    def pick_up(self):
        print("calling vacuum picker to pick up")
        command = "gpio pP.sH\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break
        command = "gpio pV.sH\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break

    def drop_down(self):
        print("calling vacuum picker to drop down")
        command = "gpio pV.sL\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break
        command = "gpio pP.sL\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break