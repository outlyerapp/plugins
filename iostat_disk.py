#!/usr/bin/env python
import os
import re
import subprocess
import sys

'''This plugin requires iostat. On Ubuntu run apt-get install sysstat'''

status = {}

def get_disk_names():
    cmd = "cat /proc/partitions|grep -v major"
    
    try:
        resp = subprocess.check_output(cmd, stderr=subprocess.PIPE,shell=True)
        
    except:
        print "sar execution failure"
        sys.exit(2)

    partitions = resp.split('\n')
    i = 0
    disk_names = []
    for partition in partitions:
        if partition:
            disk_info = partition.split()
            disk_names.append(disk_info[3])
    return disk_names        
    
def get_dev_stats(my_disk):
    cmd = "/usr/bin/iostat -xtc 1 2 | grep -v avg | grep %s |head -2|tail -1" % my_disk

    try:
        resp = subprocess.check_output(cmd, stderr=subprocess.PIPE,shell=True)
    except:
        print "iostat execution failure"
        sys.exit(2)

    metric_list = resp.split('\n')
    field = 0
    for line in metric_list:
        if line:
            metric = line.split()
            for v in metric:
                field += 1
                if field == 1:
                    status['disk'] = v
                if field == 4:
                    status['reads_per_sec'] = v
                elif field == 5:
                    status['writes_per_sec'] = v
                elif field == 6:
                    status['read_kb_per_sec'] = v
                elif field == 7:
                    status ['write_kb_per_sec'] = v
                elif field == 9:
                    status ['avg_queue_size'] = v
                elif field == 11:
                    status ['avg_wait_read'] = v
                elif field == 12:
                    status ['avg_wait_write'] = v
                elif field == 14:
                    status ['pct_utilized'] = v
    return status

disks = []
disks = get_disk_names()
disk_data = "OK | "
for my_disk in disks:
    result = get_dev_stats(my_disk)
    for k, v in result.iteritems():
        disk_data += "%s_%s=%s;;;; " % (my_disk, k, v)
print disk_data
sys.exit(0)
