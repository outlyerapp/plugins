#!/usr/bin/env python
import socket
import sys

HOST = 'localhost'
PORT = 11211


def query_stats():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
        client.send('stats\n')
        resp = client.recv(1024)
        client.close()
        return resp

    except:
        print "Plugin Failed! Unable to connect to %s:%s" % (HOST, PORT)
        sys.exit(2)


def process_response(r):
    stats = {}
    for line in r.split('\n'):
        fields = line.split(' ')
        if fields[0] == "STAT":
            try:
                stat = fields[2].replace('\r', '')
                stats[fields[1]] = stat
            except:
                pass
    return stats


def process_stats(s):
    perf_data = "OK | "
    for k in s:
        perf_data += "%s=%s;;;; " % (k, s[k])
    return perf_data

r = query_stats()
statistics = process_response(r)
print process_stats(statistics)
sys.exit(0)
