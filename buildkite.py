import sys
import requests
import json
from datetime import datetime

APIKEY = ''
PROJECT = ''
ORG = ''


def api_header():
    return {"Content-type": "application/json", "Authorization": "Bearer " + APIKEY}


projects = requests.get('https://api.buildkite.com/v1/organizations/%s/projects' % ORG, headers=api_header()).json()
message = "OK | "
exit_status = 0
perf_data = {}
for project in projects:
    if project['name'] == PROJECT:
        if project['featured_build']['state'] != 'passed':
            message = "Build failed! | "
            exit_status = 2
        perf_data['build_num'] = project['featured_build']['number']
        try:
            start_time = datetime.strptime(project['featured_build']['started_at'], '%Y-%m-%d %H:%M:%S %Z')
            end_time = datetime.strptime(project['featured_build']['finished_at'], '%Y-%m-%d %H:%M:%S %Z')
            duration = end_time - start_time
            perf_data['duration'] = str(duration.seconds) + 's'
        except:
            perf_data['duration'] = '0s'

for k, v in perf_data.iteritems():
    message += str(k) + '=' + str(v) + ';;;; '

print message
sys.exit(exit_status)

