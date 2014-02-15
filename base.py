#!/usr/bin/env python
import os
import sys
import time
import re
import argparse
import psutil

# Default values are percentages

MEMORY_CRIT = 80
MEMORY_WARN = 70

CPU_CRIT = 90
CPU_WARN = 80

DISK_CRIT = 98
DISK_WARN = 95

parser = argparse.ArgumentParser(description='Dataloop Base Plugin')
parser.add_argument('-d', '--disk', metavar='disk', action="store",
                    default="%d,%d" % (DISK_WARN, DISK_CRIT), nargs=2, help='<warning> <critical>')
parser.add_argument('-m', '--memory', metavar='memory', action="store",
                    default="%d,%d" % (MEMORY_WARN, MEMORY_CRIT), nargs=2, help='<warning> <critical>')
parser.add_argument('-c', '--cpu', metavar='cpu', action="store",
                    default="%d,%d" % (CPU_WARN, CPU_CRIT), nargs=2, help='<warning> <critical>')
args = parser.parse_args()


def check_disks():
    """returns a dict of mount point : % used"""
    disk_usage = {}
    try:
        for partition in psutil.disk_partitions(all=False):
            if os.name == 'nt':
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
            if 'Volumes' in partition.mountpoint:
                continue
            if 'libc.so' in partition.mountpoint:
                continue

            usage = psutil.disk_usage(partition.mountpoint)
            disk = re.sub(" ", "_", partition.mountpoint)
            disk_usage[disk] = "%d%%" % int(usage.percent)

            if int(usage.percent) > DISK_CRIT:
                disk_usage[disk + "_status"] = disk + " is critical! "

            if DISK_CRIT > int(usage.percent) > DISK_WARN:
                disk_usage[disk + "_status"] = disk + " is warning! "
    except OSError:
        pass

    return disk_usage


def check_memory():
    """returns a dict of memory type : % used"""

    memory = "%d%%" % int(psutil.virtual_memory().percent)
    swap = "%d%%" % int(psutil.swap_memory().percent)
    memory_used = dict(memory=memory, swap=swap)

    if int(psutil.virtual_memory().percent) > MEMORY_CRIT:
        memory_used["memory_status"] = "memory is critical! "

    if MEMORY_CRIT > int(psutil.virtual_memory().percent) > MEMORY_WARN:
        memory_used["memory_status"] = "memory is warning! "

    return memory_used


def check_cpu():
    """returns a dict of cpu type : % used"""

    cpu = "%d%%" % int(psutil.cpu_percent(interval=1))
    cpu_used = dict(cpu=cpu)

    if int(psutil.cpu_percent(interval=1)) > CPU_CRIT:
        cpu_used["cpu_status"] = "cpu is critical! "

    if CPU_CRIT > int(psutil.cpu_percent(interval=1)) > CPU_WARN:
        cpu_used["cpu_status"] = "cpu is warning! "

    return cpu_used


def check_net():
    """returns a dict of network stats in kps"""
    space_apart = 1
    rx_before = psutil.net_io_counters().bytes_recv
    sx_before = psutil.net_io_counters().bytes_sent
    time.sleep(space_apart)
    rx_after = psutil.net_io_counters().bytes_recv
    sx_after = psutil.net_io_counters().bytes_sent
    rx = "%dKps" % (((rx_after - rx_before) / 1024) / space_apart)
    sx = "%dKps" % (((sx_after - sx_before) / 1024) / space_apart)
    net = dict(net_download=rx, net_upload=sx)
    return net


def main():

    dicts = [check_disks(), check_memory(), check_cpu(), check_net()]

    perf = ""
    result = {}
    for d in dicts:
        for k, v in d.iteritems():

            if "critical" in v or "warning" in v:
                result[k] = v
            else:
                perf += "%s=%s;;;; " % (k, v)

    error_message = ""
    for v in result.itervalues():
        if "critical" in v:
            error_message += v

    warning_message = ""
    for v in result.itervalues():
        if "warning" in v:
            warning_message += v

    if len(error_message) > 0:
        print error_message + warning_message + "| " + perf
        sys.exit(2)

    if len(warning_message) > 0:
        print error_message + warning_message + "| " + perf
        sys.exit(1)

    print "OK | " + perf
    sys.exit(0)

main()