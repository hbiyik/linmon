'''
Created on Mar 2, 2023

@author: boogie
'''
import os
from liblinmon import Collection, Sensor


dmi_dir = "/sys/class/dmi"


class DmiSensor(Sensor):
    def __init__(self, path, name, file, scale, unit):
        self.name = name
        self.path = path
        self.file = os.path.join(path, file)
        self.scale = scale
        self.unit = unit
        self.attrs = []


class DmiColl(Collection):
    def __init__(self, path):
        self.name = path
        self.path = os.path.join(dmi_dir, path)

    def __repr__(self):
        return self.name

    def __iter__(self):
        for attr in os.listdir(self.path):
            if attr in ["modalias", "uevent"]:
                continue
            attr_path = os.path.join(self.path, attr)
            if os.path.isdir(attr_path):
                continue
            sensor = DmiSensor(self.path, attr.replace("_", " ").title(), attr, "", "")
            yield sensor


def Collections():
    colls = []
    if not os.path.exists(dmi_dir):
        return colls
    for sub in os.listdir(dmi_dir):
        colls.append(DmiColl(sub))
    return colls
