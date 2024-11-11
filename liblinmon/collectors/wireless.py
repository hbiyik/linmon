'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from liblinmon import Collection, Sensor, Attr, tools


proc_wifi = "/proc/net/wireless"


def parseproc():
    if os.path.exists(proc_wifi):
        for line in tools.parsefile(proc_wifi, False).split("\n")[2:]:
            params = [x.replace(":", "").replace(".", "") for x in re.split(r"\s+", line) if x != ""]
            if params:
                yield params


class QualAttr(Attr):
    index = 0

    @property
    def value(self):
        if self.sensor.params:
            return float(self.sensor.params[self.index])


class LinkAttr(QualAttr):
    name = "Link"
    index = 2
    unit = "dB"


class LevelAttr(QualAttr):
    name = "Level"
    index = 3
    unit = "dB"


class NoiseAttr(QualAttr):
    name = "Noise"
    index = 4
    unit = "dB"


class Quality(Sensor):
    def __init__(self, interface):
        self.interface = interface
        self.name = "Quality"
        self.scale = 1
        self.unit = "%"
        self.params = []
        self.attrs = [LinkAttr(self), LevelAttr(self), NoiseAttr(self)]

    def read(self):
        for params in parseproc():
            interface = params[0]
            link = params[2]
            if self.interface == interface:
                self.params = params
                self.value = 100 * float(link) / 70


class ProcWifiColl(Collection):
    @staticmethod
    def parseinterfaces():
        if os.path.exists(proc_wifi):
            for line in tools.parsefile(proc_wifi, False).split("\n")[1:]:
                yield [x for x in re.split(r"\s+", line) if x != ""]

    def __init__(self, interface):
        self.interface = interface

    def __repr__(self):
        return self.interface

    def __iter__(self):
        yield Quality(self.interface)


def Collections():
    colls = []
    for params in parseproc():
        colls.append(ProcWifiColl(params[0]))
    return colls
