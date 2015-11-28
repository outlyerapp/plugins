#!/usr/bin/env python
import subprocess
import sys

"""
The zpool command needs to be run as root. Paste this into the bottom of /etc/sudoers

dataloop ALL=(ALL) NOPASSWD: sudo /sbin/zpool get -H -p all

"""
metrics = {'size': 'bytes',
           'capacity': 'percent', 
           'health': 'string', 
           'free': 'bytes', 
           'allocated': 'bytes', 
           'freeing': 'bytes', 
           'fragmentation': 'percent', 
           'leaked': 'bytes'}


cmd = "sudo /sbin/zpool get -H -p all"
cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)

zpool = {}

def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)

def _bytes_to_tb(num):
    return round(float(num) / 1024 / 1024 / 1024 / 1024, 2)
    
for line in cmd_output.splitlines():
    data = line.split('\t')
    name = data[0]
    for k, v in metrics.iteritems():
        if data[1] in k:
            if v == 'bytes':
                zpool[name + '.' + data[1]] = data[2] + 'B'
                zpool[name + '.' + data[1] + '_gb'] = str(_bytes_to_gb(data[2])) + 'GB'
                zpool[name + '.' + data[1] + '_tb'] = str(_bytes_to_tb(data[2])) + 'TB'
            else:
                zpool[name + '.' + data[1]] = data[2]

fail_message = "Failed! "
success_message = "OK |"
perf_data = " "
status = True

for path, metric in zpool.iteritems():
    if 'health' in path:
        if metric != 'ONLINE':
            fail_message += path + ' '
            status = False
    perf_data += path + '=' + metric + ';;;; '

if status:
    print success_message + perf_data
    sys.exit(0)
else:
    print fail_message + '|' + perf_data
    sys.exit(2)
