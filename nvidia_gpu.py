#!/usr/bin/env python
import subprocess
import sys

metrics_list = [
    "fan.speed",
    "memory.total",
    "memory.used",
    "memory.free",
    "utilization.gpu",
    "utilization.memory",
    "ecc.errors.corrected.volatile.device_memory",
    "ecc.errors.corrected.volatile.register_file",
    "ecc.errors.corrected.volatile.l1_cache",
    "ecc.errors.corrected.volatile.l2_cache",
    "ecc.errors.corrected.volatile.texture_memory",
    "ecc.errors.corrected.volatile.total",
    "ecc.errors.corrected.aggregate.device_memory",
    "ecc.errors.corrected.aggregate.register_file",
    "ecc.errors.corrected.aggregate.l1_cache",
    "ecc.errors.corrected.aggregate.l2_cache",
    "ecc.errors.corrected.aggregate.texture_memory",
    "ecc.errors.corrected.aggregate.total",
    "ecc.errors.uncorrected.volatile.device_memory",
    "ecc.errors.uncorrected.volatile.register_file",
    "ecc.errors.uncorrected.volatile.l1_cache",
    "ecc.errors.uncorrected.volatile.l2_cache",
    "ecc.errors.uncorrected.volatile.texture_memory",
    "ecc.errors.uncorrected.volatile.total",
    "ecc.errors.uncorrected.aggregate.device_memory",
    "ecc.errors.uncorrected.aggregate.register_file",
    "ecc.errors.uncorrected.aggregate.l1_cache",
    "ecc.errors.uncorrected.aggregate.l2_cache",
    "ecc.errors.uncorrected.aggregate.texture_memory",
    "ecc.errors.uncorrected.aggregate.total",
    "retired_pages.single_bit_ecc.count",
    "retired_pages.double_bit.count",
    "retired_pages.pending",
    "temperature.gpu",
    "power.management",
    "power.draw",
    "power.limit",
    "enforced.power.limit",
    "power.default_limit",
    "power.min_limit",
    "power.max_limit",
    "clocks.current.graphics",
    "clocks.current.sm",
    "clocks.current.memory",
    "clocks.applications.graphics",
    "clocks.applications.memory",
    "clocks.default_applications.graphics",
    "clocks.default_applications.memory",
    "clocks.max.graphics",
    "clocks.max.sm",
    "clocks.max.memory"]

def is_digit(d):
    try:
        float(d)
    except ValueError:
        return False
    return True

try:
    query_string = '--query-gpu=' + ','.join(map(str, metrics_list))
    result_list = subprocess.check_output(['/usr/bin/nvidia-smi', query_string, '--format=csv,noheader,nounits']).split(',')
    output = "OK | "
    for i, metric in enumerate(metrics_list):
        if '[Not Supported]' not in result_list[i] and is_digit(result_list[i]) :
            output += metric + '=' + result_list[i].strip() + ';;;; '
    print output
    sys.exit(0)

except Exception, e:
    print "FAIL! %s" % e
    sys.exit(2)