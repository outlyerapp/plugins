#!/usr/bin/env python

import requests
import os
from docker import Client

try:
    cadvisor_uri = os.environ['CADVISOR_PORT'].replace('tcp', 'http')
    c = Client(base_url='unix://var/run/docker.sock')
    containers = c.containers()
except:
    print "connection failed"
    sys.exit(2)

def get_stats(container_id):
    return requests.get("%s/api/v2.0/stats/%s?type=docker&count=1" % (cadvisor_uri, container_id)).json()

raw_stats = {}
for container in containers:
    raw_stats.update({container['Id']:{ 'name': container['Names'],
                                        'image': container['Image'],
                                        'data': get_stats(container['Id'])
                                      }
                    })

metrics = {}

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
