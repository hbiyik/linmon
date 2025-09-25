'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from liblinmon import Collection, Sensor, Attr, tools


pci_dir = "/sys/bus/pci/devices"


class PciAttr(Attr):
    def __init__(self, sensor, attr, value, name=None):
        self.sensor = sensor
        self.name = name or attr
        self._value = self.human(value)

    def human(self, value):
        match = re.search(r"([0-9\.]+?) GT/s PCIe", value, re.IGNORECASE)
        if match is None:
            return value
        pcies = {"2.5": "PCIe 1.0",
                 "5.0": "PCIe 2.0",
                 "8.0": "PCIe 3.0",
                 "16.0": "PCIe 4.0",
                 "32.0": "PCIe 5.0",
                 "64.0": "PCIe 6.0",
                 "128.0": "PCIe 7.0",}
        return pcies.get(match.group(1), value)

    @property
    def value(self):
        return self._value


class PciSenor(Sensor):
    def __init__(self, basepath, vendor, device):
        self.file = None
        self.attrs = []
        self.name = device
        names = tools.pcilookup(vendor, device)
        if names:
            self.value = names[1]
        else:
            self.value = "Unknown"
        attrs = {"current_link_speed": "LaneSpeed",
                 "current_link_width": "Lanes",
                 "max_link_speed": "MaxLaneSpeed",
                 "max_link_width": "MaxLanes"}
        for attr, attrname in attrs.items():
            attrpath = os.path.join(basepath, attr)
            if not os.path.exists(attrpath):
                continue
            attrval = tools.parsefile(attrpath)
            if not attrval:
                continue
            self.attrs.append(PciAttr(self, attr, attrval, attrname))


class PciColl(Collection):
    def __init__(self, vendor, devices):
        self.vendor = vendor
        names = tools.pcilookup(vendor, None)
        if names:
            name = names[0]
        else:
            name = "unknown"
        self.name = ":".join([vendor, name])
        self.devices = devices

    def __repr__(self):
        return self.name

    def __iter__(self):
        for basepath, device in self.devices:
            vendor = tools.parsefile(os.path.join(basepath, "vendor"))
            if not self.name:
                self.name = ":".join("pci", self.vendor, vendor)
            sensor = PciSenor(basepath, vendor, device)
            yield sensor


def Collections():
    colls = []
    if not os.path.exists(pci_dir):
        return colls

    vendors = {}
    for pcidev in os.listdir(pci_dir):
        basepath = os.path.join(pci_dir, pcidev)
        if not os.path.exists(os.path.join(basepath, "current_link_speed")):
            continue
        vendor = tools.parsefile(os.path.join(basepath, "vendor"))
        if vendor is None:
            continue
        device = tools.parsefile(os.path.join(basepath, "device"))
        if device is None:
            continue
        if vendor not in vendors:
            vendors[vendor] = []
        vendors[vendor].append([basepath, device])

    if not vendors:
        return colls

    for vendor, devices in vendors.items():
        colls.append(PciColl(vendor, devices))

    return colls
