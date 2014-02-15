#!/usr/bin/env python
import requests
import json

resp = requests.get('http://localhost:9615')
decoded = json.loads(resp.text)
free_mem = decoded['monit']['free_mem']
load1 = decoded['monit']['loadavg'][0]
load5 = decoded['monit']['loadavg'][1]
load15 = decoded['monit']['loadavg'][2]

print "OK | free_mem=%s;;;; load1=%s;;;; load5=%s;;;; load15=%s;;;;" % (free_mem, load1, load5, load15)