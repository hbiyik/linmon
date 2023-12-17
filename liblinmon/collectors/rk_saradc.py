'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from operator import attrgetter
from liblinmon import Collection, Sensor, tools, Attr
from liblinmon.collectors.devices import rock5b

rootdir = "/sys/bus/iio/devices/"
volprefix = "in_voltage"


class VinAttr(Attr):
    name = "vin"

    def map(self):
        if self.sensor.inscale:
            return True

    @property
    def unit(self):
        return "V"

    @property
    def value(self):
        return self.sensor.value / self.sensor.inscale


class SaradcSensor(Sensor):
    def __init__(self, subdir, index, suffix, inscale):
        self.index = index
        self.name = f"SARADC{self.index}"
        self.inscale = inscale
        self.unit = ""
        self.file = os.path.join(subdir, f"{volprefix}{index}_{suffix}")
        self.attrs = []


class RkSaradc(Collection):
    attrs = [VinAttr,
             rock5b.VsupplyAttr,
             rock5b.RecoveryAttr,
             rock5b.BootModeAttr,
             rock5b.BoardId]

    def __init__(self, path, compat):
        self.path = path
        self.compat = compat

    def __repr__(self):
        return f"{self.compat} ({self.path})"

    def __iter__(self):
        saradcs = []
        scale = os.path.join(self.path, "in_voltage_scale")
        if os.path.exists(scale):
            scale = 1000 / float(tools.parsefile(scale))
        else:
            scale = None
        for fname in os.listdir(self.path):
            matchvolt = re.search(f"{volprefix}([0-9+])_(.+)", fname)
            if matchvolt:
                saradcs.append(SaradcSensor(self.path, int(matchvolt.group(1)),  matchvolt.group(2), scale))
        for saradc in sorted(saradcs, key=attrgetter("index")):
            for attrCls in self.attrs:
                attr = attrCls(saradc)
                if attr.map():
                    saradc.attrs.append(attr)
            yield saradc


def Collections():
    hwmons = []
    for rksaradc, compat in tools.iterdrivers(rootdir, "r[kv][0-9]+.*?saradc"):
        hwmons.append(RkSaradc(rksaradc, compat))
    return sorted(hwmons, key=attrgetter("path"))
