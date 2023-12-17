import os
from liblinmon import tools


class Sensor:
    name = "sensor"
    label = None
    unit = ""
    value = 0.0
    file = None
    scale = 1
    attrs = []
    datatype = None

    def readfile(self, fpath, scale=None):
        value = tools.parsefile(fpath)
        if value and self.datatype:
            value = self.datatype(value)
        if value is not None and value.lstrip("-").isdigit():
            value = float(value)
            if scale:
                value /= scale
        return value

    def read(self):
        if self.file:
            self.value = self.readfile(self.file, self.scale)


class Collection:
    def __iter__(self):
        raise NotImplemented

    def __repr__(self):
        raise NotImplemented


class Attr:
    name = None

    def __init__(self, sensor):
        self.sensor = sensor

    @property
    def unit(self):
        return self.sensor.unit

    def map(self):
        if os.path.exists(self.file):
            return True

    @property
    def value(self):
        return self.sensor.readfile(self.file, self.sensor.scale)
