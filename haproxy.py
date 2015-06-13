#!/usr/bin/env python
"""
Add the following line to haproxy.cfg under the global section (and restart haproxy):

stats socket /var/lib/haproxy/stats.sock level admin
"""
import sys
import re
import socket
try:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/var/lib/haproxy/stats.sock")
    s.send('show stat \n')
    data = s.recv(32768)
    s.close()
except:
    print "Plugin Failed!"
    sys.exit(2)

stats = data.split()

data = {}
headerlist = []
blist = []
flist = []

_digits = re.compile('\d')


def contains_digits(d):
    return bool(_digits.search(d))

for line in stats:
    if 'pxname' in line:
        headers = line.split(',')
        for header in headers:
            headerlist.append(header)
        data['headers'] = headerlist

    if 'BACKEND' in line:
        stat = line.split(',')
        for item in stat:
            blist.append(item)
        name = 'backend.' + blist[0]
        data[name] = blist

    if 'FRONTEND' in line:
        stat = line.split(',')
        for item in stat:
            flist.append(item)
        name = 'frontend.' + flist[0]
        data[name] = flist

perf_data = {}
for k, v in data.iteritems():
    if 'backend' in k:
        p = 0
        for header in headerlist:
            metric_path = "%s.%s" % (k, header)
            if contains_digits(v[p]):
                perf_data[metric_path] = v[p]
            p += 1
    if 'frontend' in k:
        p = 0
        for header in headerlist:
            metric_path = "%s.%s" % (k, header)
            if contains_digits(v[p]):
                perf_data[metric_path] = v[p]
            p += 1

output = "OK | "
for k, v in perf_data.iteritems():
    output += "%s=%s;;;; " % (k, v)

print output
sys.exit(0)
