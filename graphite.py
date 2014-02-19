#!/usr/bin/env python

import sys
import urllib

# Alert off of Graphite metrics.

REVERSE = True  # Alert when the value is UNDER warn/crit instead of OVER'

HW = False

CRIT = 23000
WARN = 24000

CRITUPPER = ''
CRITLOWER = ''

DIFF1 = ''
DIFF2 = ''

SECONDS = 60

URL = ''

# Nagios exit codes
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3
STATE_DEPENDENT = 4


def pull_graphite_data(url):
    """Pull down raw data from Graphite"""
    # Make sure the url ends with '&rawData'
    if not url.endswith('&rawData'):
        url += '&rawData'
    data = urllib.urlopen(url).read()
    return data


def eval_graphite_data(data, seconds):
    """Get the most recent correct value from the data"""

    sample_period = int(data.split('|')[0].split(',')[-1])
    all_data_points = data.split('|')[-1].split(',')

    # Evaluate what graphite returned, should either be a float, or None
    # First, if the number of seconds of data we want to examine is smaller or
    # equals the graphite sample period, just grab the latest data point.
    # If that data point is None, grab the one before it.
    # If that is None too, return 0.0.
    if seconds <= sample_period:
        if eval(all_data_points[-1]):
            data_value = float(all_data_points[-1])
        elif eval(all_data_points[-2]):
            data_value = float(all_data_points[-2])
        else:
            data_value = 0.0
    else:
        # Second, if we requested more than on graphite sample period, work out how
        # many sample periods we wanted (python always rounds division *down*)
        data_points = (seconds / sample_period)
        data_set = [float(x) for x in all_data_points[-data_points:]
                    if eval(x)]
        if data_set:
            data_value = float(sum(data_set) / len(data_set))
        else:
            data_value = 0.0
    return data_value


def get_hw_value(url, seconds=0):
    """Get the Holt-Winters value from a Graphite graph"""

    data = pull_graphite_data(url)
    for line in data.split():
        if line.startswith('holtWintersConfidenceUpper'):
            graphite_upper = eval_graphite_data(line, seconds)
        elif line.startswith('holtWintersConfidenceLower'):
            graphite_lower = eval_graphite_data(line, seconds)
        else:
            graphite_data = eval_graphite_data(line, seconds)

    return graphite_data, graphite_lower, graphite_upper


def get_value(url, seconds=0):
    """Get the value from a Graphite graph"""

    data = pull_graphite_data(url)
    data_value = eval_graphite_data(data, seconds)
    return data_value


def main():

    if HW:
        graphite_data, graphite_lower, graphite_upper = get_hw_value(URL, SECONDS)

        print 'Current value: %s, lower band: %s, upper band: %s' % (graphite_data, graphite_lower, graphite_upper)

        if (graphite_data > graphite_upper) or (graphite_data < graphite_lower):
            if CRITUPPER or CRITLOWER:
                sys.exit(STATE_CRITICAL)
            else:
                sys.exit(STATE_WARNING)
        else:
            sys.exit(STATE_OK)

    if DIFF1:
        graphite_data1 = get_value(DIFF1, SECONDS)
        graphite_data2 = get_value(DIFF2, SECONDS)
        graphite_data = abs(graphite_data1 - graphite_data2)

    else:
        graphite_data = get_value(URL, SECONDS)
        print 'Current value: %s, warn threshold: %s, crit threshold: %s | hubs=%s' % (graphite_data, WARN, CRIT, graphite_data)

    if REVERSE is True:
        if CRIT >= graphite_data:
            sys.exit(STATE_CRITICAL)
        elif WARN >= graphite_data:
            sys.exit(STATE_WARNING)
        else:
            sys.exit(STATE_OK)
    else:
        if graphite_data >= CRIT:
            sys.exit(STATE_CRITICAL)
        elif graphite_data >= WARN:
            sys.exit(STATE_WARNING)
        else:
            sys.exit(STATE_OK)

main()