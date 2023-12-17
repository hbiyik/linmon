'''
Created on Mar 2, 2023

@author: boogie
'''
import os

from liblinmon import Collection, Sensor, tools


platform_dir = "/sys/devices/platform/"
devfreq_dir = "/sys/class/devfreq"
clk_dir = "/sys/kernel/debug/clk"
clk_devices = {}


class ClkSensor(Sensor):
    def __init__(self, name, file, scale, unit):
        self.name = name
        self.file = file
        self.scale = scale
        self.unit = unit
        self.attrs = []


class ClkColl(Collection):
    def __init__(self, dev, clocks):
        self.dev = dev
        self.clocks = clocks

    def __repr__(self):
        return self.dev

    def __iter__(self):
        for clk in self.clocks:
            clk_path = os.path.join(clk_dir, clk, "clk_rate")
            if os.path.exists(clk_path):
                yield ClkSensor(clk, clk_path, 1000000, "Mhz")


def Collections():
    if not clk_devices:
        for sub in os.listdir(platform_dir):
            clock_names = os.path.join(platform_dir, sub, "of_node", "clock-names")
            if os.path.exists(clock_names):
                clocks = tools.parsefile(clock_names, False).split("\x00")
                if clocks:
                    clk_devices[sub] = clocks
    colls = []
    for dev, clocks in clk_devices.items():
        colls.append(ClkColl(dev, clocks))
    return colls
