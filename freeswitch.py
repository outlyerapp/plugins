#!/usr/bin/env python
import sys
import subprocess

'''
add dataloop user to the daemon unix group and restart dataloop-agent service
'''

def show_calls_count():
    command = ['/usr/local/freeswitch/bin/fs_cli', '-x', 'show calls count']
    resp = subprocess.check_output(command).split('\n')
    data = {}
    for line in resp:
        if 'total' in line:
            data['show_calls_count.total'] = filter(lambda x: x.isdigit(), line)
    return data

def sofia_status_internal():
    command = ['/usr/local/freeswitch/bin/fs_cli', '-x', 'sofia status']
    resp = subprocess.check_output(command).split('\n')
    data = {}
    for line in resp:
        if 'internal' in line:
            try:
                details = line.split()
                name = "sofia_status_%s.%s" % (details[0], details[2])
                calls = details[4].replace('(', '').replace(')', '')
                if details[3] == 'RUNNING':
                    data[name] = calls
            except:
                continue
    return data

def sofia_status_external():
    command = ['/usr/local/freeswitch/bin/fs_cli', '-x', 'sofia status']
    resp = subprocess.check_output(command).split('\n')
    data = {}
    for line in resp:
        if 'external' in line:
            try:
                details = line.split()
                name = "sofia_status_%s.%s" % (details[0], details[2])
                calls = details[4].replace('(', '').replace(')', '')
                if details[3] == 'RUNNING':
                    data[name] = calls
            except:
                continue
    return data
    
def sofia_status_profile_internal_failed_calls_in():
    command = ['/usr/local/freeswitch/bin/fs_cli', '-x', 'sofia status profile internal']
    resp = subprocess.check_output(command).split('\n')
    data = {}
    failed = 0
    for line in resp:
        if 'failed-calls-in' in line:
            try:
                details = line.split()
                failed += 1
            except:
                continue
    data['sofia_status_profile_internal_failed_calls_in.failed'] = failed
    return data
            
def sofia_status_profile_internal_failed_calls_out():
    command = ['/usr/local/freeswitch/bin/fs_cli', '-x', 'sofia status profile internal']
    resp = subprocess.check_output(command).split('\n')
    data = {}
    failed = 0
    for line in resp:
        if 'failed-calls-out' in line:
            try:
                details = line.split()
                failed += 1
            except:
                continue
    data['sofia_status_profile_internal_failed_calls_out.failed'] = failed
    return data  
    
checks = [show_calls_count,
          sofia_status_internal,
          sofia_status_external,
          sofia_status_profile_internal_failed_calls_in,
          sofia_status_profile_internal_failed_calls_out]

# Compose big dict of all check output
raw_output = {}
for check in checks:
    try:
        raw_output.update(check())
    except Exception, e:
        print "Plugin Failed! %s" % e
        sys.exit(2)

# Output in Nagios format
output = "OK | "
for k, v in raw_output.iteritems():
    output += "%s=%s;;;; " % (k, v)
print output
sys.exit(0)
