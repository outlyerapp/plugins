#!/usr/bin/env python
import sys
import re
import socket

"""
Requirements:

Add the following line to haproxy.cfg under the global section (and restart haproxy):

stats socket /var/run/haproxy.sock user dataloop group root level operator

"""

try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/var/run/haproxy.sock")
    s.send('show stat \n')
    data = s.recv(32768)
    s.close()
except:
    print "connection failure"
    sys.exit(2)

stats = data.split()

data = {}
headerlist = []

_digits = re.compile('\d')

def contains_digits(d):
    return bool(_digits.search(d))

for line in stats:
    if 'pxname' in line:
        headers = line.split(',')
        for header in headers:
            headerlist.append(header)

    elif len(line) > 1:
        blist = []
        stat = line.split(',')
        for item in stat:
            blist.append(item)
        name = blist[0] + '.' + blist[1]
        data[name] = blist

perf_data = {}
for k, v in data.iteritems():
    p = 0
    for header in headerlist:
        metric_path = "%s.%s" % (k, header)
        if contains_digits(v[p]):
            perf_data[metric_path] = v[p]
        p += 1

output = "OK | "
for k, v in perf_data.iteritems():
    output += "%s=%s;;;; " % (k.lower(), v)

print output
sys.exit(0)

