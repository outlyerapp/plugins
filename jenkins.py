#!/usr/bin/env python
import sys
from jenkinsapi.jenkins import Jenkins

"""
Click username in top right of Jenkins web UI, click Configure, then Show API Token. Use the User ID and Token
in this script to authenticate.
"""

JOBNAME = ""
JENKINS_URL = 'http://localhost:8080'
USER = ''
PASSWORD = ''

try:
    server = Jenkins(JENKINS_URL, username = USER , password = PASSWORD)
except:
    print "connection failed"
    sys.exit(2)

job_instance = server.get_job(JOBNAME)
last_build = job_instance.get_last_buildnumber()
build_instance = job_instance.get_build(last_build)

duration = build_instance.get_duration().seconds
status = build_instance.get_status()

perf_data = "build_number=%s;;;; duration=%ss;;;;" % (last_build, duration) 

if status == "SUCCESS" or status == "null":
    print "OK | " + perf_data
    sys.exit(0)
else:
    print "Job Fail | " + perf_data
    sys.exit(2)

