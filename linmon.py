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
from __future__ import print_function

import os
import re
from operator import itemgetter


inputs = {
    "in": {"unit": "V", "factor": 1000},
    "curr": {"unit": "A", "factor": 1000},
    "fan": {"unit": "RPM", "factor": 1},
    "temp": {"unit": "C", "factor": 1000},
    "power": {"unit": "W", "factor": 1000000},
    "pwm": {"unit": "%", "factor": 2.55},
}

attrs = {
    "min": "float",
    "max": "float",
    "crit": "float",
    "crit_alarm": "float",
    "beep": "float",
    "alarm": "float",
    "label": "str"
    }

sens_re = ")|(?:".join(inputs.keys())
sens_re = "((?:%s))([0-9]+)_input$" % sens_re

sensors = {}


def parsefile(fpath):
    if os.path.exists(fpath):
        try:
            with open(fpath) as f:
                data = f.read().replace("\n", "")
                try:
                    return float(data)
                except Exception:
                    return data
        except Exception:
            pass


def addsensor(source, sens_type, sens_num, sens_val, sens_attrs):
    if source not in sensors:
        sensors[source] = []
    sensors[source].append((sens_type, sens_num, sens_val, sens_attrs))


def attributes(file_path, sensor_type, sensor_num):
    sens_attrs = {}
    for sens_attr in attrs:
        attr_path = os.path.join(file_path, sensor_type + sensor_num + "_" + sens_attr)
        attr_val = parsefile(attr_path)
        if attr_val is not None:
            sens_attrs[sens_attr] = attr_val
    return sens_attrs


def readsensor(filepath, sens_type, sens_num, suffix="_input"):
    sensfile = os.path.join(filepath, sens_type + sens_num + suffix)
    if sens_type in inputs:
        sens_val = parsefile(sensfile)
        if sens_val is not None:
            sens_attrs = attributes(filepath, sens_type, sens_num)
            addsensor(filepath, sens_type, sens_num, sens_val, sens_attrs)


def collect():
    for subdir, _, files in os.walk("/sys"):
        for fname in files:
            sensor = re.search(sens_re, fname)
            suffix = "_input"
            if not sensor:
                sensor = re.search("((?:pwm))([0-9]+)$", fname)
                suffix = ""
            if sensor:
                sens_type = sensor.group(1)
                sens_num = sensor.group(2)
                readsensor(subdir, sens_type, sens_num, suffix)


def report():
    for source in sensors:
        source_name = parsefile(os.path.join(source, "name"))
        if source_name:
            print("%s (%s)" % (source_name, source))
        else:
            print("%s:" % source)
        for stype, snum, sval, sattrs in sorted(sensors[source], key=itemgetter(0, 1)):
            scfg = inputs[stype]
            sname = "%s%s" % (stype, snum)
            if stype == "pwm":
                sval = "%.2f%s (%i) " % (sval / scfg["factor"], scfg["unit"], sval)
            else:
                sval = "%.2f%s" % (sval / scfg["factor"], scfg["unit"])
            sattr_txts = []
            for sattr in sattrs:
                sattr_val = sattrs[sattr]
                if sattr == "label":
                    sname = "%s (%s)" % (sname, sattr_val)
                    continue
                elif attrs[sattr] == "float":
                    sattr_val = "%.2f" % (sattr_val / scfg["factor"])
                sattr_txts.append("%s: %s%s" % (sattr,
                                                sattr_val,
                                                scfg["unit"]))
            if len(sattr_txts):
                sval += " (%s)" % ", ".join(sattr_txts)
            print("    %s: %s" % (sname, sval))


collect()
report()
