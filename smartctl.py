#!/usr/bin/env python

import subprocess
import sys

"""
NOTE:
The smartctl command needs to be run as root. 
Paste this into the bottom of /etc/sudoers:

dataloop ALL=(ALL) NOPASSWD: /sbin/smartctl
"""

status = "OK"
disks = []

try:
    cmd = "sudo smartctl --scan-open"
    cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    for line in cmd_output.splitlines():
        (dev, _, dtype) = line.split(' ')[0:3]
        disks.append((dev, dtype))

    for (dev, dtype) in disks:
        cmd = "sudo smartctl --device=%s --health %s" % (dtype, dev)
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        for line in cmd_output.splitlines():
            if "test result" in line and "PASSED" not in line:
                status = "CRITICAL"
                break
except subprocess.CalledProcessError:
    status = "WARNING"
    
print status

