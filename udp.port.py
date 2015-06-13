#!/usr/bin/env python
import socket
import sys

host = ''
port = 

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect((host, port))
    s.shutdown(2)
    up = True
except:
    up = False
s.close()

if up:
    print "success"
    sys.exit(0)
else:
    print "sonnection failure"
    sys.exit(2)

