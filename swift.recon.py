#!/usr/bin/env python
import sys
import requests
import json
import socket

"""
/recon/load	returns 1,5, and 15 minute load average
/recon/mem	returns /proc/meminfo
/recon/mounted	returns ALL currently mounted filesystems
/recon/unmounted	returns all unmounted drives if mount_check = True
/recon/diskusage	returns disk utilization for storage devices
/recon/ringmd5	returns object/container/account ring md5sums
/recon/quarantined	returns # of quarantined objects/accounts/containers
/recon/sockstat	returns consumable info from /proc/net/sockstat|6
/recon/devices	returns list of devices and devices dir i.e. /srv/node
/recon/async	returns count of async pending
/recon/replication	returns object replication times (for backward compatibility)
"""

URIS = ['load', 'mem', 'diskusage', 'quarantined', 'sockstat', 'async', 'replication']

PORT = 6000

metrics = {}
try:
    for URI in URIS:
        resp = requests.get('http://localhost:%d/recon/%s' % (PORT, URI), timeout=60).json()
        if isinstance(resp, dict):
            for k, v in resp.iteritems():
                metrics[URI + '.' + k.lower().replace('(', '_').replace(')', '')] = v
        if isinstance(resp, list):
            for i in resp:
                if i['mounted']:
                    metrics[URI + '.' + i['device'] + '.used'] = i['used']
                    metrics[URI + '.' + i['device'] + '.size'] = i['size']
                    metrics[URI + '.' + i['device'] + '.avail'] = i['avail']
except Exception:
    print "Plugin Failed! Unable to connect to http://localhost:%d/recon/%s" % (PORT, URI)
    sys.exit(2)

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v).lower().replace(' ', '') + ';;;; '

print output
sys.exit(0)

