'''
Created on Mar 3, 2023

@author: boogie
'''
import os
import re

pciids = []
for p in ("/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids"):
    try:
        pciids.append(open(p).read())
    except Exception:
        pass


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
