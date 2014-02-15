#!/usr/bin/env python

import threading
import socket
import time
import getopt
import sys


def usage():
    print "Usage: %s -H <server> [-w <warning>] [-c <critical>] -p \"<list of opened ports>\"" % (sys.argv[0])

try:
    optlist, args = getopt.getopt(sys.argv[1:], 'H:w:c:p:h')
except getopt.GetoptError:
    usage()
    sys.exit(2)

server = 'localhost'
warning = 10 # default value
critical = 30 # default value
ports = '3000'

for opt, arg in optlist:
    if opt == '-h':
        usage()
        sys.exit(2)
    if opt == '-H':
        server = arg
    if opt == '-p':
        ports = arg
    if opt == '-w':
        warning = int(arg)
    if opt == '-c':
        critical = int(arg)

if ports is None or server is None:
    print "Server or ports not entered."
    usage()
    sys.exit(2)


def check_port(server, port):
    sock = socket.socket()
    if sock.connect_ex((server, port)) == 0:
        ports_opened.append(port)
    else:
        ports_closed.append(port)
    sock.close()


s = time.time()
threads = []
ports_opened = []
ports_closed = []

ports = ports.split()

for port in ports:
    t = threading.Thread(target=check_port,args=(server,int(port)))
    t.start()
    threads.append(t)
for t in threads:
    t.join()

time_value = time.time() - s

if ports_closed:
    msg = "Opened ports: %s; not opened but expected %s."% (ports_opened, ports_closed)
    exit_code = 2
else:
    msg = "All ports %s opened." % ports_opened
    exit_code = 0


if time_value > critical:
    msg += " Time is CRITICAL %s" % time_value
    exit_code = 2

if time_value > warning:
    msg += " Time is WARNING %s" % time_value
    if exit_code == 0:
        exit_code = 1

print msg
sys.exit(exit_code)
