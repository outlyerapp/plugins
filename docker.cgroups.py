#!/usr/bin/env python
"""
Metrics collection for docker:
see https://blog.docker.com/2013/10/gathering-lxc-docker-containers-metrics/

The metrics path is currently the docker name from 'docker ps'
"""

import os
import collections
from subprocess import check_output
from string import Template


# TODO: get the cgroups path from mounts
# Assume cgroups are under /sys/fs/cgroup
CGROUP_PATH = '/sys/fs/cgroup/'
CGROUP_STUBS = [ 'lxc', 'docker', 'system.slice' ]
CGROUP_FILE = { 'memory': 'memory.stat',
                'cpuacct': 'cpuacct.stat'}

# empty metric hash
metrics = {}


def flatten(d, parent_key='', sep='.'):
    """ flatten a dictionary into a dotted string
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def determine_path(cgroup):
    """
    possible paths:
    /sys/fs/cgroup/<<CGROUP>>/lxc/<<DOCKERID>>/memory.stat')
    /sys/fs/cgroup/<<CGROUP>>/docker/<<DOCKERID>>/memory.stat')
    /sys/fs/cgroup/<<CGROUP>>/system.slice/docker-<<DOCKERID>>.scope/memory.stat')
    """
    if os.path.exists(CGROUP_PATH + cgroup + '/lxc/'):
        return Template(CGROUP_PATH + cgroup + '/lxc/' + '$dockerID/' + CGROUP_FILE[cgroup])
    elif os.path.exists(CGROUP_PATH + cgroup + '/docker/'):
        return Template(CGROUP_PATH + cgroup + '/docker/' + '$dockerID/' + CGROUP_FILE[cgroup])
    elif os.path.exists(CGROUP_PATH + cgroup + '/system.slice/'):
        return Template(CGROUP_PATH + cgroup + '/system.slice/docker-' + '$dockerID' + '.scope/' + CGROUP_FILE[cgroup])
    else:
        raise Exception("Could not determine docker cgroups directory. Is docker running?")

docker_ps = check_output("/usr/bin/docker ps --no-trunc 2>/dev/null", shell=True).splitlines()[1::]

metrics['containers'] = {}
metrics['containers']['count'] =  len(docker_ps)


for container in docker_ps:
    vmid = container.split()[0]
    PATH = container.split()[-1]
    metrics[PATH] =  {}
    metrics[PATH]['memory'] =  {}
    stat_file = determine_path('memory').substitute(dockerID=vmid)
    with open(stat_file, 'r') as fp:
        stats = [line.rstrip('\n') for line in fp]
        for stat in stats:
            k,v = stat.split(' ')
            metrics[PATH]['memory'][k] = v

    metrics[PATH]['cpuacct'] = {}
    stat_file = determine_path('cpuacct').substitute(dockerID=vmid)
    with open(stat_file, 'r') as fp:
        stats = [line.rstrip('\n') for line in fp]
        for stat in stats:
            k,v = stat.split(' ')
            metrics[PATH]['cpuacct'][k] = v


metrics = flatten(metrics)

perf_data = "OK | "
for k,v in metrics.iteritems():
    perf_data += "%s=%s;;;; " % (k,v)

print perf_data
