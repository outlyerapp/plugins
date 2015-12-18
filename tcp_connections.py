#!/usr/bin/env python
import sys
import psutil

PORT = 22

cmap = {'in': 0,
        'out': 0 }

for c in psutil.net_connections(kind='inet'):
    if len(c.laddr) > 0 and c.laddr[1] == PORT and c.status == 'ESTABLISHED':
        cmap['in'] += 1
    if len(c.raddr) > 0 and c.raddr[1] == PORT and c.status == 'ESTABLISHED':
        cmap['out'] += 1

print "OK | connections_in=%d;;;; connections_out=%d;;;;" % (cmap['in'], cmap['out'])
sys.exit(0)