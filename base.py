#!/usr/bin/env python
import os
import sys
import time
import re
import psutil
import subprocess

if os.name == 'nt':
    import wmi
    c = wmi.WMI()


def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)


def _get_counter_increment(before, after):
    value = after - before
    if value >= 0: return value
    for boundary in [1<<16, 1<<32, 1<<64]:
        if (value + boundary) > 0:
            return value + boundary


def check_disks():
    disk_usage = {}
    for partition in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in partition.opts or partition.fstype == '':
                continue
        if 'Volumes' in partition.mountpoint:
            continue
        if 'libc.so' in partition.mountpoint:
            continue
        usage = psutil.disk_usage(partition.mountpoint)
        disk = re.sub(" ", "_", partition.mountpoint).replace(':', '').replace('\\', '').lower()
        disk_usage['disk.' + disk + '.percent_used'] = "%d%%" % int(usage.percent)
        disk_usage['disk.' + disk + '.percent_free'] = "%d%%" % int(100 - usage.percent)
        disk_usage['disk.' + disk + '.free'] = "%sb" % usage.free
        disk_usage['disk.' + disk + '.used'] = "%sb" % usage.used
        used_gb = _bytes_to_gb(usage.used)
        disk_usage['disk.' + disk + '.used_gb'] = "%sGb" % used_gb
        free_gb = _bytes_to_gb(usage.free)
        disk_usage['disk.' + disk + '.free_gb'] = "%sGb" % free_gb
    return disk_usage


def check_memory():
    memory = "%d%%" % int(psutil.virtual_memory().percent)
    swap = "%d%%" % int(psutil.swap_memory().percent)
    memory_used = dict(memory=memory, swap=swap)
    return memory_used


def check_cpu():
    cpu = "%d%%" % int(psutil.cpu_percent(interval=5))
    cpu_used = dict(cpu=cpu)
    return cpu_used


def check_net():
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
    cores = psutil.NUM_CPUS
    load_avg = {}
    if os.name == 'nt':
        cpu_queue_length = sum([int(cpu.ProcessorQueueLength) for cpu in c.Win32_PerfRawData_PerfOS_System()])
        load_avg['load_1_min'] = str(cpu_queue_length)
    else:
        load = os.getloadavg()
        load_avg['load_1_min'] = str(load[0])
        load_avg['load_5_min'] = str(load[1])
        load_avg['load_15_min'] = str(load[2])
    load_avg['load_fractional'] = float(load_avg['load_1_min']) / int(cores)
    return load_avg


def check_netio():
    net_map = {}
    # total net counters
    net_all = psutil.net_io_counters()._asdict()
    for k, v in net_all.iteritems():
        net_map['network.'+ k] = v
    # per net io counters
    net_per_nic = psutil.net_io_counters(pernic=True)
    for device, details in net_per_nic.iteritems():
        for k, v in net_per_nic[device]._asdict().iteritems():
            net_map["network." + device.replace(' ', '_').lower() + "." + k] = v
    return net_map


def check_cputime():
    cpu_map = {}
    # total cpu counters
    cputime_all = psutil.cpu_times_percent()._asdict()
    for k, v in cputime_all.iteritems():
        cpu_map['cpu.'+ k] = v
    # per cpu counters
    cputime_per_cpu = psutil.cpu_times_percent(percpu=True)
    for i in range(len(cputime_per_cpu)):
        for k, v in cputime_per_cpu[i]._asdict().iteritems():
            cpu_map['cpu.%s.%s' % (i, k)] = v
    cpu_map['cpu.cores'] = psutil.cpu_count(logical=True)
    # get the cpu speed on linux
    if sys.platform == 'linux2':
        command = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(command, shell=True).strip()
        for line in all_info.split("\n"):
            if "model name" in line:
                speed = re.sub(".*model name.*:", "", line, 1).split(' ')[-1]
                cpu_map['cpu.speed'] = speed
    return cpu_map


def check_diskio():
    dm = False
    disk_map = {}
    # total io counters
    diskio_all = psutil.disk_io_counters()
    for k, v in diskio_all._asdict().iteritems():
        disk_map["disk." + k] = v
    # per disk io counters
    diskio_per_disk = psutil.disk_io_counters(perdisk=True)
    for device, details in diskio_per_disk.iteritems():
        for k, v in diskio_per_disk[device]._asdict().iteritems():
            disk_map["disk." + device.lower() + "." + k] = v
    # per windows volume counters
    if os.name == 'nt':
        for disk in c.Win32_PerfFormattedData_PerfDisk_LogicalDisk():
            if len(disk.Name) < 3:
                ln = disk.Name.replace(':', '').lower()
                disk_map["disk." + ln + ".reads_per_sec"] = disk.DiskReadsPerSec
                disk_map["disk." + ln + ".writes_per_sec"] = disk.DiskWritesPerSec
                disk_map["disk." + ln + ".transfers_per_sec"] = disk.DiskTransfersPerSec
                disk_map["disk." + ln + ".current_disk_queue_length"] = disk.CurrentDiskQueueLength
    # check for any device mapper partitions
    for partition in psutil.disk_partitions():
        if '/dev/mapper' in partition.device:
            dm = True
    # per device mapper friendly name io counters
    if dm:
        device_mapper = {}
        for name in os.listdir('/dev/mapper'):
            path = os.path.join('/dev/mapper', name)
            if os.path.islink(path):
                device_mapper[os.readlink(os.path.join('/dev/mapper', name)).replace('../', '')] = name
        for device, details in diskio_per_disk.iteritems():
            for k, v in diskio_per_disk[device]._asdict().iteritems():
                if device in device_mapper:
                    disk_map["disk." + device_mapper[device] + "." + k] = v
    return disk_map


def check_virtmem():
    virt_map = {}
    virtmem = psutil.virtual_memory()._asdict()
    virt_map['vmem.total_gb'] = "%sGb" % _bytes_to_gb(virtmem['total'])
    virt_map['vmem.available_gb'] = "%sGb" % _bytes_to_gb(virtmem['available'])
    virt_map.update(dict(("vmem." + k, v) for k, v in virtmem.items()))
    return virt_map


def check_ctxswitch():
    proc = psutil.Process(os.getpid())
    ctx_switch = proc.get_num_ctx_switches()._asdict()
    return dict(("ctx-switch." + k, v) for k,v in ctx_switch.items())


checks = [
    check_disks,
    check_cpu,
    check_memory,
    check_net,
    check_load,
    check_cputime,
    check_netio,
    check_diskio,
    check_virtmem,
    check_ctxswitch
]

raw_output = {}
for check in checks:
    try:
        raw_output.update(check())
    except Exception, e:
        continue

output = "OK | "
for k, v in raw_output.iteritems():
    output += "%s=%s;;;; " % (k, v)
print output + 'count=1;;;;'

