'''
Created on Mar 2, 2023

@author: boogie
'''
import re
import os

from liblinmon import Collection, Sensor, Attr


devfreq_dir = "/sys/class/devfreq"


class DevFreqAttr(Attr):
    @property
    def file(self):
        return os.path.join(self.sensor.path, self.path)


class MaxAttr(DevFreqAttr):
    name = "max"
    path = "max_freq"


class MinAttr(DevFreqAttr):
    name = "min"
    path = "min_freq"


class TargetAttr(DevFreqAttr):
    name = "target"
    path = "target_freq"


class UpAttr(DevFreqAttr):
    name = "up"
    path = "upthreshold"


class DownAttr(DevFreqAttr):
    name = "down"
    path = "downdifferential"


class AvailFreqAttr(DevFreqAttr):
    name = "available"
    path = "available_frequencies"

    @property
    def unit(self):
        return ""

    @property
    def value(self):
        freqs = [str(int(int(x)/self.sensor.scale)) for x in self.sensor.readfile(self.file).split(" ")]
        return " ".join(freqs) + " " + self.sensor.unit


class AvailGovAttr(DevFreqAttr):
    name = "available"
    path = "available_governors"


class DevfreqSensor(Sensor):
    def __init__(self, path, name, file, scale, unit):
        self.name = name
        self.path = path
        self.file = os.path.join(path, file)
        self.scale = scale
        self.unit = unit
        self.attrs = []


class LoadSensor(DevfreqSensor):
    def read(self):
        value = self.readfile(self.file, self.scale)
        value = re.search("([0-9]+)@", value)
        if value:
            self.value = int(value.group(1))


class Devfreq(Collection):
    sensors = [(DevfreqSensor, "frequency", "cur_freq", 1000000, "Mhz", [MaxAttr, MinAttr, TargetAttr, AvailFreqAttr]),
               (DevfreqSensor, "governor", "governor", None, "", [AvailGovAttr]),
               (LoadSensor, "load", "load", None, "", [UpAttr, DownAttr])]

    def __init__(self, path, devfreq):
        self.path = path
        self.devfreq = devfreq

    def __repr__(self):
        return self.devfreq

    def __iter__(self):
        for sensorCls, name, file, scale, unit, attrs in self.sensors:
            freq = os.path.join(self.path, file)
            if os.path.exists(freq):
                sensor = sensorCls(self.path, name, file, scale, unit)
                for attrCls in attrs:
                    attr = attrCls(sensor)
                    if attr.map():
                        sensor.attrs.append(attr)
                yield sensor


def Collections():
    colls = []
    if not os.path.exists(devfreq_dir):
        return colls
    for devfreq in os.listdir(devfreq_dir):
        colls.append(Devfreq(os.path.join(devfreq_dir, devfreq), devfreq))
    return colls
