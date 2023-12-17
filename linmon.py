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
import sys
from liblinmon import collectors
from liblinmon import tui

updatetime = None
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    updatetime = float(sys.argv[1])

if False:
    import pydevd
    pydevd.settrace("192.168.2.10")


def report(start=0, end=float("inf")):
    index = 0
    for colname, collections in collectors.registry.items():
        for collection in collections:
            sensors = list(collection)
            if sensors:
                if index >= start and index < end:
                    yield f"{colname}:{repr(collection)}"
                elif index >= end:
                    break
                index += 1
                for sensor in sensors:
                    sensor.read()
                    name = sensor.name
                    if sensor.label:
                        name = f"{sensor.name} ({sensor.label})"
                    if isinstance(sensor.value, float):
                        sensorstr = f"{name}: {sensor.value:.2f}{sensor.unit}"
                    else:
                        sensorstr = f"{name}: {sensor.value}{sensor.unit}"
                    extra = []
                    for attr in sensor.attrs:
                        if isinstance(attr.value, float):
                            extra.append(f"{attr.name}: {attr.value:.2f}{attr.unit}")
                        else:
                            extra.append(f"{attr.name}: {attr.value}{attr.unit}")
                    if extra:
                        sensorstr += " (%s)" % ", ".join(extra)
                    if index >= start and index < end:
                        yield sensorstr
                    elif index >= end:
                        break
                    index += 1
                if index >= start and index < end:
                    yield ""
                elif index >= end:
                    break
                index += 1


if updatetime is not None:
    screen = tui.Screen(report, updatetime)
    screen.run()
else:
    for line in report():
        print(line)
