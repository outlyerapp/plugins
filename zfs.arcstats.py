#!/usr/bin/env python

import sys

arcstats_file = '/proc/spl/kstat/zfs/arcstats'

try:
    with open(arcstats_file, 'r') as f:
        garbage = f.readline()
        header = f.readline()
        stats = f.read()
        stats_lines = stats.split('\n')


except Exception as E:
    print "CRITICAL - failed to parse arcstats: %s" % E
    sys.exit(2)

def bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)

gbstats = ['c', 'c_max']

message = "OK | "

for line in stats_lines:
    fields = line.split()
    if len(fields) > 0:
        for stat in gbstats:
            if stat == fields[0]:
                message += "%s=%sgb;;;; " % (fields[0] + '_GB', bytes_to_gb(fields[2]))
        message += "%s=%s;;;; " % (fields[0], fields[2])

print message