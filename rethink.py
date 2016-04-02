#!/usr/bin/env python
import rethinkdb as r
import sys
from socket import gethostname


rt_host = 'localhost'
rt_port = 28015

metrics = {}
server_stats = []
table_stats = []
replica_stats = []
size_metrics = ['metadata_bytes', 'garbage_bytes', 'data_bytes', 'in_use_bytes', 'preallocated']
hostname = gethostname()
out_str = 'OK |'


def flatten(prefix, d):
    prefix = prefix.replace(" ", "_")
    if type(d) == dict:
        for k, v in d.iteritems():
            k = k.replace(" ", "_")
            if isinstance(v, int):
                metrics[prefix + '.' + k] = v
                if k in size_metrics:
                    convert_sizes_from_bytes(prefix + '.' + k,v)
            elif isinstance(v, dict):
                for a, b in d.iteritems():
                    flatten(prefix, b)
            elif isinstance(v, list):
                for i in v:
                    for b in i['value']:
                        new_key = prefix + '.' + k + '.' + i['key'] + '.' + b
                        new_key = new_key.replace(" ", "_")
                        metrics[new_key] = i['value'][b]
            else:
                metrics[prefix + '.' + k] = v


def convert_sizes_from_bytes(k, v):
    kb = k.replace('_bytes', '_kb')
    mb = k.replace('_bytes', '_mb')
    gb = k.replace('_bytes', '_gb')
    metrics[kb] = v / 1024
    metrics[mb] = v / 1024 / 1024
    metrics[gb] = v / 1024 / 1024 / 1024


def iterate_stats(stats_array):
    metrics_array = []
    for _stats in stats_array:
        for k, v in _stats.iteritems():
            k = k.replace(" ", "_")
            if isinstance(v, int):
                metrics[k] = v
                if k in size_metrics:
                    convert_sizes_from_bytes(k, v)
            elif isinstance(v, list):
                if k == 'id':
                    new_key = (v[0] + '_' + k)
                    metrics[new_key] = v[1]
            elif isinstance(v, dict):
                flatten(k, v)
            else:
                metrics[k] = v
        metrics_array.append(metrics.copy())
    return metrics_array


def is_digit(d):
    if isinstance(d, bool):
        return False
    elif isinstance(d, int) or isinstance(d, float):
        return True
    return False

try:
    conn = r.connect(host=rt_host, port=rt_port).repl()

except Exception, e:
    print 'No database connection could be established: %s' % e
    sys.exit(2)

try:
    conn = r.connect(host=rt_host, port=rt_port).repl()
    for stats in r.db("rethinkdb").table("stats").run():
        if 'server' in stats['id']:
            server_stats.append(stats)
        if 'table' in stats['id']:
            table_stats.append(stats)
        if 'table_server' in stats['id']:
            replica_stats.append(stats)
    conn.close()

except Exception, e:
    print 'Rethink Query Failed: %s' % e
    sys.exit(2)
    
server_metrics = iterate_stats(server_stats)
table_metrics = iterate_stats(table_stats)
replica_metrics = iterate_stats(replica_stats)

for stats in server_metrics:
    host = stats['server']
    if host == hostname:
        for key, value in stats.iteritems():
            if is_digit(value):
                out_str += '%s=%s;;;; ' % (key, value)

for stats in table_metrics:
    db = stats['db']
    table = stats['table']
    for key, value in stats.iteritems():
        if is_digit(value):
            out_str += '%s.%s.%s=%s;;;; ' % (db, table, key, value)
        
for stats in replica_metrics:
    host = stats['server']
    db = stats['db']
    table = stats['table']
    if host == hostname:
        for key, value in stats.iteritems():
            if is_digit(value):
                out_str += '%s.%s.replica.%s=%s;;;; ' % (db, table, key, value)

print out_str
sys.exit(0)
