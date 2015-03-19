#!/usr/bin/env python
import psutil
import sys

PROCESS_NAME = "syslogd"

for process in psutil.process_iter():
    if process.name() == PROCESS_NAME:
        print "OK - %s is up and running" % PROCESS_NAME
        sys.exit(0)

print "CRITICAL! Process %s is not running" % PROCESS_NAME
sys.exit(2)
