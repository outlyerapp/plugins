#!/usr/bin/env python

import argparse
import logging
import datetime
from datetime import timedelta
import nagiosplugin
import boto
from boto.ec2.cloudwatch import CloudWatchConnection


AWS_KEY = ''
AWS_SECRET = ''
REGION = 'us-east-1'


""" Set the namespace, metric and dimension as per
    http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/CW_Support_For_AWS.html
"""

NAMESPACE = 'AWS/RDS'
METRIC = 'DatabaseConnections'
DIMENSIONS = 'DBInstanceIdentifier='


def string_to_dict(values):
    if values is None or len(values) is 0:
        return {}

    kvs = {}
    for pair in values.split(','):
        kv = pair.split('=')
        kvs[kv[0]] = kv[1]
    return kvs


def create_connection():
    return boto.ec2.cloudwatch.connect_to_region(REGION,
                                                 aws_access_key_id=AWS_KEY,
                                                 aws_secret_access_key=AWS_SECRET)


class CloudWatchMetric(nagiosplugin.Resource):

    def __init__(self, namespace, metric, dimensions, statistic, period, lag):
        self.namespace = namespace
        self.metric = metric
        self.dimensions = string_to_dict(dimensions)
        self.statistic = statistic
        self.period = int(period)
        self.lag = int(lag)

    def probe(self):
        logging.info('getting stats from cloudwatch')
        cw = create_connection()
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(seconds=self.lag)
        logging.info(start_time)
        stats = []
        stats = cw.get_metric_statistics(self.period,
                                         start_time,
                                         end_time,
                                         self.metric,
                                         self.namespace,
                                         self.statistic,
                                         self.dimensions)
        if len(stats) == 0:
            return []

        stat = stats[0]
        return [nagiosplugin.Metric('cloudwatchmetric', stat[self.statistic], stat['Unit'])]


class CloudWatchRatioMetric(nagiosplugin.Resource):

    def __init__(self, dividend_namespace, dividend_metric, dividend_dimension, dividend_statistic, period, lag, divisor_namespace, divisor_metric, divisor_dimension, divisor_statistic):
        self.dividend_metric = CloudWatchMetric(dividend_namespace, dividend_metric, dividend_dimension, dividend_statistic, int(period), int(lag))
        self.divisor_metric = CloudWatchMetric(divisor_namespace, divisor_metric, divisor_dimension, divisor_statistic, int(period), int(lag))

    def probe(self):
        dividend = self.dividend_metric.probe()[0]
        divisor = self.divisor_metric.probe()[0]

        ratio_unit = '%s / %s' % (dividend.uom, divisor.uom)

        return [nagiosplugin.Metric('cloudwatchmetric', dividend.value / divisor.value, ratio_unit)]


class CloudWatchDeltaMetric(nagiosplugin.Resource):

    def __init__(self, namespace, metric, dimensions, statistic, period, lag, delta):
        self.namespace = namespace
        self.metric = metric
        self.dimensions = string_to_dict(dimensions)
        self.statistic = statistic
        self.period = period
        self.lag = lag
        self.delta = delta

    def probe(self):
        logging.info('getting stats from cloudwatch')
        cw = create_connection()

        datapoint1_start_time = (datetime.datetime.utcnow() - timedelta(seconds=self.period) - timedelta(seconds=self.lag)) - timedelta(seconds=self.delta)
        datapoint1_end_time = datetime.datetime.utcnow() - timedelta(seconds=self.delta)
        datapoint1_stats = cw.get_metric_statistics(self.period, datapoint1_start_time, datapoint1_end_time,
                                                    self.metric, self.namespace, self.statistic, self.dimensions)

        datapoint2_start_time = datetime.datetime.utcnow() - timedelta(seconds=self.period) - timedelta(seconds=self.lag)
        datapoint2_end_time = datetime.datetime.utcnow()
        datapoint2_stats = cw.get_metric_statistics(self.period, datapoint2_start_time, datapoint2_end_time,
                                                    self.metric, self.namespace, self.statistic, self.dimensions)

        if len(datapoint1_stats) == 0 or len(datapoint2_stats) == 0:
            return []

        datapoint1_stat = datapoint1_stats[0]
        datapoint2_stat = datapoint2_stats[0]
        num_delta = datapoint2_stat[self.statistic] - datapoint1_stat[self.statistic]
        per_delta = (100 / datapoint2_stat[self.statistic]) * num_delta
        return [nagiosplugin.Metric('cloudwatchmetric', per_delta, '%')]


class CloudWatchMetricSummary(nagiosplugin.Summary):

    def __init__(self, namespace, metric, dimensions, statistic):
        self.namespace = namespace
        self.metric = metric
        self.dimensions = string_to_dict(dimensions)
        self.statistic = statistic

    def ok(self, results):
        full_metric = '%s:%s' % (self.namespace, self.metric)
        return 'CloudWatch Metric %s with dimensions %s' % (full_metric, self.dimensions)

    def problem(self, results):
        full_metric = '%s:%s' % (self.namespace, self.metric)
        return 'CloudWatch Metric %s with dimensions %s' % (full_metric, self.dimensions)


class CloudWatchMetricRatioSummary(nagiosplugin.Summary):

    def __init__(self, dividend_namespace, dividend_metric, dividend_dimensions, dividend_statistic, divisor_namespace, divisor_metric, divisor_dimensions, divisor_statistic):
        self.dividend_namespace = dividend_namespace
        self.dividend_metric = dividend_metric
        self.dividend_dimensions = dividend_dimensions
        self.dividend_statistic = dividend_statistic
        self.divisor_namespace = divisor_namespace
        self.divisor_metric = divisor_metric
        self.divisor_dimensions = divisor_dimensions
        self.divisor_statistic = divisor_statistic

    def ok(self, results):
        dividend_full_metric = '%s:%s' % (self.dividend_namespace, self.dividend_metric)
        divisor_full_metric = '%s:%s' % (self.divisor_namespace, self.divisor_metric)
        return 'Ratio: CloudWatch Metric %s with dimensions %s / CloudWatch Metric %s with dimensions %s' % (dividend_full_metric, self.dividend_dimensions, divisor_full_metric, self.divisor_dimensions)

    def problem(self, results):
        dividend_full_metric = '%s:%s' % (self.dividend_namespace, self.dividend_metric)
        divisor_full_metric = '%s:%s' % (self.divisor_namespace, self.divisor_metric)
        return 'Ratio: CloudWatch Metric %s with dimensions %s / CloudWatch Metric %s with dimensions %s' % (dividend_full_metric, self.dividend_dimensions, divisor_full_metric, self.divisor_dimensions)


class CloudWatchDeltaMetricSummary(nagiosplugin.Summary):

    def __init__(self, namespace, metric, dimensions, statistic, delta):
        self.namespace = namespace
        self.metric = metric
        self.dimensions = string_to_dict(dimensions)
        self.statistic = statistic
        self.delta = delta

    def ok(self, results):
        full_metric = '%s:%s' % (self.namespace, self.metric)
        return 'CloudWatch %d seconds Delta %s Metric with dimensions %s' % (self.delta, full_metric, self.dimensions)

    def problem(self, results):
        full_metric = '%s:%s' % (self.namespace, self.metric)
        return 'CloudWatch %d seconds Delta %s Metric with dimensions %s' % (self.delta, full_metric, self.dimensions)


class KeyValArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        kvs = {}
        for pair in values.split(','):
            kv = pair.split('=')
            kvs[kv[0]] = kv[1]
        setattr(namespace, self.dest, kvs)

@nagiosplugin.guarded
def main():

    argp = argparse.ArgumentParser(description='Nagios plugin to check cloudwatch metrics')

    argp.add_argument('-n', '--namespace', required=False, default=NAMESPACE,
                      help='namespace for cloudwatch metric')
    argp.add_argument('-m', '--metric', required=False, default=METRIC,
                      help='metric name')
    argp.add_argument('-d', '--dimensions', default=DIMENSIONS,
                      help='dimensions of cloudwatch metric in the format dimension=value[,dimension=value...]')
    argp.add_argument('-s', '--statistic', choices=['Average', 'Sum', 'SampleCount', 'Maximum', 'Minimum'], default='Average',
                      help='statistic used to evaluate metric')
    argp.add_argument('-p', '--period', default=60, type=int,
                      help='the period in seconds over which the statistic is applied')
    argp.add_argument('-l', '--lag', default=60,
                      help='delay in seconds to add to starting time for gathering metric. '
                           'useful for ec2 basic monitoring which aggregates over 5min periods')
    argp.add_argument('-r', '--ratio', default=False, action='store_true',
                      help='this activates ratio mode')
    argp.add_argument('--divisor-namespace',
                      help='ratio mode: namespace for cloudwatch metric of the divisor')
    argp.add_argument('--divisor-metric',
                      help='ratio mode: metric name of the divisor')
    argp.add_argument('--divisor-dimensions',
                      help='ratio mode: dimensions of cloudwatch metric of the divisor')
    argp.add_argument('--divisor-statistic', choices=['Average', 'Sum', 'SampleCount', 'Maximum', 'Minimum'],
                      help='ratio mode: statistic used to evaluate metric of the divisor')

    argp.add_argument('--delta', type=int,
                      help='time in seconds to build a delta mesurement')

    argp.add_argument('-w', '--warning', metavar='RANGE', default=0,
                      help='warning if threshold is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE', default=0,
                      help='critical if threshold is outside RANGE')
    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase verbosity (use up to 3 times)')

    args = argp.parse_args()

    if args.ratio:
        metric = CloudWatchRatioMetric(args.namespace, args.metric, args.dimensions, args.statistic, args.period, args.lag, args.divisor_namespace,  args.divisor_metric, args.divisor_dimensions, args.divisor_statistic)
        summary = CloudWatchMetricRatioSummary(args.namespace, args.metric, args.dimensions, args.statistic, args.divisor_namespace,  args.divisor_metric, args.divisor_dimensions, args.divisor_statistic)
    elif args.delta:
        metric = CloudWatchDeltaMetric(args.namespace, args.metric, args.dimensions, args.statistic, args.period, args.lag, args.delta)
        summary = CloudWatchDeltaMetricSummary(args.namespace, args.metric, args.dimensions, args.statistic, args.delta)
    else:
        metric = CloudWatchMetric(args.namespace, args.metric, args.dimensions, args.statistic, args.period, args.lag)
        summary = CloudWatchMetricSummary(args.namespace, args.metric, args.dimensions, args.statistic)

    check = nagiosplugin.Check(
        metric,
        nagiosplugin.ScalarContext('cloudwatchmetric', args.warning, args.critical),
        summary)
    check.main(verbose=args.verbose)

main()