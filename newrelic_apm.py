#!/usr/bin/env python

import requests
import sys

"""
New Relic APM Nagios Plugin

Description:

Get's APM metrics from New Relic's REST API for specified application. Will list all the metrics for every instance monitored
in the application:
    - health_status     Green is good, red is bad
    - response_time     Average Web response time in MS
    - throughput        Number of requests going through application per minute
    - error_rate        Number of errors per minute
    - apdex_score       How long requests are taking to respond in seconds

This script uses New Relic's V2 REST API: https://rpm.newrelic.com/api/explore

Setup:

This plugin requires your New Relic API Key (found under Account Settings -> Data Sharing) and your New Relic Application
ID (found in the URL https://rpm.newrelic.com/accounts/{accountID}/applications/{applicationID}). Once you have them
put them at the top of the script and the script should run successfully

"""


# Set Variables to access New Relic Rest API

NEWRELIC_APIKEY = 'NEW RELIC API KEY'
NEWRELIC_APPID = 'NEW RELIC APPLICATION ID'
NEWRELIC_INSTANCEID = 'NEW RELIC INSTANCE ID'

# Main method
def main():

    url = 'https://api.newrelic.com/v2/applications/{}/instances/{}.json'.format(NEWRELIC_APPID, NEWRELIC_INSTANCEID)
    data = _make_request(url)
    metrics = data['application_instance']['application_summary']

    # Get output variables
    health_status = data['application_instance']['health_status']
    error_rate = metrics['error_rate']
    apdex_score = metrics['apdex_score']
    throughput = metrics['throughput']
    response_time = metrics['response_time']

    if health_status == 'green':
        print "OK | error_rate={};;;; apdex_score={};;;; throughput={};;;; response_time={};;;;".format(error_rate,
                                                                                apdex_score, throughput, response_time)
        sys.exit(0)
    else:
        print "Health_Status is {} on New Relic | error_rate={};;;; apdex_score={};;;; throughput={};;;; response_time={};;;;".format(health_status,
                                                                                error_rate, apdex_score, throughput, response_time)
        sys.exit(2)


# Makes authenticated request to New Relic REST APIs and return JSON Response
def _make_request(url):

    response = requests.get(url, headers={'X-Api-Key': NEWRELIC_APIKEY})
    if response.status_code == 200:
        return response.json()
    else:
        print 'Error calling ' + url + ': {}'.format(response.status_code);
        sys.exit(2)

# Run main
main()