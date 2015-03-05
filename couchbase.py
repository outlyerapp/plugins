#!/usr/bin/env python
import sys
import requests
from requests.auth import HTTPBasicAuth

USER = ''
PASSWORD = ''

output = "OK | "
exit_status = 0
auth = HTTPBasicAuth(USER, PASSWORD)
perf_data = {}

try:
    default = requests.get('http://localhost:8091/pools/default', auth=auth).json()
except:
    print "connection failed!"
    sys.exit(2)

# The top level metrics
perf_data['maxbucketcount'] = default['maxBucketCount']
perf_data['rebalance_success'] = default['counters']['rebalance_success']
perf_data['rebalance_start'] = default['counters']['rebalance_start']
perf_data['hdd_storage.free'] = default['storageTotals']['hdd']['free']
perf_data['hdd_storage.total'] = default['storageTotals']['hdd']['total']
perf_data['hdd_storage.quota_total'] = default['storageTotals']['hdd']['quotaTotal']
perf_data['hdd_storage.used_by_data'] = default['storageTotals']['hdd']['usedByData']
perf_data['hdd_storage.used'] = default['storageTotals']['hdd']['used']
perf_data['ram.used'] = default['storageTotals']['ram']['used']
perf_data['ram.quota_used'] = default['storageTotals']['ram']['quotaUsed']
perf_data['ram.quota_used_per_node'] = default['storageTotals']['ram']['quotaUsedPerNode']
perf_data['ram.quota_total_per_node'] = default['storageTotals']['ram']['quotaTotalPerNode']
perf_data['ram.total'] = default['storageTotals']['ram']['total']
perf_data['ram.quota_total'] = default['storageTotals']['ram']['quotaTotal']
perf_data['ram.used_by_data'] = default['storageTotals']['ram']['usedByData']

# Node level metrics
nodes = default['nodes']
for node in nodes:
    node_name = node['hostname'].split('.')[0]
    if node['clusterMembership'] != 'active' and node['thisNode']:
        output = "Node: %s is not active | " % node
        exit_status = 2
    perf_data[node_name + '.' + 'mcd_memory_reserved'] = node['mcdMemoryReserved']
    perf_data[node_name + '.' + 'mcd_memory_allocated'] = node['mcdMemoryAllocated']
    perf_data[node_name + '.' + 'memory_free'] = node['memoryFree']
    perf_data[node_name + '.' + 'memory_total'] = node['memoryTotal']
    system = node['systemStats']
    for k, v in system.iteritems():
        perf_data[node_name + '.' + k] = v
    interesting = node['interestingStats']
    for k, v in interesting.iteritems():
        perf_data[node_name + '.' + k] = v

for k, v in perf_data.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
sys.exit(exit_status)
