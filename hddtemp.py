#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
import re
import StringIO

DEVICES_TO_CHECK = "/dev/sd[a-z]"
WARNING_THRESHOLD = 50
CRITICAL_THRESHOLD = 60

"""
NOTE:
The hddtemp command needs to be run as root. 
Paste this into the bottom of /etc/sudoers:

dataloop ALL=(ALL) NOPASSWD: /usr/sbin/hddtemp
"""

status = "OK"
exitcode = 0
buf = StringIO.StringIO()
buf.write(' | ')

try:
    cmd = "sudo hddtemp --unit C " + DEVICES_TO_CHECK
    cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    for line in cmd_output.splitlines():
        m = re.match(r'^/dev/(?P<dev>\w+): .*: (?P<temp>\d+)°C$', line)
        if m:
            dev = m.group('dev')
            temp = int(m.group('temp'))
            buf.write('{0}={1};;;; '.format(dev, temp))
            if temp >= CRITICAL_THRESHOLD and exitcode < 2:
                status = 'CRITICAL - device {0} is at {1}°C'.format(dev, temp)
                exitcode = 2
            elif temp >= WARNING_THRESHOLD and exitcode < 1:
                status = 'WARNING - device {0} is at {1}°C'.format(dev, temp)
                exitcode = 1

except subprocess.CalledProcessError as ex:
    status = "WARNING - " + ex.message
    exitcode = 1

print status + buf.getvalue()
sys.exit(exitcode)
