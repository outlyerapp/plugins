#!/usr/bin/env python
import sys
import subprocess
import re
import platform

'''
This script pings a list of addresses an returns the status and round trip stats for each
'''

addresses = ["microsoft.com", "google.com"]
num_pings = 2

metrics = {}

def ping_linux(i, q):
    address = q
    cmd = "ping -c %i %s" % (num_pings, address)
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError:
        metrics[address + '.status'] = 2
    else:
        address = address.replace('.', '_')
        metrics[address + '.status'] = 0
        cmd_output = filter(None, cmd_output.split('\n'))[-1].split('=')[1].replace(' ms', '')
        rtt = cmd_output.split('/')
        rtt = [x.strip(' ') for x in rtt]
        metrics[address + '.min'] = rtt[0] + 'ms'
        metrics[address + '.avg'] = rtt[1] + 'ms'
        metrics[address + '.max'] = rtt[2] + 'ms'
        metrics[address + '.stddev'] = rtt[3] + 'ms'
    return metrics

def ping_windows(i, q):
    regex = r'\n[\s]{4}Minimum\s=\s(?P<min>[0-9]+(ms|s)),\sMaximum\s=\s(?P<max>[0-9]+(ms|s)),\sAverage\s=\s(?P<avg>[0-9]+(ms|s))'
    address = q
    cmd = "ping -n %i %s" % (num_pings, address)
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError:
        metrics[address + '.status'] = 2
    else:
        address = address.replace('.', '_')
        metrics[address + '.status'] = 0
        #print cmd_output
        processed_results = re.search(regex, cmd_output, re.M)
        #print processed_results
        metrics[address + '.min'] = str(processed_results.group('min'))
        metrics[address + '.avg'] = str(processed_results.group('avg'))
        metrics[address + '.max'] = str(processed_results.group('max'))
    return metrics

for address in addresses:
    if platform.system() == "Windows":
        metrics = ping_windows(num_pings, address)
    if platform.system() == "Linux":
        metrics = ping_linux(num_pings, address)

output = "OK | "
exit_code = 0
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '
    if k.endswith('.status'):
        if v == 2:
            exit_code = 2

print output
sys.exit(exit_code)
