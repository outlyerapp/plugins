#!/usr/bin/env python
import sys
import requests


# Set these variables for Auth and what test to use
API_KEY = ''
USER = ''
TEST_ID = ''

try:
    TEST_URL = 'https://www.statuscake.com/API/Tests/Checks?TestID=%s&Fields=status,state,time,performance' % TEST_ID

    headers = {"API": API_KEY,
               "Username": USER}

    resp = requests.get(TEST_URL, headers=headers).json()

    current_time = 0
    highest_time = 0
    for check, details in resp.iteritems():
        current_time = details['Time']
        if current_time > highest_time:
            final_details = details

    if final_details['State'] == 'Up':
        print "OK | status_code=%s;;;; performance=%s;;;;" % (final_details['Status'], final_details['Performance'])
        sys.exit(0)
    else:
        print "DOWN! | status_code=%s" % final_details['Status']
        sys.exit(2)

except Exception, e:
    print "Plugin Failed!: %s" % e
    sys.exit(2)
