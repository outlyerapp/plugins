#!/usr/bin/env python
import os
import sys
import time
import re
import argparse
import psutil

# Default values are percentages

MEMORY_CRIT = 100
MEMORY_WARN = 100

CPU_CRIT = 100
CPU_WARN = 100

DISK_CRIT = 98
DISK_WARN = 95


def _get_counter_increment(before, after):
    """ function to calculate network counters """  
    value = after - before
    if value > 0: return value
    for boundry in [1<<16, 1<<32, 1<<64]:
        if (value + boundry) > 0:
            return value + boundry

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
    rx = "%dKps" % ((_get_counter_increment(rx_before, rx_after) / 1024) / space_apart)
    sx = "%dKps" % ((_get_counter_increment(sx_before, sx_after) / 1024) / space_apart)
    net = dict(net_download=rx, net_upload=sx)
    return net

def check_load():
    """returns a dict of load num : value"""

    try:
        load = os.getloadavg()
        load_avg = {}
        load_avg['load_1_min'] = str(load[0])
        load_avg['load_5_min'] = str(load[1])
        load_avg['load_15_min'] = str(load[2])

        return load_avg
    
    except:
        return {}

def check_netio():
    """returns a dict of net io counters : value"""
    try:
        return psutil.net_io_counters()._asdict()

    except:
        return {} 


def check_cputime():
    """ returns a dict of cpu type : value """
    try:
        return psutil.cpu_times()._asdict()

    except:
        return {}

def main():

    dicts = [check_disks(), check_memory(), check_cpu(), check_net(), check_load(), check_netio(), check_cputime()]

    perf = ""
    result = {}
    for d in dicts:
        for k, v in d.iteritems():
            if v:
                if "critical" in str(v) or "warning" in str(v):
                    result[k] = v
                else:
                    perf += "%s=%s;;;; " % (k, v)

    error_message = ""
    for v in result.itervalues():
        if "critical" in str(v):
            error_message += v

    warning_message = ""
    for v in result.itervalues():
        if "warning" in str(v):
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
