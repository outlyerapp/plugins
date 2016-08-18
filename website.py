#!/usr/bin/env python

import requests
import sys

URL = 'https://www.google.com'
STRING = '<title>Google</title>'

response = requests.get(URL)

if STRING in response.content:
    print "OK | status_code=%s;;;; time=%s;;;; size=%s;;;;" % (str(response.status_code), 
                                                               str(response.elapsed.total_seconds()) + 's',
                                                               str(response.headers['content-length']) + 'B')
    sys.exit(0)
else:
    print "Plugin Failed!"
    sys.exit(2)

