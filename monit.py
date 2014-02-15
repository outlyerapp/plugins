#!/usr/bin/env python

import sys
import subprocess

"""
    This plugin checks health services in 'monit summary' output.
    If any has 'Not monitored' status, then plugin returns CRITICAL.
"""
binary = 'monit'


def end(status, message):
    if status == "OK":
        print "OK: %s" % message
        sys.exit(0)
    elif status == "CRITICAL":
        print "CRITICAL: %s" % message
        sys.exit(2)
    else:
        print "UNKNOWN: %s" % message
        sys.exit(3)

try:
    cmd = subprocess.Popen([binary, "summary"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
except Exception, (errmsg):
    end("UNKNOWN", "%s: %s" % (binary, errmsg))
else:
    col = False
    for line in cmd.stdout:
        if "ot monitored" in line:
            if "Process" in line:
                if col:
                    col = col + ", " + line.split('\'')[1]
                elif not col:
                    col = line.split('\'')[1]
    if col:
        end("CRITICAL", "processes not monitored: " + col)
    elif not col:
        end("OK", "all processess are monitored")
