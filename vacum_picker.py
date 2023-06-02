class VacumPicker:
    def __init__(self, serial):
        self.serial = serial

    def pick_up(self):
        command = "gpio pV.sH\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break

    def let_down(self):
        command = "gpio pV.sL\n"
        self.serial.write(bytes(command, 'ascii'))
        while True:
            result = self.serial.readline().decode().strip()
            if "successfully" in result:
                print("result is:")
                print(result)
                break
