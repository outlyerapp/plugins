#!/usr/bin/env python

from rackspace_monitoring.providers import get_driver
from rackspace_monitoring.types import Provider
import sys
import socket
import time

"""
Rackspace Cloud Monitor Metrics Nagios Plugin

Description:

Pulls in Rackspace Cloud Monitoring metrics from Rackspace's Cloud Monitoring API for the instance the script is working
on

Setup:

You need to install the Raxmon client (http://www.rackspace.com/knowledge_center/article/getting-started-with-rackspace-monitoring-cli)
Use the command:

sudo pip install rackspace-monitoring-cli

And run this plugin in the 'System Default' shell to work properly. You will also need to apply your Rackspace cloud console username
and API Key (founder under Account Settings in your Cloud Console) to the top of the script

"""

# Set Variables to access Rackspace Rest APIs

RS_USERNAME = 'USERNAME'
RS_APIKEY = 'API KEY'

# Use this to override the hostname to get metrics for, for testing. Leave blank if using OS hostname
OVERRIDE_HOSTNAME = ''

# Main method
def main():

    entity = _get_entity()
    values = _get_metric_values(entity)

    output = 'OK | '
    for key, value in values.iteritems():
        output = output + key + "={};;;; ".format(value)

    print output
    sys.exit(0)

# Get the API Entity ID for the current host running the script
def _get_entity():

    hostname = OVERRIDE_HOSTNAME

    if OVERRIDE_HOSTNAME == '':
        hostname = socket.gethostname()

    driver = _get_driver()
    results = driver.list_entities()
    for entity in results:
        if entity.label == hostname:
            return driver.get_entity(entity_id= entity.id)

    return None

# List alarms created by checks on Rackspace sever
def _get_metric_values(entity):

    driver = _get_driver()
    checks = _list_entity_checks(entity)

    values = {}

    to_timestamp = str(int(time.time()) * 1000);
    from_timestamp = str((int(time.time()) * 1000) - 60000)

    # Iterate through all the checks for an instance
    for check in checks:
        metrics = driver.list_metrics(entity_id=entity.id, check_id=check.id)
        # Iterate through all the metrics for the check
        for metric in metrics:
            datapoint = driver.fetch_data_point(entity_id=entity.id, check_id=check.id, metric_name=metric.name,
                                                from_timestamp=from_timestamp, to_timestamp=to_timestamp)
            if not datapoint:
                values[check.id + "." + metric.name] = 0
            else:
                values[check.id + "." + metric.name] = datapoint[0].average

    return values

# List checks running for a particular Rackspace server
def _list_entity_checks(entity):

    driver = _get_driver()
    checks =  driver.list_checks(entity=entity)
    return checks

# Get a Rackspace API driver to make requests to APIs
def _get_driver():
    driver = get_driver(Provider.RACKSPACE)

    kwargs = {}
    kwargs['ex_force_base_url'] = 'https://monitoring.api.rackspacecloud.com/v1.0'
    kwargs['ex_force_auth_url'] = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
    kwargs['ex_force_auth_token'] = None
    instance = driver(RS_USERNAME, RS_APIKEY, **kwargs)

    return instance

# Run main
main()