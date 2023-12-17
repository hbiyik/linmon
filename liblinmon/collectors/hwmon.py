'''
Created on Mar 2, 2023

@author: boogie
'''
import re
import os

from operator import attrgetter
from liblinmon import Collection, Sensor, Attr, tools


hwmon_dir = "/sys/class/hwmon"


class HwmonAttr(Attr):
    @property
    def file(self):
        return os.path.join(self.sensor.path, "%s%s_%s" % (self.sensor.type,
                                                           self.sensor.num,
                                                           self.name))


class MinAttr(HwmonAttr):
    name = "min"


class MaxAttr(HwmonAttr):
    name = "max"


class CritAttr(HwmonAttr):
    name = "crit"


class CritAlarmAttr(HwmonAttr):
    name = "crit_alarm"


class BeepAttr(HwmonAttr):
    name = "beep"


class AlarmAttr(HwmonAttr):
    name = "alarm"


class OffsetAttr(HwmonAttr):
    name = "offset"


class CapMaxAttr(HwmonAttr):
    name = "cap_max"


class CapMinAttr(HwmonAttr):
    name = "cap_min"


class CapAttr(HwmonAttr):
    name = "cap"


class RequestedAttr(HwmonAttr):
    name = "requested"


class HwmonSensor(Sensor):
    def __init__(self, sens_path, sens_type, sens_num, suffix="_input"):
        self.path = sens_path
        self.type = sens_type
        self.num = sens_num
        self.suffix = suffix
        self.dtype = Hwmon.hwmon_inputs[self.type]["dtype"]
        self.unit = Hwmon.hwmon_inputs[self.type]["unit"]
        self.scale = Hwmon.hwmon_inputs[self.type]["factor"] or 1
        self.value = None
        self.file = os.path.join(self.path, "%s%s%s" % (sens_type, sens_num, suffix))
        self.name = f"{self.type}{self.num}"
        self.attrs = []
        label = os.path.join(self.path, "%s%s_%s" % (self.type, self.num, "label"))
        if os.path.exists(label):
            self.name = f"{self.name} ({tools.parsefile(label)})"


class Hwmon(Collection):
    hwnames = {}
    hwmon_inputs = {
        "in": {"unit": "V", "factor": 1000, "suffix": "_input", "dtype": float},
        "curr": {"unit": "A", "factor": 1000, "suffix": "_input", "dtype": float},
        "fan": {"unit": "RPM", "factor": 1, "suffix": "_input", "dtype": float},
        "temp": {"unit": "C", "factor": 1000, "suffix": "_input", "dtype": float},
        "power": {"unit": "W", "factor": 1000000, "suffix": "_input", "dtype": float},
        "power": {"unit": "W", "factor": 100000, "suffix": "_average", "dtype": float},
        "freq": {"unit": "Mhz", "factor": 100000, "suffix": "_input", "dtype": float},
        "pwm": {"unit": "%", "factor": 2.55, "suffix": "", "dtype": float},
        "intrusion": {"unit": "", "factor": None, "suffix": "_alarm", "dtype": bool},
    }
    attrs = [MinAttr, MaxAttr, CritAttr, CritAlarmAttr, BeepAttr, AlarmAttr,
             OffsetAttr, CapAttr, CapMaxAttr, CapMinAttr, RequestedAttr]

    def __init__(self, path):
        self.path = path
        self.name = tools.parsefile(os.path.join(self.path, "name"))
        self.hwname = self._hwname(self.path)

    def _hwname(self, source):
        if source in Hwmon.hwnames:
            return Hwmon.hwnames[source]

        # try to get vendor and product id
        ids = []
        for path in [os.path.join(source, "device", "vendor"), os.path.join(source, "device", "device")]:
            pid = tools.parsefile(path)
            if pid:
                ids.append(pid.replace("0x", ""))

        # if vid, pid is found
        if len(ids) == 2:
            for pciid in tools.pciids:
                rgx = "\n%s\s\s(.+?)\n.+?\n\t%s\s\s(.+?)\n" % (ids[0], ids[1])
                match = re.search(rgx, pciid, re.DOTALL)
                if match:
                    Hwmon.hwnames[source] = "%s:%s" % (match.group(1), match.group(2))
                    return Hwmon.hwnames[source]
            Hwmon.hwnames[source] = None

    def __iter__(self):
        sensors = []
        for fname in os.listdir(self.path):
            for sens_type in Hwmon.hwmon_inputs:
                suffix = Hwmon.hwmon_inputs[sens_type]["suffix"]
                sensor = re.search("%s([0-9]+)%s$" % (sens_type, suffix), fname)
                if sensor:
                    sens_num = int(sensor.group(1))
                    sensors.append((sens_type, sens_num, suffix))
        for sens_type, sens_num, suffix in sorted(sensors):
            sensor = HwmonSensor(self.path, sens_type, sens_num, suffix)
            for attrCls in self.attrs:
                attr = attrCls(sensor)
                if attr.map():
                    sensor.attrs.append(attr)
            yield sensor

    def __repr__(self):
        printable = "%s (%s)" % (self.name, self.path)
        if self.hwname:
            printable += " %s" % self.hwname
        return printable


def Collections():
    hwmons = []
    for hwmon in os.listdir(hwmon_dir):
        hwmons.append(Hwmon(os.path.join(hwmon_dir, hwmon)))
    return sorted(hwmons, key=attrgetter("name"))
