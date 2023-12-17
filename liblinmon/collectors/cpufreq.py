'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from operator import itemgetter
from liblinmon import Collection, Sensor, Attr, tools


cpu_dir = "/sys/devices/system/cpu"


class CpuFreqAttr(Attr):
    @property
    def file(self):
        return os.path.join(self.sensor.path, self.path)


class InfoMaxAttr(CpuFreqAttr):
    name = "max"
    path = "cpuinfo_max_freq"


class InfoMinAttr(CpuFreqAttr):
    name = "min"
    path = "cpuinfo_min_freq"


class ScaleMaxAttr(CpuFreqAttr):
    name = "max"
    path = "scaling_max_freq"


class ScaleMinAttr(CpuFreqAttr):
    name = "min"
    path = "scale_min_freq"


class RelatedAttr(CpuFreqAttr):
    name = "related"
    path = "related_cpus"

    @property
    def unit(self):
        return ""

    @property
    def value(self):
        return tools.parsefile(self.file)


class AffectedAttr(RelatedAttr):
    name = "affected"
    path = "affected_cpus"


class ScaleDrvAttr(RelatedAttr):
    name = "driver"
    path = "scaling_driver"


class AvaileGovsAttr(RelatedAttr):
    name = "available"
    path = "scaling_available_governors"


class ScaleAvailAttr(CpuFreqAttr):
    name = "available"
    path = "scaling_available_frequencies"

    @property
    def unit(self):
        return ""

    @property
    def value(self):
        freqs = []
        for freq in tools.parsefile(self.file).split(" "):
            if freq.isdigit():
                freqs.append(str(int(int(freq)/self.sensor.scale)))
        return " ".join(freqs)


class CpuSensor(Sensor):
    def __init__(self, path, name, file, scale, unit, datatype=None):
        self.name = name
        self.path = path
        self.file = os.path.join(path, file)
        self.scale = scale
        self.unit = unit
        self.attrs = []


class CpuFreqColl(Collection):
    sensors = [(CpuSensor, "freq", "cpuinfo_cur_freq", 1000, "Mhz", [InfoMinAttr, InfoMaxAttr, RelatedAttr, AffectedAttr], None),
               (CpuSensor, "scaling_freq", "scaling_cur_freq", 1000, "Mhz", [ScaleMinAttr, ScaleMaxAttr, ScaleDrvAttr, ScaleAvailAttr], None),
               (CpuSensor, "governor", "scaling_governor", None, "", [AvaileGovsAttr], None)]

    def __init__(self, cores):
        self.cores = cores

    def __repr__(self):
        return "cpufreq"

    def __iter__(self):
        for sensorCls, name, file, scale, unit, attrs, dtype in self.sensors:
            for sub, _num, core_path in sorted(self.cores, key=itemgetter(1)):
                freq = os.path.join(core_path, file)
                if os.path.exists(freq):
                    sensor = sensorCls(core_path, f"{sub}_{name}", file, scale, unit, dtype)
                    for attrCls in attrs:
                        attr = attrCls(sensor)
                        if attr.map():
                            sensor.attrs.append(attr)
                    yield sensor


def Collections():
    cores = []
    for sub in os.listdir(cpu_dir):
        core_path = os.path.join(cpu_dir, sub, "cpufreq")
        if os.path.exists(os.path.join(core_path, "cpuinfo_cur_freq")):
            num = int(re.search("cpu([0-9]+)", sub).group(1))
            cores.append([sub, num, core_path])
    return [CpuFreqColl(cores)]
