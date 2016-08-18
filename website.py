#!/usr/bin/env python

import requests
from requests import exceptions
import sys

URL = 'https://www.gradschool.psu.edu'
STRING = '<a href="/prospective-students/how-to-apply/">How to Apply</a>'

try:
    response = requests.get(URL, verify=True)

    if STRING in response.content:
        print "OK | status_code=%s;;;; time=%s;;;;" % (str(response.status_code),
                                                       str(response.elapsed.total_seconds()) + 's')
        sys.exit(0)
    else:
        print "Plugin Failed! String %s not found" % STRING
        sys.exit(2)

except exceptions.SSLError:
    print "Plugin Failed! SSL Certificate verification failed."
    sys.exit(2)



