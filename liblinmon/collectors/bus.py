'''
Created on Mar 2, 2023

@author: boogie
'''
import os
import re
from liblinmon import Collection, Sensor, Attr, tools


UNKNOWN = "Unknown"
PCIE_RGX = r"([0-9\.]+?) GT/s PCIe"
PCIE_HUMAN = {"2.5": "PCIe 1.0",
              "5.0": "PCIe 2.0",
              "8.0": "PCIe 3.0",
              "16.0": "PCIe 4.0",
              "32.0": "PCIe 5.0",
              "64.0": "PCIe 6.0",
              "128.0": "PCIe 7.0",}
USB_RGX = r"([0-9]+)"
USB_HUMAN = {"12": "USB1.1",
             "480": "USB2.0",
             "5000": "USB3.0G1",
             "10000": "USB3.0G2"}


class PciBus:
    name = "pci"
    rootdir = "/sys/bus/pci/devices/"
    speedfile = "current_link_speed"
    vendorfile = "vendor"
    devicefile = "device"
    idlookup = tools.pcilookup
    attrs = (("current_link_speed", "LaneSpeed", PCIE_RGX, PCIE_HUMAN),
             ("current_link_width", "Lanes", None, None),
             ("max_link_speed", "MaxLaneSpeed", PCIE_RGX, PCIE_HUMAN),
             ("max_link_width","MaxLanes", None, None))


class UsbBus(PciBus):
    name = "usb"
    rootdir = "/sys/bus/usb/devices/"
    speedfile = "speed"
    vendorfile = "idVendor"
    devicefile = "idProduct"
    idlookup = tools.usblookup
    attrs = (("speed", "Speed", USB_RGX, USB_HUMAN),)


class BusAttr(Attr):
    def __init__(self, sensor, value, attr, name, rgx, human):
        self.sensor = sensor
        self.name = name or attr
        self._value = self.human(value, rgx, human) if rgx and human else value

    def human(self, value, rgx, human):
        match = re.search(rgx, value, re.IGNORECASE)
        if match is None:
            return value
        return human.get(match.group(1), value)

    @property
    def value(self):
        return self._value


class BusSensor(Sensor):
    def __init__(self, bus, basepath, vendor, device):
        self.file = None
        self.attrs = []
        self.name = device
        names = bus.idlookup(vendor, device)
        if names:
            self.value = names[1]
        else:
            self.value = UNKNOWN
        for attr, attrname, rgx, human in bus.attrs:
            attrpath = os.path.join(basepath, attr)
            if not os.path.exists(attrpath):
                continue
            attrval = tools.parsefile(attrpath)
            if not attrval:
                continue
            self.attrs.append(BusAttr(self, attrval, attr, attrname, rgx, human))


class BusColl(Collection):
    def __init__(self, bus, vendor, devices):
        self.bus = bus
        self.vendor = vendor
        names = bus.idlookup(vendor, None)
        name = names[0] if names else UNKNOWN
        self.name = ":".join([bus.name, vendor, name])
        self.devices = devices

    def __repr__(self):
        return self.name

    def __iter__(self):
        for basepath, device in self.devices:
            vendor = tools.parsefile(os.path.join(basepath, self.bus.vendorfile))
            sensor = BusSensor(self.bus, basepath, vendor, device)
            yield sensor


def Collections():
    colls = []
    for bus in [PciBus, UsbBus]:
        if not os.path.exists(bus.rootdir):
            continue

        vendors = {}
        for busdev in os.listdir(bus.rootdir):
            basepath = os.path.join(bus.rootdir, busdev)
            if not os.path.exists(os.path.join(basepath, bus.speedfile)):
                continue
            vendor = tools.parsefile(os.path.join(basepath, bus.vendorfile))
            if vendor is None:
                continue
            device = tools.parsefile(os.path.join(basepath, bus.devicefile))
            if device is None:
                continue
            if vendor not in vendors:
                vendors[vendor] = []
            vendors[vendor].append([basepath, device])

        if not vendors:
            continue

        for vendor, devices in vendors.items():
            colls.append(BusColl(bus, vendor, devices))

    return colls
