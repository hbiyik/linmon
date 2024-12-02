'''
Created on Mar 2, 2023

@author: boogie
'''
import os
from liblinmon import Collection, Sensor, Attr, tools


drm_dir = "/sys/class/drm"


class DrmAttr(Attr):
    @property
    def file(self):
        return os.path.join(self.sensor.path, self.path)


class MaxAttr(DrmAttr):
    name = "max"
    path = "gt_max_freq_mhz"


class MinAttr(DrmAttr):
    name = "min"
    path = "gt_min_freq_mhz"


class BoostAttr(DrmAttr):
    name = "boost"
    path = "gt_boost_freq_mhz"


class DrmSensor(Sensor):
    def __init__(self, path, name, file, scale, unit):
        self.name = name
        self.path = path
        self.file = os.path.join(path, file)
        self.scale = scale
        self.unit = unit
        self.attrs = []


class i915Coll(Collection):
    sensors = [(DrmSensor, "gt_act_freq_mhz", "actual_freq", 1, "Mhz", [MinAttr, MaxAttr, BoostAttr]),
               (DrmSensor, "gt_cur_freq_mhz", "current_freq", 1, "Mhz", [MinAttr, MaxAttr, BoostAttr])]

    def __init__(self, path):
        self.name = path
        self.path = os.path.join(drm_dir, path)

    def __repr__(self):
        return "%s:i915" % self.name

    def __iter__(self):
        for sensorCls, file, name, scale, unit, attrs in self.sensors:
            sensor = sensorCls(self.path, name, file, scale, unit)
            for attrCls in attrs:
                attr = attrCls(sensor)
                if attr.map():
                    sensor.attrs.append(attr)
            yield sensor


def Collections():
    colls = []
    if not os.path.exists(drm_dir):
        return colls
    for sub in os.listdir(drm_dir):
        if "render" in sub:
            # skip render devices nothing to see here
            continue
        dev_path = os.path.join(drm_dir, sub)
        device = tools.parseuevent_driver(os.path.join(dev_path, "device"))
        if not device:
            continue
        if device == "i915":
            colls.append(i915Coll(sub))
    return colls
