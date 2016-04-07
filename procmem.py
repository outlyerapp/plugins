#!/usr/bin/env python
import sys
import psutil

# change the command to match the full path of the executable
command = '/usr/lib/ddb/erts-7.2/bin/beam.smp'


def _bytes_to_mb(num):
    return round(float(num) / 1024 / 1024, 2)


def _bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)

try:
    perf_data = {}
    for p in psutil.process_iter():
        if command in p.cmdline():
            mem_info_ex = p.memory_info_ex()
            perf_data['rss'] = mem_info_ex.rss
            perf_data['rss_mb'] = _bytes_to_mb(mem_info_ex.rss)
            perf_data['rss_gb'] = _bytes_to_gb(mem_info_ex.rss)
            perf_data['vms'] = mem_info_ex.vms
            perf_data['vms_mb'] = _bytes_to_mb(mem_info_ex.vms)
            perf_data['vms_gb'] = _bytes_to_gb(mem_info_ex.vms)
            perf_data['shared'] = mem_info_ex.shared
            perf_data['shared_mb'] = _bytes_to_mb(mem_info_ex.shared)
            perf_data['shared_gb'] = _bytes_to_gb(mem_info_ex.shared)
            perf_data['text'] = mem_info_ex.text
            perf_data['lib'] = mem_info_ex.lib
            perf_data['data'] = mem_info_ex.data
            perf_data['dirty'] = mem_info_ex.data

    output = "OK | "
    for k, v in perf_data.iteritems():
        output += "%s=%s;;;; " % (k.lower(), v)
    print output
    sys.exit(0)

except Exception, e:
    print "Plugin Failed!: %s" % e
    sys.exit(2)