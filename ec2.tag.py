#!/usr/bin/env python
import sys
import requests
import socket
import subprocess
from boto import ec2

'''
Tagging script that can be applied to AWS EC2 instances.
Update the settings below and set the plugin interval to 5 minutes to reduce the API calls
'''

# AWS Settings
AWS_REGION = 'us-east-1'
AWS_KEY = ''
AWS_SECRET = ''

try:
    # collect some useful metadata
    hostname = socket.gethostname().partition('.')[0].lower()
    instance_id = requests.get('http://instance-data/latest/meta-data/instance-id').text
    instance_type = requests.get('http://instance-data/latest/meta-data/instance-type').text
    availability_zone = requests.get('http://instance-data/latest/meta-data/placement/availability-zone').text
    
    # collect the AWS tags
    conn = ec2.connect_to_region(AWS_REGION, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)
    reservations = conn.get_all_instances(instance_ids=[instance_id])
    instance = reservations[0].instances[0]
    tags = instance.tags
    
    # create a list of tags from everything
    aws_tag_list = []
    for k, v in tags.iteritems():
        aws_tag_list.append(str(k + ':' + v).lower())
    aws_tag_list.append(instance_type)
    aws_tag_list.append(availability_zone)
    tags = ','.join(map(str, aws_tag_list))

    # tell the dataloop agent to apply the tags
    subprocess.check_output(['dataloop-agent', '--add-tags', tags])
    sys.exit(0)
except Exception, e:
    print "aws tagging failed! %s" % e
    sys.exit(2)
