#!/usr/bin/env python

"""
Reads through an nginx access log file and extracts a count of http status
codes.
Calculates the average response time.
Returns the slowest response time.

An offset is stored so only new log lines are read and metrics calculated on that
"""

import re
import os
import sys

TMPDIR = '/opt/dataloop/tmp'
TMPFILE = 'dl-nginx-metrics'
LOGFILE = '/var/log/nginx/access.log'

status_codes={'2xx': 0,
              '3xx': 0,
              '4xx': 0,
              '5xx': 0}
times = {}
times['count'] = 0
times['total'] = 0
times['max'] = 0
offset = 0

def tmp_file():
    # Ensure the dataloop tmp dir is available
    if not os.path.isdir(TMPDIR):
        os.makedirs(TMPDIR)
    if not os.path.isfile(TMPDIR + '/' + TMPFILE):
        os.mknod(TMPDIR + '/' + TMPFILE)


def get_offset():
    with open(TMPDIR + '/' + TMPFILE, 'r') as off:
        try:
            offset = int(off.read())
        except:
            # unable to read offset file
            offset = 0
    return offset

def write_offset(offset):
    with open(TMPDIR + '/' + TMPFILE, 'w') as off:
        off.write("%s" % offset)

# Flow
tmp_file()

# Get the last know log file read position
# to mitigate logrotation, if the file is smaller than offset, read the whol
# log file again
position = get_offset()
file_size = os.stat(LOGFILE).st_size
if file_size < position:
    position = 0

with open(LOGFILE) as fp:

    if position > 0:
        fp.seek(position)

    for line in fp.xreadlines():

        code = line.split(' ')[8]
        if re.match('^[0-9]', code):
            if code not in status_codes.keys():
                status_codes[code] = 1
            else:
                status_codes[code] += 1
            if code.startswith('2'):
                status_codes['2xx'] += 1
            if code.startswith('3'):
                status_codes['3xx'] += 1
            if code.startswith('4'):
                status_codes['4xx'] += 1
            if code.startswith('5'):
                status_codes['5xx'] += 1                


        time_taken = line.split(' ')[9]
        if re.match('^[0-9]', time_taken):
            if 'min' not in times.iterkeys():
                times['min'] = int(time_taken)
            times['count'] += 1
            times['total'] += int(time_taken)
            if int(time_taken) > int(times['max']):
                times['max'] = int(time_taken)
            if int(time_taken) < int(times['min']):
                times['min'] = int(time_taken)

    write_offset(fp.tell())
    fp.close()


# emit lots of lovely metrics:
message = "OK | "
for k,v in status_codes.iteritems():
    message += "%s=%s;;;; " % (k,v)

if times['count'] > 0:
    message += "avg_time=%sms;;;; " % (int(times['total'])/int(times['count']))

message += "max_time=%sms;;;; min_time=%sms;;;;" % (times['max'], times['min'])

print message
sys.exit(0)
