#!/usr/bin/env python

import psutil
import re
import time
import sys
from traceback import format_exception

# Set your regular expression filter to match an application's cmdline string
# Set DEBUG to True if you would like to print all of the data objects and
# return the stacktrace.

FILTER = 'CHANGE_ME'
DEBUG = False


def compare_list_strings(a):
    """
    Compare all strings in a given iterable (list, array)

    :arg a: array-like data structure

    :return bool: Return False if an array item is not the same as the others.
    Otherwise, return True
    """
    if len(a) <= 1:
        return True
    else:
        for i in range(0, len(a)):
            if a[0] != a[i]:
                return False
        return True


def mb(num):
    """
    Convert bytes to megabytes

    :arg num: int|float: data in bytes

    :return float: data in megabytes
    """

    return num / 1024.0 / 1024.0


class ApplicationProfiler(object):
    """

    Takes a regex filter and provides metrics for matched processes
    """

    def __init__(self, search_filter):
        """
        :ivar search_filter: string: regular expression filter to match against
        the cmdline string for the process

        :ivar profile: dict: A dictionary containing lists, with each list
        mapping to a given metric

        :ivar profile['full_command']: list: The cmdline value as a string
        :ivar profile['num_threads']: list: The number of threads currently
        used

        :ivar profile['cpu_percent']: list: A float representing the current
        system-wide CPU utilization as a percentage

        :ivar profile['memory_percent']: list: Compare physical system memory
        to process resident memory (RSS) and calculate process memory
        utilization as a percentage.

        :ivar profile['rss']: list: Resident Set Size (memory) in MB

        :ivar profile['vms']: list: Virtual Memory Size in MB

        :ivar profile['num_fds']: list: Number of file descriptors used

        :ivar profile['io_counters_read']: list: Number of read io counters

        :ivar profile['io_counters_write']: list: Number of write io counters

        :ivar current_time: float: Current time (epoch)
        """
        self.search_filter = search_filter
        self.profile = {}
        self.p_name = None
        self.profile['full_command'] = []
        self.profile['num_threads'] = []
        self.profile['cpu_percent'] = []
        self.profile['rss'] = []
        self.profile['vms'] = []
        self.profile['memory_percent'] = []
        self.profile['connections'] = []
        self.profile['num_fds'] = []
        self.profile['io_counters_read'] = []
        self.profile['io_counters_write'] = []
        self.current_time = time.time()
        self._build_profile_result = self._build_profile()

    def _build_profile(self):
        """
        Builds an array for each metric and inserts into the profile dict.

        :return bool: Test if filter found one or more processes on the system
        """
        found = False

        for proc in psutil.process_iter():
            try:
                data = proc.as_dict()
            except psutil.NoSuchProcess:
                continue

            if DEBUG:
                print("Data Object: {data}\n".format(data=data))

            if data['cmdline']:
                full_command = " ".join(data['cmdline'])
            else:
                full_command = ''

            if re.search(self.search_filter, full_command) and not re.search(
                '/opt/dataloop', full_command
            ):
                found = True
                self.p_name = data['name'].lower()
                self.profile['full_command'].append(full_command)

                if 'num_threads' in data:
                    if data['num_threads']:
                        self.profile['num_threads'].append(
                            float(data['num_threads'])
                        )
                    else:
                        self.profile['num_threads'].append(0.0)
                else:
                    self.profile['num_threads'].append(0.0)

                if 'cpu_percent' in data:
                    if data['cpu_percent']:
                        self.profile['cpu_percent'].append(
                            float(data['cpu_percent'])
                        )
                    else:
                        self.profile['cpu_percent'].append(0.0)
                else:
                    self.profile['cpu_percent'].append(0.0)

                if 'memory_percent' in data:
                    if data['memory_percent']:
                        self.profile['memory_percent'].append(
                            float(data['memory_percent'])
                        )
                    else:
                        self.profile['memory_percent'].append(0.0)
                else:
                    self.profile['memory_percent'].append(0.0)

                if 'memory_info' in data:
                    if data['memory_info']:
                        if data['memory_info'][0]:
                            self.profile['rss'].append(
                                mb(float(data['memory_info'][0]))
                            )
                        else:
                            self.profile['rss'].append(0.0)
                        if data['memory_info'][1]:
                            self.profile['vms'].append(
                                mb(float(data['memory_info'][1]))
                            )
                        else:
                            self.profile['vms'].append(0.0)
                    else:
                        self.profile['rss'].append(0.0)
                        self.profile['vms'].append(0.0)
                else:
                    self.profile['rss'].append(0.0)
                    self.profile['vms'].append(0.0)

                if 'num_fds' in data:
                    if data['num_fds']:
                        self.profile['num_fds'].append(
                            float(data['num_fds'])
                        )
                    else:
                        self.profile['num_fds'].append(0.0)
                else:
                    self.profile['num_fds'].append(0.0)

                if 'io_counters' in data:
                    if data['io_counters']:
                        if data['io_counters'][0]:
                            self.profile['io_counters_read'].append(
                                float(data['io_counters'][0])
                            )
                        else:
                            self.profile['io_counters_read'].append(0.0)
                        if data['io_counters'][1]:
                            self.profile['io_counters_write'].append(
                                float(data['io_counters'][1])
                            )
                        else:
                            self.profile['io_counters_read'].append(0.0)
                    else:
                        self.profile['io_counters_read'].append(0.0)
                        self.profile['io_counters_write'].append(0.0)
                else:
                    self.profile['io_counters_read'].append(0.0)
                    self.profile['io_counters_write'].append(0.0)

        return found

    def show_results(self):
        """
        Print output of check.

        This method was inspired by the base plugin.
        """

        if DEBUG:
            print("Profile Object: {profile}\n".format(profile=self.profile))

        if self._build_profile_result is False:
            print("CRITICAL | Application not found")
            sys.exit(2)

        output = "OK | "
        for key, val in self.profile.iteritems():

            if key == 'full_command':

                if compare_list_strings(val):
                    output += "{name}.{key}.consistency=1;;;; ".format(
                        name=self.p_name,
                        key=key
                    )
                else:
                    output += "{name}.{key}.consistency=0;;;; ".format(
                        name=self.p_name,
                        key=key
                    )
            else:

                # An array of zeros gives you an empty array
                if len(val) == 0:
                    mx = 0.0
                    mn = 0.0
                    av = 0.0
                else:
                    mx = max(val)
                    mn = min(val)
                    av = float(sum(val)) / float(len(val))

                if key == 'rss' or key == 'vms':
                    output += "{name}.{key}.high={mx}mb;;;; ".format(
                        name=self.p_name,
                        key=key,
                        mx=mx
                    )

                    output += "{name}.{key}.low={mn}mb;;;; ".format(
                        name=self.p_name,
                        key=key,
                        mn=mn
                    )

                    output += "{name}.{key}.average={av}mb;;;; ".format(
                        name=self.p_name,
                        key=key,
                        av=av
                    )
                elif key == 'memory_percent':
                    output += "{name}.{key}.high={mx}%;;;; ".format(
                        name=self.p_name,
                        key=key,
                        mx=mx
                    )

                    output += "{name}.{key}.low={mn}%;;;; ".format(
                        name=self.p_name,
                        key=key,
                        mn=mn
                    )

                    output += "{name}.{key}.average={av}%;;;; ".format(
                        name=self.p_name,
                        key=key,
                        av=av
                    )
                else:

                    output += "{name}.{key}.high={mx};;;; ".format(
                        name=self.p_name,
                        key=key,
                        mx=mx
                    )

                    output += "{name}.{key}.low={mn};;;; ".format(
                        name=self.p_name,
                        key=key,
                        mn=mn
                    )

                    output += "{name}.{key}.average={av};;;; ".format(
                        name=self.p_name,
                        key=key,
                        av=av
                    )

        output += "{name}.process_num={num};;;;".format(
            name=self.p_name,
            num=len(self.profile['full_command'])
        )

        print(output)


try:
    ap = ApplicationProfiler(FILTER)
    ap.show_results()
except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print("CRITICAL | Plugin Failure: Exception: {exception_type} "
          "Msg: {msg}".format(exception_type=exc_type.__name__, msg=e))
    if DEBUG:
        lines = format_exception(exc_type, exc_value, exc_traceback)
        s = ''.join(line for line in lines)
        lines = s.split('\n')
        for line in lines:
            print(line)

    sys.exit(2)
