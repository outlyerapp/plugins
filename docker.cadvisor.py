#!/usr/bin/env python
"""
This plugin should only be assigned to dataloop-docker containers that are linked to a cadvisor container

This script scrapes the cadvisor api to gather host and per container metrics

For more details see : https://github.com/dataloop/dataloop-docker
"""
import requests
import os
import sys
from docker import Client

try:
    cadvisor_uri = os.environ['CADVISOR_PORT'].replace('tcp', 'http')
    c = Client(base_url='unix://var/run/docker.sock')
    containers = c.containers()
except:
    print "Plugin Failed!"
    sys.exit(2)

metrics = {}

# Docker Stats
info = c.info()
metrics['ngoroutines'] = info['NGoroutines']
metrics['driverstatus.dirs'] = info['DriverStatus'][2][1]
metrics['containers.running'] = len(c.containers())
metrics['containers.total'] = info['Containers']
metrics['images.total'] = info['Images']
metrics['images.committed'] = len(c.images(quiet=True))
    
# Host Stats
host_stats = requests.get("%s/api/v2.0/stats?count=1" % cadvisor_uri, timeout=60).json()

# Network
for index, elem in enumerate(host_stats['/'][0]['network']):
    metrics['host.network.%s.tx_dropped' % index] = host_stats['/'][0]['network'][index]['tx_dropped']
    metrics['host.network.%s.rx_packets' % index] = host_stats['/'][0]['network'][index]['rx_packets']
    metrics['host.network.%s.rx_bytes' % index] = host_stats['/'][0]['network'][index]['rx_bytes']
    metrics['host.network.%s.tx_errors' % index] = host_stats['/'][0]['network'][index]['tx_errors']
    metrics['host.network.%s.rx_errors' % index] = host_stats['/'][0]['network'][index]['rx_errors']
    metrics['host.network.%s.tx_bytes' % index] = host_stats['/'][0]['network'][index]['tx_bytes']
    metrics['host.network.%s.rx_dropped' % index] = host_stats['/'][0]['network'][index]['rx_dropped']
    metrics['host.network.%s.tx_packets' % index] = host_stats['/'][0]['network'][index]['tx_packets']
    
# Load Stats
metrics['host.load_stats.nr_stopped'] = host_stats['/'][0]['load_stats']['nr_stopped']
metrics['host.load_stats.nr_sleeping'] = host_stats['/'][0]['load_stats']['nr_sleeping']
metrics['host.load_stats.nr_uninterruptible'] = host_stats['/'][0]['load_stats']['nr_uninterruptible']
metrics['host.load_stats.nr_running'] = host_stats['/'][0]['load_stats']['nr_running']
metrics['host.load_stats.nr_io_wait'] = host_stats['/'][0]['load_stats']['nr_io_wait']

# Disk IO
for index, elem in enumerate(host_stats['/'][0]['diskio']['io_service_bytes']):
    metrics['host.diskio.io_service_bytes.%s.major' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['major']
    metrics['host.diskio.io_service_bytes.%s.minor' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['minor']
    metrics['host.diskio.io_service_bytes.%s.stats.read' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['stats']['Read']
    metrics['host.diskio.io_service_bytes.%s.stats.async' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['stats']['Async']
    metrics['host.diskio.io_service_bytes.%s.stats.write' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['stats']['Write']
    metrics['host.diskio.io_service_bytes.%s.stats.total' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['stats']['Total']
    metrics['host.diskio.io_service_bytes.%s.stats.sync' % index] = host_stats['/'][0]['diskio']['io_service_bytes'][index]['stats']['Sync']

for index, elem in enumerate(host_stats['/'][0]['diskio']['io_serviced']):    
    metrics['host.diskio.io_serviced.%s.major' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['major']
    metrics['host.diskio.io_serviced.%s.minor' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['minor']
    metrics['host.diskio.io_serviced.%s.stats.read' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['stats']['Read']
    metrics['host.diskio.io_serviced.%s.stats.async' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['stats']['Async']
    metrics['host.diskio.io_serviced.%s.stats.write' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['stats']['Write']
    metrics['host.diskio.io_serviced.%s.stats.total' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['stats']['Total']
    metrics['host.diskio.io_serviced.%s.stats.sync' % index] = host_stats['/'][0]['diskio']['io_serviced'][index]['stats']['Sync']
    
# Memory
metrics['host.memory.usage'] = host_stats['/'][0]['memory']['usage']
metrics['host.memory.working_set'] = host_stats['/'][0]['memory']['working_set']
metrics['host.memory.hierarchical_data.pgfault'] = host_stats['/'][0]['memory']['hierarchical_data']['pgfault']
metrics['host.memory.hierarchical_data.pgmajfault'] = host_stats['/'][0]['memory']['hierarchical_data']['pgmajfault']
metrics['host.memory.container_data.pgfault'] = host_stats['/'][0]['memory']['container_data']['pgfault']
metrics['host.memory.container_data.pgmajfault'] = host_stats['/'][0]['memory']['container_data']['pgmajfault']

# CPU
metrics['host.cpu.usage.system'] = host_stats['/'][0]['cpu']['usage']['system']
metrics['host.cpu.usage.total'] = host_stats['/'][0]['cpu']['usage']['total']
metrics['host.cpu.usage.user'] = host_stats['/'][0]['cpu']['usage']['user']
metrics['host.cpu.load_average'] = host_stats['/'][0]['cpu']['load_average']

for index, elem in enumerate(host_stats['/'][0]['cpu']['usage']['per_cpu_usage']):
    metrics['host.cpu.usage.per_cpu_usage.%s' % index] = host_stats['/'][0]['cpu']['usage']['per_cpu_usage'][index]
        

# Container Stats

raw_stats = {}

def get_stats(container_id):
    return requests.get("%s/api/v2.0/stats/%s?type=docker&count=1" % (cadvisor_uri, container_id)).json()


for container in containers:
    raw_stats.update({container['Id']:{ 'name': container['Names'],
                                        'image': container['Image'],
                                        'data': get_stats(container['Id'])
                                      }
                    })


def store_metric(name, image, path, value):
    metrics[name + '.' + path] = value
    metrics[image + '.' + path] = value

for id, values in raw_stats.iteritems():
    name = values['name'][0].replace('/', '')
    image = values['image'].replace('/', '.').replace(':', '.')
    stats = values['data']['/docker/' + id]
    for stat in stats:
        # Network
        for index, elem in enumerate(stat['network']):
            store_metric(name, image, 'network.%s.tx_dropped' % index, stat['network'][index]['tx_dropped'])
            store_metric(name, image, 'network.%s.rx_packets' % index, stat['network'][index]['rx_packets'])
            store_metric(name, image, 'network.%s.rx_bytes' % index, stat['network'][index]['rx_bytes'])
            store_metric(name, image, 'network.%s.tx_errors' % index, stat['network'][index]['tx_errors'])
            store_metric(name, image, 'network.%s.rx_errors' % index, stat['network'][index]['rx_errors'])
            store_metric(name, image, 'network.%s.tx_bytes' % index, stat['network'][index]['tx_bytes'])
            store_metric(name, image, 'network.%s.rx_dropped' % index, stat['network'][index]['rx_dropped'])
            store_metric(name, image, 'network.%s.tx_packets' % index, stat['network'][index]['tx_packets'])
            
        # Load Stats
        store_metric(name, image, 'load_stats.nr_stopped', stat['load_stats']['nr_stopped'])
        store_metric(name, image, 'load_stats.nr_sleeping', stat['load_stats']['nr_sleeping'])
        store_metric(name, image, 'load_stats.nr_uninterruptible', stat['load_stats']['nr_uninterruptible'])
        store_metric(name, image, 'load_stats.nr_running', stat['load_stats']['nr_running'])
        store_metric(name, image, 'load_stats.nr_io_wait', stat['load_stats']['nr_io_wait'])
        
        # Disk IO
        for index, elem in enumerate(stat['diskio']['io_service_bytes']):
            store_metric(name, image, 'diskio.io_service_bytes.%s.major' % index, stat['diskio']['io_service_bytes'][index]['major'])
            store_metric(name, image, 'diskio.io_service_bytes.%s.minor' % index, stat['diskio']['io_service_bytes'][index]['minor'])
            store_metric(name, image, 'diskio.io_service_bytes.%s.stats.read' % index, stat['diskio']['io_service_bytes'][index]['stats']['Read'])
            store_metric(name, image, 'diskio.io_service_bytes.%s.stats.async' % index, stat['diskio']['io_service_bytes'][index]['stats']['Async'])
            store_metric(name, image, 'diskio.io_service_bytes.%s.stats.write' % index, stat['diskio']['io_service_bytes'][index]['stats']['Write'])
            store_metric(name,  image, 'diskio.io_service_bytes.%s.stats.total' % index, stat['diskio']['io_service_bytes'][index]['stats']['Total'])
            store_metric(name, image, 'diskio.io_service_bytes.%s.stats.sync' % index, stat['diskio']['io_service_bytes'][index]['stats']['Sync'])
        
        for index, elem in enumerate(stat['diskio']['io_serviced']):    
            store_metric(name, image, 'diskio.io_serviced.%s.major' % index, stat['diskio']['io_serviced'][index]['major'])
            store_metric(name, image, 'diskio.io_serviced.%s.minor' % index, stat['diskio']['io_serviced'][index]['minor'])
            store_metric(name, image, 'diskio.io_serviced.%s.stats.read' % index, stat['diskio']['io_serviced'][index]['stats']['Read'])
            store_metric(name, image, 'diskio.io_serviced.%s.stats.async' % index, stat['diskio']['io_serviced'][index]['stats']['Async'])
            store_metric(name, image, 'diskio.io_serviced.%s.stats.write' % index, stat['diskio']['io_serviced'][index]['stats']['Write'])
            store_metric(name,  image, 'diskio.io_serviced.%s.stats.total' % index, stat['diskio']['io_serviced'][index]['stats']['Total'])
            store_metric(name, image, 'diskio.io_serviced.%s.stats.sync' % index, stat['diskio']['io_serviced'][index]['stats']['Sync'])
            
        # Memory
        store_metric(name, image, 'memory.usage', stat['memory']['usage'])
        store_metric(name, image, 'memory.working_set', stat['memory']['working_set'])
        store_metric(name, image, 'memory.hierarchical_data.pgfault', stat['memory']['hierarchical_data']['pgfault'])
        store_metric(name, image, 'memory.hierarchical_data.pgmajfault', stat['memory']['hierarchical_data']['pgmajfault'])
        store_metric(name, image, 'memory.container_data.pgfault', stat['memory']['container_data']['pgfault'])
        store_metric(name, image, 'memory.container_data.pgmajfault', stat['memory']['container_data']['pgmajfault'])
        
        # CPU
        store_metric(name, image, 'cpu.usage.system', stat['cpu']['usage']['system'])
        store_metric(name, image, 'cpu.usage.total', stat['cpu']['usage']['total'])
        store_metric(name, image, 'cpu.usage.user', stat['cpu']['usage']['user'])
        store_metric(name, image, 'cpu.load_average', stat['cpu']['load_average'])
        
        for index, elem in enumerate(stat['cpu']['usage']['per_cpu_usage']):
            store_metric(name, image, 'cpu.usage.per_cpu_usage.%s' % index, stat['cpu']['usage']['per_cpu_usage'][index])
                
        
output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
