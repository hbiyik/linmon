'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from liblinmon import Collection, Sensor, Attr, tools

regulator_dir = "/sys/class/regulator"


class RegulatorAttr(Attr):
    @property
    def file(self):
        return os.path.join(self.sensor.path, self.name + "_" + self.sensor.dataname)


class RegulatorProp(Attr):

    @property
    def file(self):
        return os.path.join(self.sensor.path, self.name)

    @property
    def unit(self):
        return ""

    @property
    def value(self):
        return tools.parsefile(self.file)


class MinAttr(RegulatorAttr):
    name = "min"


class MaxAttr(RegulatorAttr):
    name = "max"


class CritAttr(RegulatorAttr):
    name = "crit"


class CritAlarmAttr(RegulatorAttr):
    name = "crit_alarm"


class BeepAttr(RegulatorAttr):
    name = "beep"


class AlarmAttr(RegulatorAttr):
    name = "alarm"


class OffsetAttr(RegulatorAttr):
    name = "offset"


class CapMaxAttr(RegulatorAttr):
    name = "cap_max"


class CapMinAttr(RegulatorAttr):
    name = "cap_min"


class CapAttr(RegulatorAttr):
    name = "cap"


class RequestedAttr(RegulatorAttr):
    name = "requested"


class StatusProp(RegulatorProp):
    name = "status"


class StateProp(RegulatorProp):
    name = "state"


class NumUsersProp(RegulatorProp):
    name = "num_users"


class Reg_Sensor(Sensor):

    def __init__(self, path, dataname):
        self.path = path
        devname = tools.parseuevent_name(self.path) or self.path
        self.unit = "A" if dataname == "microamps" else "V"
        self.scale = 1000000
        self.label = devname.split("/")[-1]
        self.name = tools.parsefile(os.path.join(self.path, "name"))
        self.dataname = dataname
        self.file = os.path.join(self.path, dataname)
        self.attrs = []


class Reg_Collection(Collection):
    attrs = [MinAttr, MaxAttr, CritAttr, CritAlarmAttr, BeepAttr, AlarmAttr,
             OffsetAttr, CapAttr, CapMaxAttr, CapMinAttr, RequestedAttr, StatusProp, StateProp, NumUsersProp]

    def __repr__(self):
        return "Regulators"

    def __iter__(self):
        if not os.path.exists(regulator_dir):
            return
        for regulator in os.listdir(regulator_dir):
            regulator = os.path.join(regulator_dir, regulator)
            regtype = tools.parsefile(os.path.join(regulator, "type"))
            if regtype:
                dataname = "microamps" if regtype == "current" else "microvolts"
                if os.path.exists(os.path.join(regulator, dataname)):
                    sensor = Reg_Sensor(regulator, dataname)
                    for attrCls in self.attrs:
                        attr = attrCls(sensor)
                        if attr.map():
                            sensor.attrs.append(attr)
                    yield sensor
