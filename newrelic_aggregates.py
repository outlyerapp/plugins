#!/usr/bin/env python

import requests
import socket
import sys
import re

"""
Enter your New Relic API Key found under Account Settings -> Data Sharing
and a list of your Application ID's found in the URL https://rpm.newrelic.com/accounts/{accountID}/applications/{applicationID}

This script will return metrics in the format:

application_name.hostname.metric

You should run it on a single agent.
"""

NEWRELIC_APIKEY = ''
NEWRELIC_APPIDS = ['']

metrics = {}

for app in NEWRELIC_APPIDS:

    url = 'https://api.newrelic.com/v2/applications/{}/instances.json'.format(app)
    data = requests.get(url, headers={'X-Api-Key': NEWRELIC_APIKEY}).json()
    instances = data['application_instances']

    for instance in instances:
        if 'Aggregate' in instance['application_name']:
            application_name = instance['application_name'].replace(' ', '.').lower()
            host_name = instance['host'].replace('.', '-')
            metrics[application_name + '.' + host_name + '.error_rate'] = instance['application_summary']['error_rate']
            metrics[application_name + '.' + host_name + '.apdex_score'] = instance['application_summary']['apdex_score']
            metrics[application_name + '.' + host_name + '.throughput'] = instance['application_summary']['throughput']
            metrics[application_name + '.' + host_name + '.response_time'] = instance['application_summary']['response_time']
            metrics[application_name + '.' + host_name + '.instance_count'] = instance['application_summary']['instance_count']
            if instance['health_status'] == "green":
                metrics[application_name + '.' + host_name + '.status'] = 0
            else:
                metrics[application_name + '.' + host_name + '.status'] = 2

output = "OK | "
for k, v in metrics.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
