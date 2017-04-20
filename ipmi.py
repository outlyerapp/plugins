#!/usr/bin/env python

import sys
import pyghmi
from pyghmi.ipmi import command
from StringIO import StringIO

HOST = '192.168.1.10'
USERNAME = 'ADMIN'
PASSWORD = 'ADMIN'


def sanitize_string(s):
    s = s.lower()
    s = s.replace(' ', '_')
    s = s.replace('-', '_')
    s = s.replace('+', '')
    s = s.replace('.', '_')
    return s


buf = StringIO()
buf.write('OK | ')

try:
    cmd = command.Command(HOST, USERNAME, PASSWORD)
except pyghmi.exceptions.IpmiException as ex:
    print 'WARNING - ' + ex.message
    sys.exit(2)

for sensor in cmd.get_sensor_data():
    if sensor.value:
        type = sanitize_string(sensor.type)
        name = sanitize_string(sensor.name)
        unit = sensor.units
        buf.write('{0}.{1}={2}{3};;;; '.format(type, name, sensor.value, unit))

print buf.getvalue()

