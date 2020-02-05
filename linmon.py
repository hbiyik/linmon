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


def addsensor(source, *sensor):
    if source not in sensors:
        sensors[source] = []
    sensors[source].append(sensor)


def attribute(source, sensor_type, sensor_num, tag):
    tagpath = os.path.join(source, sensor_type + sensor_num + "_" + tag)
    return parsefile(tagpath)


def readsensor(filepath, sensor):
    sens_type = sensor.group(1)
    sens_num = sensor.group(2)
    if sens_type in inputs:
        sens_val = parsefile(filepath)
        if sens_val is not None:
            addsensor(filepath, sens_type, sens_num, sens_val,
                      attribute(filepath, sens_type, sens_num, "min"),
                      attribute(filepath, sens_type, sens_num, "max"),
                      attribute(filepath, sens_type, sens_num, "alarm"),
                      attribute(filepath, sens_type, sens_num, "beep"),
                      attribute(filepath, sens_type, sens_num, "label"))


def collect():
    for subdir, _, files in os.walk("/sys"):
        for fname in files:
            sensor = re.search("((?:curr)|(?:in)|(?:fan)|(?:temp)|(?:power))([0-9]+)_input$", fname)
            if not sensor:
                sensor = re.search("((?:pwm))([0-9]+)$", fname)
            if sensor:
                filepath = os.path.join(subdir, fname)
                sens_type = sensor.group(1)
                sens_num = sensor.group(2)
                if sens_type in inputs:
                    sens_val = parsefile(filepath)
                    if sens_val is not None:
                        addsensor(subdir, sens_type, sens_num, sens_val,
                                  attribute(subdir, sens_type, sens_num, "min"),
                                  attribute(subdir, sens_type, sens_num, "max"),
                                  attribute(subdir, sens_type, sens_num, "alarm"),
                                  attribute(subdir, sens_type, sens_num, "beep"),
                                  attribute(subdir, sens_type, sens_num, "label"))


def report():
    for source in sensors:
        source_name = parsefile(os.path.join(source, "name"))
        if source_name:
            print("%s (%s)" % (source_name, source))
        else:
            print("%s:" % source)
        for stype, snum, sval, smin, smax, salarm, sbeep, slabel in sorted(sensors[source], key=itemgetter(0, 1)):
            scfg = inputs[stype]
            sname = "%s%s" % (stype, snum)
            if slabel:
                sname = "%s (%s)" % (sname, slabel)
            if stype == "pwm":
                sval = "%.3f%s (%i) " % (sval / scfg["factor"], scfg["unit"], sval)
            else:
                sval = "%.3f%s" % (sval / scfg["factor"], scfg["unit"])
            sattrs = []
            if smin:
                sattrs.append("MIN: %.3f%s" % (smin / scfg["factor"], scfg["unit"]))
            if smax:
                sattrs.append("MAX: %.3f%s" % (smax / scfg["factor"], scfg["unit"]))
            if salarm:
                sattrs.append("ALARM: %.3f%s" % (salarm / scfg["factor"], scfg["unit"]))
            if sbeep:
                sattrs.append("BEEP: %.3f%s" % (sbeep / scfg["factor"], scfg["unit"]))
            if len(sattrs):
                sval += " (%s)" % ", ".join(sattrs)
            print("    %s: %s" % (sname, sval))


collect()
report()
