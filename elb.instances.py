#!/usr/bin/env python

"""
"""

from boto.ec2 import elb
import sys

AWS_REGION = ''
AWS_KEY = ''
AWS_SECRET = ''
ELB_NAME = ''

CRITICAL_LIMIT = 1

state = {}
state['InService'] = 0
state['OutOfService'] = 0
state['unknown'] = 0


conn = elb.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY,
                            aws_secret_access_key=AWS_SECRET)


instances = conn.describe_instance_health("tester")

for instance in instances:
    if instance.state == 'InService':
        state['InService'] += 1
    elif instance.state == 'OutOfService':
        state['OutOfService'] =+ 1
    else:
        state['unknown'] +=1

if state['unknown'] > 0:
    message = "WARN - instances in an unknown state | "
    EXIT = 1
elif state['OutOfService'] >= CRITICAL_LIMIT:
    message = "CRITICAL - instances down | "
    EXIT = 2
else:
    message = "OK | "
    EXIT = 0

for s in state:
    message += "%s=%s;;;; " % (s, state[s])

print message
sys.exit(EXIT)


