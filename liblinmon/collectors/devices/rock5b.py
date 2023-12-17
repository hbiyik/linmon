'''
Created on Dec 16, 2023

@author: boogie
'''
import os
from liblinmon import tools, Attr


class VsupplyAttr(Attr):
    name = "vsupply"

    @property
    def unit(self):
        return "V"

    def check_rock5b(self):
        return (os.path.exists("/proc/device-tree/model") and
                "rock5b" in tools.parsefile("/proc/device-tree/model").lower().replace(" ", "").replace("-", "")) or \
                (os.path.exists("/proc/device-tree/compatible") and
                 "rock5b" in tools.parsefile("/proc/device-tree/compatible").lower().replace(" ", "").replace("-", ""))

    def map(self):
        if self.check_rock5b() and self.sensor.index == 6:
            return True

    @property
    def value(self):
        # 8.2 to 100K external voltage divider
        return self.sensor.value * (100 + 8.2) / (self.sensor.inscale * 8.2)


class RecoveryAttr(VsupplyAttr):
    name = "recovery"

    @property
    def unit(self):
        return ""

    def map(self):
        if self.check_rock5b() and self.sensor.index == 1:
            return True

    @property
    def value(self):
        # 8.2 to 100K external voltage divider
        return "OFF" if self.sensor.value > 100 else "ON"


class BoardId(RecoveryAttr):
    name = "boardid"
    ranges = [[0.00, 0.15, "A"],  # 0V
              [0.15, 0.45, "B"],  # 0.3V
              [0.45, 0.75, "C"],  # 0.6V
              [0.75, 1.05, "D"],  # 0.9V
              [1.05, 1.35, "E"],  # 1.2V
              [1.35, 1.65, "F"],  # 1.5V
              [1.65, 1.95, "H"],  # 1.8V
              ]

    def map(self):
        if self.check_rock5b() and self.sensor.index == 5:
            return True

    @property
    def value(self):
        # 8.2 to 100K external voltage divider
        inval = self.sensor.value / self.sensor.inscale
        for low, high, value in self.ranges:
            if inval >= low and inval < high:
                return value


class BootModeAttr(BoardId):
    name = "bootmode"
    ranges = [[0.00, 0.15, "USB"],  # 0V
              [0.15, 0.45, "SD Card-USB"],  # 0.3V
              [0.45, 0.75, "EMMC-USB"],  # 0.6V
              [0.75, 1.05, "FSPI M0-USB"],  # 0.9V
              [1.05, 1.35, "FSPI M1-USB"],  # 1.2V
              [1.35, 1.65, "FSPI M2-USB"],  # 1.5V
              [1.65, 1.95, "FSPI_M2-FSPI_M1-FSPI_M0-EMMC-SD Card-USB"],  # 1.8V
              ]

    def map(self):
        if self.check_rock5b() and self.sensor.index == 0:
            return True
