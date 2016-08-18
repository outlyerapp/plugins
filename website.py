#!/usr/bin/env python

import requests
from requests import exceptions
import sys

URL = 'https://www.google.com'
STRING = '<title>Google</title>'

try:
    response = requests.get(URL, verify=True)

    if STRING in response.content:
        print "OK | status_code=%s;;;; time=%s;;;; size=%s;;;;" % (str(response.status_code),
                                                                   str(response.elapsed.total_seconds()) + 's',
                                                                   str(response.headers['content-length']) + 'B')
        sys.exit(0)
    else:
        print "Plugin Failed! String %s not found" % STRING
        sys.exit(2)

except exceptions.SSLError:
    print "Plugin Failed! SSL Certificate verification failed."
    sys.exit(2)



