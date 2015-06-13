#!/usr/bin/env python
import socket
import subprocess
import sys
import psutil

NODE_TOOL = '/usr/local/cassandra-1/bin/nodetool'
HOST = 'localhost'


def is_digit(d):
    try:
        float(d)
    except ValueError:
        return False
    return True


def get_cfstats():
    try:
        p = subprocess.Popen([NODE_TOOL, "-h", HOST, "cfstats"], stdout=subprocess.PIPE)
        return p.stdout
    except:
        print "Plugin Failed! Cassandra is down"
        sys.exit(2)


def parse(f):
    values = {}
    keyspace = None
    while True:
        line = f.readline()
        if not line:
            break
        s = line.split()
        if not s:
            continue
        if s[0].startswith('Keyspace'):
            keyspace = s[1]
            parse_keyspace(f, values, keyspace)
        if s[0].startswith('Column'):
            cf = s[2]
            parse_cf(f, values, keyspace, cf)
    return values


def parse_keyspace(f, values, keyspace):
    values[keyspace] = {'global': {}}
    for i in xrange(0, 5):
        line = f.readline()
        s = line.split()
        add_value(s, values[keyspace]['global'])


def parse_cf(f, values, keyspace, cf):
    values[keyspace][cf] = {}
    while True:
        line = f.readline()
        if not line:
            break
        s = line.split()
        if not s:
            break
        s = line.split()
        add_value(s, values[keyspace][cf])


def add_value(s, values):
    for i, k in enumerate(s):
        s[i] = k.replace('(', '').replace(')', '')

    if s[-1] == 'ms.':
        s = s[:-1]

    if s[-1] == 'NaN':
        s[-1] = '0'

    if is_digit(s[-1]):
        k = '_'.join(s[0:-1]).replace(':', '')
        values[k] = s[-1]


f = get_cfstats()
dataset = parse(f)
output = "OK | "

for root, context in dataset.iteritems():
    for counter, values in context.iteritems():
        for k, v in values.iteritems():
            output += root + '.' + counter + '.' + k + '=' + v + ';;;; '

print output

