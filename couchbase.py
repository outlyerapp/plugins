#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth

"""

Update the USER and PASSWORD variables below.

"""

USER = ''
PASSWORD = ''

URL = 'http://localhost:8091/pools/default'
auth = HTTPBasicAuth(USER, PASSWORD)
try:
    resp = requests.get(URL, auth=auth, timeout=60).json()
except:
    print "Plugin Failed! Unable to connect to %s" % URL
    sys.exit(2)


def flatten(structure, key="", path="", flattened=None):
    if flattened is None:
        flattened = {}
    if type(structure) not in (dict, list):
        flattened[((path + ".") if path else "") + key] = structure
    elif isinstance(structure, list):
        for i, item in enumerate(structure):
            flatten(item, "%d" % i, path + "." + key, flattened)
    else:
        for new_key, value in structure.items():
            flatten(value, new_key, path + "." + key, flattened)
    return flattened


def bytes_to_gb(num):
    return round(float(num) / 1024 / 1024 / 1024, 2)


success_message = "OK | "
failure_message = "FAILED! | "
perf_data = ""
healthy = True

for node in resp['nodes']:
    if node['status'] != 'healthy':
        healthy = False

for k, v in flatten(resp).iteritems():
    if type(v) is int or type(v) is float:
        metric_path =  k.lower().replace('..', '')
        perf_data += metric_path + '=' + str(v) + ';;;; '
        if 'storagetotals' in metric_path:
            perf_data += metric_path + '_gb=' + str(bytes_to_gb(v)) + 'GB;;;; '

if healthy:
    print success_message + perf_data
    sys.exit(0)
else:
    print failure_message + perf_data
    sys.exit(2)
