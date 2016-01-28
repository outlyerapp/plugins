#### github.py
#
# Monitors the Github Status Api and
# reports back on platform availability.
#
# (c) DevopsGuys Ltd/Matthew Macdonald-Wallace 2016
# 
# Made available under the MIT license 

import json
import requests
import sys

status_uri = 'https://status.github.com/api/status.json'
r = requests.get(status_uri)
gh_status = json.loads(r.text)
if gh_status['status'] == "major":
    exit_code = 2
elif gh_status['status'] == "minor":
    exit_code = 1
elif gh_status['status'] == "good":
    exit_code = 0
else:
    exit_code = 3

print "Current github status is %s" % gh_status['status']
sys.exit(exit_code)
