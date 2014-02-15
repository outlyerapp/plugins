#!/usr/bin/env python

import sys
import psutil
import socket
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM

"""
    Nagios script that takes a list of allowed ports and alerts if any others are opened
"""

allowed_port_list = [
    22,
    80,
    443,
    3306
]

AD = "-"
AF_INET6 = getattr(socket, 'AF_INET6', object())
proto_map = {(AF_INET, SOCK_STREAM): 'tcp',
             (AF_INET6, SOCK_STREAM): 'tcp6',
             (AF_INET, SOCK_DGRAM): 'udp',
             (AF_INET6, SOCK_DGRAM): 'udp6'}


def get_listening_ports():
    ports = []
    for p in psutil.process_iter():
        name = '?'
        try:
            name = p.name
            cons = p.get_connections(kind='inet')
        except psutil.AccessDenied:
            pass
        else:
            for c in cons:
                if c.status is "LISTEN":
                    ports.append(c.local_address[1])
    return list(set(ports))

listening_ports = get_listening_ports()

not_allowed = list(set(listening_ports) - set(allowed_port_list))

if len(not_allowed) > 0:
    print "Critical! port(s) %s listening" % not_allowed
    sys.exit(2)
else:
    print "OK"
    sys.exit(0)
