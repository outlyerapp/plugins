#!/usr/bin/env python

import os
import re
from datetime import datetime
import time
import sys

"""
Reads through an nginx access log file and extracts a count of http status codes.

To enable calculation of response times you need to enable more logging in Nginx. Add this to nginx.conf to the http block:

        log_format timed_combined '$remote_addr - $remote_user [$time_local] '
                                  '"$request" $status $body_bytes_sent '
                                  '"$http_referer" "$http_user_agent" '
                                  '"$request_time"';

Then in your log directives use time_combined. For example:

access_log /var/log/nginx/yourdomain.com.access.log timed_combined;

"""

LOGFILE = '/var/log/nginx/access.log'

combined = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
timed_combined = '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$request_time"'
timezone = time.strftime("%z",time.localtime()) 
start_time = datetime.now()

status_codes = {'2xx': 0,
                '3xx': 0,
                '4xx': 0,
                '5xx': 0}
times = {
    'count': 0,
    'total': 0,
    'max': 0
}

def reverse_read(fname, separator=os.linesep):
    with file(fname) as f:
        f.seek(0, 2)
        fsize = f.tell()
        r_cursor = 1
        while r_cursor <= fsize:
            a_line = ''
            while r_cursor <= fsize:
                f.seek(-1 * r_cursor, 2)
                r_cursor += 1
                c = f.read(1)
                if c == separator and a_line:
                    r_cursor -= 1
                    break
                a_line += c
            a_line = a_line[::-1]
            yield a_line

for line in reverse_read(LOGFILE):
    regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', timed_combined))
    m = re.match(regex, line)
    if not m:
        regex = ''.join('(?P<' + g + '>.*?)' if g else re.escape(c) for g, c in re.findall(r'\$(\w+)|(.)', combined))
        m = re.match(regex, line)
    data = m.groupdict()

    line_time = datetime.strptime(data['time_local'], '%d/%b/%Y:%H:%M:%S '+ timezone)
    delta = start_time - line_time
    if delta.seconds < 30:
        code = data['status']
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
        if 'request_time' in data.iterkeys():
            time_taken = data['request_time']
            if 'min' not in times.iterkeys():
                times['min'] = time_taken
            times['count'] += 1
            times['total'] += float(time_taken)
            if time_taken > times['max']:
                times['max'] = time_taken
            if time_taken < times['min']:
                times['min'] = time_taken
    else:
        break

            
message = "OK | "
for k, v in status_codes.iteritems():
    message += "%s=%s;;;; " % (k, v)

if times['count'] > 0:
    message += "avg_time=%0.2fs;;;; " % (float(times['total'])/float(times['count']))

if 'request_time' in data.iterkeys():
    message += "max_time=%0.2fs;;;; min_time=%0.2fs;;;;" % (float(times['max']), float(times['min']))

print message
sys.exit(0)
