'''
Created on Mar 3, 2023

@author: boogie
'''
import os
import re

PCIIDDB = {}
USBIDDB = {}

for db, paths in ((PCIIDDB, ("/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids")),
                  (USBIDDB, ("/usr/share/misc/usb.ids", "/usr/share/hwdata/usb.ids"))):
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            vid = None
            for line in f.readlines():
                try:
                    line = line.decode()
                except UnicodeDecodeError:
                    continue
                matchvid = re.search(r"(^[0-9a-f]{4,4})\s\s(.+?)\n", line)
                if matchvid is not None:
                    vid = matchvid.group(1).lower()
                    vname = matchvid.group(2)
                    if vid not in db:
                        db[vid] = [vname, {}]
                    continue
                if vid is None:
                    continue
                pidmatch = re.search(r"^\t([0-9a-f]{4,4})\s\s(.+?)\n", line)
                if pidmatch is None:
                    continue
                pid = pidmatch.group(1).lower()
                pname = pidmatch.group(2)
                db[vid][1][pid] = pname


def buslookup(vendor, device, db):
    if not vendor:
        return
    if vendor.startswith("0x"):
        vendor = vendor[2:]
    if device and device.startswith("0x"):
        device = device[2:]
    vendor = vendor.lower()
    if device is not None:
        device = device.lower()
    if vendor not in db:
        return
    if device is None:
        return db[vendor][0], None
    if device not in db[vendor][1]:
        return
    return db[vendor][0], db[vendor][1][device]


def pcilookup(vendor, device):
    return buslookup(vendor, device, PCIIDDB)


def usblookup(vendor, device):
    return buslookup(vendor, device, USBIDDB)


def iterdirs(rootdir):
    for basedir, subdirs, files in os.walk(rootdir):
        for subdir in subdirs:
            subdir = os.path.join(basedir, subdir)
            if not os.path.islink(subdir):
                for _ in iterdirs(subdir):
                    yield _
        for fname in files:
            yield basedir, fname


def parsefile(fpath, trim=True):
    try:
        with open(fpath, "rb") as f:
            content = f.read().decode()
            if trim:
                content = content.replace("\n", "").replace("\x00", "")
            return content
    except Exception:
        pass


def iterdrivers(rootdir, rgx):
    if os.path.exists(rootdir):
        for sub in os.listdir(rootdir):
            subdir = os.path.join(rootdir, sub)
            compat = os.path.join(rootdir, sub, "of_node", "compatible")
            if os.path.exists(compat):
                compatstr = parsefile(compat)
                if re.search(rgx, compatstr):
                    yield subdir, compatstr


def _parseuevent(path, rgx, trim=True):
    uevent_path = os.path.join(path, "uevent")
    if not os.path.exists(uevent_path):
        return
    uevent = parsefile(uevent_path, trim=trim)
    devname = re.search(rgx, uevent)
    if not devname:
        return
    return devname.group(1)


def parseuevent_name(path):
    return _parseuevent(path, r"OF_FULLNAME=(.+?)OF_COMPATIBLE")


def parseuevent_driver(path):
    return _parseuevent(path, r"DRIVER=(.+?)\n", False)
