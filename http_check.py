#!/usr/bin/env python

"""
Call a json endpoint and return metrics about the page call
Also allow metrics for content in the json
"""

import requests
import sys

BASE_URL = 'https://your.example.com'
URL = '/'

URL_PARAMS = { 'apikey': 'random-uuid-string'}  # can be left blank

# setup a metrics dictionary for metrics output
metrics = {}
metrics['error'] = 0
E_CODE = 0

# Try and get the json api endpoint
try:
    url = '%s%s' % (BASE_URL, URL)
    req = requests.get(url, params=URL_PARAMS)
    json_content = req.json()
    # Build the exit message. Anything other then 200 is not ideal
    if req.status_code == 200:
        message = "OK | "
    else:
        message = "Critical | "
        metrics['error'] = 1
        E_CODE = 2

    # return the time taken
    metrics['time'] = str(req.elapsed.total_seconds()) + 's'
    # return the http status code
    metrics['http_status_code'] = req.status_code
    # return the content size
    metrics['size'] = str(req.headers['content-length']) + 'B'

except Exception as e:
    message =  "CRITICAL - %s | " % str(e)
    metrics['error'] = 1
    metrics['time'] = '0s'
    metrics['http_status_code'] = 0
    metrics['size'] = '0B'
    E_CODE = 2

for k,v in metrics.iteritems():
    message += "%s=%s;;; " % (k,v)

print message
sys.exit(E_CODE)
