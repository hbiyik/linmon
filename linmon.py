#!/usr/bin/python
"""
 * This file is part of the XXX distribution (https://github.com/xxxx or http://xxx.github.io).
 * Copyright (c) 2015 Liviu Ionescu.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 """
import os
import re
from operator import itemgetter
import sys
import curses
import time

updatetime = None
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    updatetime = float(sys.argv[1])


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

reg_inputs = {"voltage": {"unit": "V", "factor": 1000000, "dtype":float},
              "current": {"unit": "A", "factor": 1000000, "dtype":float}}
 

hwmon_attrs = ["min", "max", "crit", "crit_alarm", "beep", "alarm", "label", "offset", "cap", "cap_max", "cap_min", "requested"]
reg_props = ["status", "state", "num_users"]
hwnames = {}

hwmon_dir = "/sys/class/hwmon"
regulator_dir = "/sys/class/regulator"

sensors = {}
pciids = []

REG_DEVNAME = "regulators"


def init():
    for p in ("/usr/share/misc/pci.ids", "/usr/share/hwdata/pci.ids"):
        try:
            pciids.append(open(p).read())
        except Exception:
            pass


def parsefile(fpath, callback=float):
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                data = f.read().replace("\n", "")
                try:
                    return callback(data)
                except Exception:
                    return data
        except Exception:
            pass


def addsensor(devname, sens_type, sens_num, sens_val, sens_attrs, reg_type=None):
    if devname not in sensors:
        sensors[devname] = []
    sensors[devname].append((sens_type, sens_num, sens_val, sens_attrs, reg_type))


def attributes(file_path, sensor_type, sensor_num):
    sens_attrs = {}
    for sens_attr in hwmon_attrs:
        attr_path = os.path.join(file_path, sensor_type + sensor_num + "_" + sens_attr)
        attr_val = parsefile(attr_path)
        if attr_val is not None:
            sens_attrs[sens_attr] = attr_val
    return sens_attrs


def readsensors(filepath, sens_type, sens_num, suffix="_input"):
    sensfile = os.path.join(filepath, sens_type + sens_num + suffix)
    if sens_type in hwmon_inputs:
        sens_val = parsefile(sensfile, hwmon_inputs[sens_type]["dtype"])
        if sens_val is not None:
            sens_attrs = attributes(filepath, sens_type, sens_num)
            source_name = parsefile(os.path.join(filepath, "name"))
            if source_name:
                devname = "%s (%s)" % (source_name, filepath)
            else:
                devname = filepath
            if hwname(filepath):
                devname = hwname(filepath)
            addsensor(devname, sens_type, sens_num, sens_val, sens_attrs)


def readregulators():
    for subdir, _fname in iterdirs(regulator_dir):
        regtype = parsefile(os.path.join(subdir, "type"), str)
        if regtype:
            attrs = {}
            dataname = "microamps" if regtype == "current" else "microvolts"
            regval = parsefile(os.path.join(subdir, dataname), int)
            if not regval:
                continue
            for regattr in hwmon_attrs:
                regattrval = parsefile(os.path.join(subdir, regattr + "_" + dataname), int)
                if regattrval:
                    attrs[regattr] = regattrval
            for regprop in reg_props:
                regpropval = parsefile(os.path.join(subdir, regprop), str)
                if regpropval:
                    attrs[regprop] = regpropval
            uevent = parsefile(os.path.join(os.path.join(subdir, "uevent")), str)
            devname = re.search("OF_FULLNAME=(.+?)OF_COMPATIBLE", uevent)
            devname = devname.group(1) if devname is not None else subdir
            devname = devname.split("/")[-1]
            regname = parsefile(os.path.join(os.path.join(subdir, "name")), str)
            if regname:
                regname = "%s (%s)" % (devname, regname)
            else:
                regname = devname
            addsensor(REG_DEVNAME, regname, "", regval, attrs, regtype)
    

def iterdirs(rootdir):
    for _root in os.listdir(rootdir):
        classdir = os.path.abspath(os.path.join(hwmon_dir, os.readlink(os.path.join(rootdir, _root))))
        for subdir, _, files in os.walk(classdir):
            yield subdir, files

def collect():
    for subdir, files in iterdirs(hwmon_dir):
        for fname in files:
            for sens_type in hwmon_inputs:
                suffix = hwmon_inputs[sens_type]["suffix"]
                sensor = re.search("%s([0-9]+)%s$" % (sens_type, suffix), fname)
                if sensor:
                    sens_num = sensor.group(1)
                    readsensors(subdir, sens_type, sens_num, suffix)
                    break
    readregulators()


def hwname(source):
    if source in hwnames:
        return hwnames[source]
    ids = []
    for path in [os.path.join(source, "device", "vendor"), os.path.join(source, "device", "device")]:
        pid = parsefile(path)
        if pid:
            ids.append(pid.replace("0x", ""))

    if len(ids) == 2:
        for pciid in pciids:
            rgx = "\n%s\s\s(.+?)\n.+?\n\t%s\s\s(.+?)\n" % (ids[0], ids[1])
            match = re.search(rgx, pciid, re.DOTALL)
            if match:
                hwnames[source] = "%s:%s" % (match.group(1), match.group(2))
                return hwnames[source]
        hwnames[source] = None


def report():
    log = ""
    for source in sorted(sensors):
        log += "%s\n" % source
        for stype, snum, sval, sattrs, regtype in sorted(sensors[source], key=itemgetter(0, 0)):
            if regtype is None:
                dtype = hwmon_inputs[stype]["dtype"]
                dfactor = hwmon_inputs[stype]["factor"]
                dunit = hwmon_inputs[stype]["unit"]
            else:
                dtype = float
                dfactor = reg_inputs[regtype]["factor"]
                dunit = reg_inputs[regtype]["unit"]
            sname = "%s%s" % (stype, snum)
            if dtype in [int, float]:
                sval = "%.2f" % (sval / dfactor)
            sval = "%s%s" % (sval, dunit)
            sattr_txts = []
            for sattr in sattrs:
                if sattr == "label":
                    sname = "%s (%s)" % (sname, sattrs[sattr])
                    continue
                elif sattr in reg_props:
                    sattr_txts.append("%s: %s" % (sattr, sattrs[sattr]))
                    continue

                if dtype in [int, float]:
                    sattr_val = "%.2f" % (sattrs[sattr] / dfactor)
                else:
                    sattr_val = sattrs[sattr]
                sattr_txts.append("%s: %s%s" % (sattr,
                                                sattr_val,
                                                dunit))
            if len(sattr_txts):
                sval += " (%s)" % ", ".join(sattr_txts)
            log += "    %s: %s\n" % (sname, sval)
    return log


init()

if updatetime is not None:
    screen = curses.initscr()
    screen.erase()
    screen.refresh()
    try:
        while True:
            y, x = screen.getmaxyx()
            screen.resize(y, x)
            t1 = time.time()
            sensors = {}
            collect()
            screen.insstr(1, 0, report())
            runtime = time.time() - t1
            screen.refresh()
            if runtime < updatetime:
                time.sleep(updatetime - runtime)
            screen.addstr(0, 0, "Refresh Time: %.3f seconds\n" % (time.time() - t1))
            screen.refresh()
    finally:
        curses.nocbreak()
        screen.keypad(0)
        curses.echo()
        curses.endwin()
else:
    collect()
    sys.stdout.write(report())
