#!/usr/bin/env python
import getopt
import sys
import re

from datetime import datetime
from datetime import timedelta
from boto.ec2 import connect_to_region
from boto.exception import EC2ResponseError
from boto import config

if not config.has_section('Boto'):
    config.add_section('Boto')

config.setbool('Boto', 'https_validate_certificates', False)

"""
    Nagios check to alert on any retiring instances or instances that need rebooting.
"""

# Setup IAM User with read-only EC2 access
AWS_KEY = ''
AWS_SECRET = ''
REGION = 'us-east-1'

OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def get_instances(instance_ids):
    """
    Return an Instance objects for the given instance ids

    @param instance_ids: Instance ids (list)
    @return: Instance objects (dict)
    """

    instances = dict()
    conn = connect_to_region(REGION, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)
    try:
        reservations = conn.get_all_instances(instance_ids)
    except EC2ResponseError, ex:
        print 'Got exception when calling EC2 for instances (%s): %s' % \
                        (", ".join(instance_ids), ex.error_message)
        return instances

    for r in reservations:
        if len(r.instances) and r.instances[0].id in instance_ids:
            instances[r.instances[0].id] = r.instances[0].tags["Name"]

    return instances


class AmazonEventCheck(object):
    """
    Nagios check for the Amazon events.
    Will warn/error if any pending events based on time till event occurs
    """

    def __init__(self):
        pass

    def _get_instances_pending_events(self):
        """
        Get list of instances that have pending events.

        @return: List(Instance, String , Datetime), List of (Instance, instance
                 Event, Scheduled Date) for hosts with pending events
        """

        conn = connect_to_region(REGION, aws_access_key_id=AWS_KEY, aws_secret_access_key=AWS_SECRET)
        stats = conn.get_all_instance_status()
        next_token = stats.next_token
        while next_token != None:
            next_stats = conn.get_all_instance_status(next_token=next_token)
            stats.extend(next_stats)
            next_token = next_stats.next_token
        ret = []
        for stat in stats:
            if stat.events:
                for event in stat.events:
                    if re.match('^\[Completed\]', event.description):
                        continue
                    ret.append([stat.id, event.code, event.not_before])
        if len(ret) > 0:
            instances = get_instances([stat[0] for stat in ret])
            for stat in ret:
                stat.insert(1, instances[stat[0]])
        return ret

    def check(self, critical_threshold):
        """
        Check pending instance events, alert if
        event time is less than critical_threshold
        Warn otherwise

        @param critical_threshold: int, number of days before an event that nagios should alert
        """

        events = self._get_instances_pending_events()

        if not events:
            print 'OK: no pending events'
            return OK

        critical_events = []
        warning_events = []

        for event in events:
            event_time = datetime.strptime(event[3], '%Y-%m-%dT%H:%M:%S.000Z')
            # Are we close enough to the instance event that we should alert?
            if datetime.utcnow() > (event_time - timedelta(days=critical_threshold)):
                critical_events.append(event)
            else:
                warning_events.append(event)

        if critical_events:
            print 'CRITICAL: instances with events in %d days - %s' % (critical_threshold, ", ".join(["%s(%s)" % (event[0], event[1]) for event in critical_events]))
            return CRITICAL

        print 'WARNING: instances with scheduled events %s' % (", ".join(["%s(%s)" % (event[0], event[1]) for event in warning_events]))
        return WARNING


def usage():
    print >> sys.stderr, 'Usage: %s [-h|--help] [-A <aws_access_key_id>] [-S <aws_secret_access_key>] [-R <region>] [-c <day>]' % sys.argv[0]


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hA:S:R:c:", ["help"])
    except getopt.GetoptError:
        usage()
        return UNKNOWN

    global KEY_ID, ACCESS_KEY, REGION

    critical_threshold = 2
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            return UNKNOWN
        if o in ("-A"):
            KEY_ID = a
        if o in ("-S"):
            ACCESS_KEY = a
        if o in ("-R"):
            REGION = a
        if o in ("-c"):
            critical_threshold = int(a)

    if KEY_ID == "" or ACCESS_KEY == "":
        usage()
        return UNKNOWN

    eventcheck = AmazonEventCheck()
    return eventcheck.check(critical_threshold)

sys.exit(main())
