#!/usr/bin/env python

import sys
import time
import optparse
import re
import os
import requests
from requests.auth import HTTPDigestAuth
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError, e:
        print e
        sys.exit(2)


def optional_arg(arg_default):
    def func(option, opt_str, value, parser):
        if parser.rargs and not parser.rargs[0].startswith('-'):
            val = parser.rargs[0]
            parser.rargs.pop(0)
        else:
            val = arg_default
        setattr(parser.values, option.dest, val)
    return func


def performance_data(perf_data, params):
    data = ''
    if perf_data:
        data = " |"
        for p in params:
            p += (None, None, None, None)
            param, param_name, warning, critical = p[0:4]
            data += "%s=%s" % (param_name, str(param))
            if warning or critical:
                warning = warning or 0
                critical = critical or 0
                data += ";%s;%s" % (warning, critical)
                
            data += " "
            
    return data


def numeric_type(param):
    """
    Checks parameter type
    True for float; int or null data; false otherwise
    
    :param param: input param to check
    """
    if type(param) is float or type(param) is int or param is None:
        return True
    return False


def check_levels(param, warning, critical, message, ok=[]):
    """
    Checks error level
    
    :param param: input param
    :param warning: watermark for warning
    :param critical: watermark for critical
    :param message: message to be reported to nagios
    :param ok: watermark for ok level
    """
    if numeric_type(critical) and numeric_type(warning):
        if param >= critical:
            print "CRITICAL - " + message
            sys.exit(2)
        elif param >= warning:
            print "WARNING - " + message
            sys.exit(1)
        else:
            print "OK - " + message
            sys.exit(0)
    else:
        if param in critical:
            print "CRITICAL - " + message
            sys.exit(2)

        if param in warning:
            print "WARNING - " + message
            sys.exit(1)

        if param in ok:
            print "OK - " + message
            sys.exit(0)

        # unexpected param value
        print "CRITICAL - Unexpected value : %d" % param + "; " + message
        return 2


def get_digest_auth_json(host, port, uri, user, password, payload):
    """
    HTTP GET with Digest Authentication. Returns JSON result.
    Base URI of http://{host}:{port}/management is used
    
    :param host: JBossAS hostname
    :param port: JBossAS HTTP Management Port
    :param uri: URL fragment
    :param user: management username
    :param password: password
    :param payload: JSON payload 
    """
    try:
        url = base_url(host, port) + uri
        res = requests.get(url, params=payload, auth=HTTPDigestAuth(user, password))
        data = res.json()
        
        try:    
            outcome = data['outcome']
            if outcome == "failed":
                print "CRITICAL - Unexpected value : %s" % data
                sys.exit(2)
        except KeyError: pass

        return data
    except Exception, e:
        # The server could be down; make this CRITICAL.
        print "CRITICAL - JbossAS Error:", e
        sys.exit(2)


def post_digest_auth_json(host, port, uri, user, password, payload):
    """
    HTTP POST with Digest Authentication. Returns JSON result.
    Base URI of http://{host}:{port}/management is used
    
    :param host: JBossAS hostname
    :param port: JBossAS HTTP Management Port
    :param uri: URL fragment
    :param user: management username
    :param password: password
    :param payload: JSON payload 
    """
    try:
        url = base_url(host, port) + uri
        headers = {'content-type': 'application/json'}        
        res = requests.post(url, data=json.dumps(payload), headers=headers, auth=HTTPDigestAuth(user, password))
        data = res.json()
        
        try:    
            outcome = data['outcome']
            if outcome == "failed":
                print "CRITICAL - Unexpected value : %s" % data
                sys.exit(2)
        except KeyError: pass

        return data
    except Exception, e:
        # The server could be down; make this CRITICAL.
        print "CRITICAL - JbossAS Error:", e
        sys.exit(2)


def base_url(host, port):
    """
    Provides base URL for HTTP Management API
    
    :param host: JBossAS hostname
    :param port: JBossAS HTTP Management Port
    """
    url = "http://{host}:{port}/management".format(host=host, port=port)
    return url


def main(argv):
    
    global ds_stat_types
    ds_stat_types = ['ActiveCount', 'AvailableCount', 'AverageBlockingTime', 'AverageCreationTime',
                     'CreatedCount', 'DestroyedCount', 'MaxCreationTime', 'MaxUsedCount',
                     'MaxWaitTime', 'TimedOut', 'TotalBlockingTime', 'TotalCreationTime']
    
    p = optparse.OptionParser(conflict_handler="resolve", description="This Nagios plugin checks the health of JBossAS.")

    p.add_option('-H', '--host', action='store', type='string', dest='host', default='127.0.0.1', help='The hostname you want to connect to')
    p.add_option('-P', '--port', action='store', type='int', dest='port', default=9990, help='The port JBoss management console is runnung on')
    p.add_option('-u', '--user', action='store', type='string', dest='user', default=None, help='The username you want to login as')
    p.add_option('-p', '--pass', action='store', type='string', dest='passwd', default=None, help='The password you want to use for that user')
    p.add_option('-W', '--warning', action='store', dest='warning', default=None, help='The warning threshold we want to set')
    p.add_option('-C', '--critical', action='store', dest='critical', default=None, help='The critical threshold we want to set')
    p.add_option('-A', '--action', action='store', type='choice', dest='action', default='server_status', help='The action you want to take',
                 choices=['server_status', 'heap_usage', 'non_heap_usage', 'eden_space_usage',
                          'old_gen_usage', 'perm_gen_usage', 'code_cache_usage', 'gctime',
                          'queue_depth', 'datasource', 'xa_datasource', 'threading'])
    p.add_option('-D', '--perf-data', action='store_true', dest='perf_data', default=False, help='Enable output of Nagios performance data')
    p.add_option('-g', '--gctype', action='store', dest='gc_type', default='PS_MarkSweep', help='The memory pool type to check for gctime')
    p.add_option('-q', '--queuename', action='store', dest='queue_name', default=None, help='The queue name for which you want to retrieve queue depth')
    p.add_option('-d', '--datasource', action='store', dest='datasource_name', default=None, help='The datasource name for which you want to retrieve statistics')
    p.add_option('-s', '--poolstats', action='store', dest='ds_stat_type', default=None, help='The datasource pool statistics type')
    p.add_option('-t', '--threadstats', action='store', dest='thread_stat_type', default=None, help='The threading statistics type')

    options, arguments = p.parse_args()
    host = options.host
    port = options.port
    user = options.user
    passwd = options.passwd
    gc_type = options.gc_type
    queue_name = options.queue_name
    datasource_name = options.datasource_name
    ds_stat_type = options.ds_stat_type
    thread_stat_type = options.thread_stat_type
    
    if (options.action == 'server_status'):
        warning = str(options.warning or "")
        critical = str(options.critical or "")
    else:
        warning = float(options.warning or 0)
        critical = float(options.critical or 0)

    action = options.action
    perf_data = options.perf_data

    if action == "server_status":
        return check_server_status(host, port, user, passwd, warning, critical, perf_data)
    elif action == "gctime":
        return check_gctime(host, port, user, passwd, gc_type, warning, critical, perf_data)
    elif action == "queue_depth":
        return check_queue_depth(host, port, user, passwd, queue_name, warning, critical, perf_data)
    elif action == "heap_usage":
        return check_heap_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "non_heap_usage":
        return check_non_heap_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "eden_space_usage":
        return check_eden_space_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "old_gen_usage":
        return check_old_gen_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "perm_gen_usage":
        return check_perm_gen_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "code_cache_usage":
        return check_code_cache_usage(host, port, user, passwd, warning, critical, perf_data)
    elif action == "datasource":
        return check_non_xa_datasource(host, port, user, passwd, datasource_name, ds_stat_type, warning, critical, perf_data)
    elif action == "xa_datasource":
        return check_xa_datasource(host, port, user, passwd, datasource_name, ds_stat_type, warning, critical, perf_data)
    elif action == "threading":
        return check_threading(host, port, user, passwd, thread_stat_type, warning, critical, perf_data)
    else:
        return 2


def exit_with_general_warning(e):
    """
    
    :param e: exception
    """
    if isinstance(e, SystemExit):
        return e
    elif isinstance(e, ValueError):
        print "WARNING - General JbossAS Error:", e
        sys.exit(1)
    else:
        print "WARNING - General JbossAS warning:", e
    return 1


def exit_with_general_critical(e):
    if isinstance(e, SystemExit):
        return e
    elif isinstance(e, ValueError):
        print "CRITICAL - General JbossAS Error:", e
        sys.exit(2)
    else:
        print "CRITICAL - General JbossAS Error:", e
    return 2


def check_server_status(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or "reload-required"
    critical = critical or ""
    ok = "running"
    
    try:
        payload = {'operation': 'read-attribute', 'name': 'server-state'}
        res = post_digest_auth_json(host, port, "", user, passwd, payload)
        res = res['result']
        
        message = "Server Status '%s'" % res
        message += performance_data(perf_data, [(res, "server_status", warning, critical)])
    
        return check_levels(res, warning, critical, message, ok)
    except Exception, e:
        return exit_with_general_critical(e)


def get_memory_usage(host, port, user, passwd, is_heap, memory_value):
    try:
        payload = {'include-runtime': 'true'}
        url = "/core-service/platform-mbean/type/memory"
        
        data = get_digest_auth_json(host, port, url, user, passwd, payload)
        
        if is_heap:
            data = data['heap-memory-usage'][memory_value] / (1024 * 1024)
        else:
            data = data['non-heap-memory-usage'][memory_value] / (1024 * 1024)
        
        return data
    except Exception, e:
        return exit_with_general_critical(e)

def check_heap_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 80
    critical = critical or 90
    
    try:
        used_heap = get_memory_usage(host, port, user, passwd, True, 'used')
        max_heap = get_memory_usage(host, port, user, passwd, True, 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "Heap Memory Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "heap_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def check_non_heap_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 80
    critical = critical or 90
    
    try:
        used_heap = get_memory_usage(host, port, user, passwd, False, 'used')
        max_heap = get_memory_usage(host, port, user, passwd, False, 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "Non Heap Memory Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "non_heap_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def get_memory_pool_usage(host, port, user, passwd, pool_name, memory_value):
    try:
        payload = {'include-runtime': 'true', 'recursive':'true'}
        url = "/core-service/platform-mbean/type/memory-pool"
        
        data = get_digest_auth_json(host, port, url, user, passwd, payload)
        usage = data['name'][pool_name]['usage'][memory_value] / (1024 * 1024)
        
        return usage
    except Exception, e:
        return exit_with_general_critical(e)


def check_eden_space_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 80
    critical = critical or 90
    
    try:
        used_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Eden_Space', 'used')
        max_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Eden_Space', 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "PS_Eden_Space Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "eden_space_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def check_old_gen_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 80
    critical = critical or 90
    
    try:
        used_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Old_Gen', 'used')
        max_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Old_Gen', 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "PS_Old_Gen Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "old_gen_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)


def check_perm_gen_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 90
    critical = critical or 95
    
    try:
        used_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Perm_Gen', 'used')
        max_heap = get_memory_pool_usage(host, port, user, passwd, 'PS_Perm_Gen', 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "PS_Perm_Gen Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "perm_gen_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def check_code_cache_usage(host, port, user, passwd, warning, critical, perf_data):
    warning = warning or 90
    critical = critical or 95
    
    try:
        used_heap = get_memory_pool_usage(host, port, user, passwd, 'Code_Cache', 'used')
        max_heap = get_memory_pool_usage(host, port, user, passwd, 'Code_Cache', 'max')
        percent = round((float(used_heap * 100) / max_heap), 2)
        
        message = "Code_Cache Utilization %s of %s MiB" % (used_heap, max_heap)
        message += performance_data(perf_data, [(percent, "code_cache_usage", warning, critical)])
    
        return check_levels(percent, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)


def check_gctime(host, port, user, passwd, gc_type, warning, critical, perf_data):
    # Make sure you configure right values for your application    
    warning = warning or 500
    critical = critical or 1000
    
    try:
        if gc_type not in ['PS_MarkSweep', 'PS_Scavenge']:
            return exit_with_general_critical("The GC type of '%s' is not valid" % gc_type)
            
        payload = {'include-runtime': 'true', 'recursive':'true'}
        url = "/core-service/platform-mbean/type/garbage-collector"
        res = get_digest_auth_json(host, port, url, user, passwd, payload)
        gc_time = res['name'][gc_type]['collection-time']
        gc_count = res['name'][gc_type]['collection-count']
        
        avg_gc_time = 0
         
        if gc_count > 0:
            avg_gc_time = gc_time / gc_count
        
        message = "GC '%s' collection-time %s collection-count %s avg-time %s" % (gc_type, gc_time, gc_count, avg_gc_time)
        message += performance_data(perf_data, [(avg_gc_time, "gctime", warning, critical)])
    
        return check_levels(avg_gc_time, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)
    

def check_threading(host, port, user, passwd, thread_stat_type, warning, critical, perf_data):
    warning = warning or 100
    critical = critical or 200
    
    try:
        if thread_stat_type not in ['thread-count', 'peak-thread-count', 'total-started-thread-count', 'daemon-thread-count']:
            return exit_with_general_critical("The thread statistics value type of '%s' is not valid" % thread_stat_type)
            
        payload = {'include-runtime': 'true'}
        url = "/core-service/platform-mbean/type/threading"
        
        data = get_digest_auth_json(host, port, url, user, passwd, payload)
        data = data[thread_stat_type]
        
        message = "Threading Statistics '%s':%s " % (thread_stat_type, data)
        message += performance_data(perf_data, [(data, "threading", warning, critical)])
    
        return check_levels(data, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)


def check_queue_depth(host, port, user, passwd, queue_name, warning, critical, perf_data):
    warning = warning or 100
    critical = critical or 200
    
    try:    
        if queue_name is None:
            return exit_with_general_critical("The queue name '%s' is not valid" % queue_name)
            
        payload = {'include-runtime': 'true', 'recursive':'true'}
        url = "/subsystem/messaging/hornetq-server/default/jms-queue/" + queue_name
        
        data = get_digest_auth_json(host, port, url, user, passwd, payload)
        queue_depth = data['message-count']
        
        message = "Queue %s depth %s" % (queue_name, queue_depth)
        message += performance_data(perf_data, [(queue_depth, "queue_depth", warning, critical)])
    
        return check_levels(queue_depth, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def get_datasource_stats(host, port, user, passwd, is_xa, ds_name, ds_stat_type):
    try:    
        if ds_name is None:
            return exit_with_general_critical("The ds_name name '%s' is not valid" % ds_name)
        if ds_stat_type not in ds_stat_types:
            return exit_with_general_critical("The datasource statistics type of '%s' is not valid" % ds_stat_type)
            
        payload = {'include-runtime': 'true', 'recursive':'true'}
        if is_xa:
            url = "/subsystem/datasources/xa-data-source/" + ds_name + "/statistics/pool/"
        else:
            url = "/subsystem/datasources/data-source/" + ds_name + "/statistics/pool/"
        
        data = get_digest_auth_json(host, port, url, user, passwd, payload)
        data = data[ds_stat_type]
        
        return data
    except Exception, e:
        return exit_with_general_critical(e)


def check_non_xa_datasource(host, port, user, passwd, ds_name, ds_stat_type, warning, critical, perf_data):
    warning = warning or 0
    critical = critical or 10
    
    try:    
        data = get_datasource_stats(host, port, user, passwd, False, ds_name, ds_stat_type)
        
        message = "DataSource %s %s" % (ds_stat_type, data)
        message += performance_data(perf_data, [(data, "datasource", warning, critical)])
        return check_levels(data, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def check_xa_datasource(host, port, user, passwd, ds_name, ds_stat_type, warning, critical, perf_data):
    warning = warning or 0
    critical = critical or 10
    
    try:    
        data = get_datasource_stats(host, port, user, passwd, True, ds_name, ds_stat_type)

        message = "XA DataSource %s %s" % (ds_stat_type, data)
        message += performance_data(perf_data, [(data, "xa_datasource", warning, critical)])
        return check_levels(data, warning, critical, message)
    except Exception, e:
        return exit_with_general_critical(e)

def build_file_name(host, action):
    # done this way so it will work when run independently and from shell
    module_name = re.match('(.*//*)*(.*)\..*', __file__).group(2)
    return "/tmp/" + module_name + "_data/" + host + "-" + action + ".data"


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


def write_values(file_name, string):
    f = None
    try:
        f = open(file_name, 'w')
    except IOError, e:
        # try creating
        if (e.errno == 2):
            ensure_dir(file_name)
            f = open(file_name, 'w')
        else:
            raise IOError(e)
    f.write(string)
    f.close()
    return 0


def read_values(file_name):
    data = None
    try:
        f = open(file_name, 'r')
        data = f.read()
        f.close()
        return 0, data
    except IOError, e:
        if (e.errno == 2):
            # no previous data
            return 1, ''
    except Exception, e:
        return 2, None


def calc_delta(old, new):
    delta = []
    if (len(old) != len(new)):
        raise Exception("unequal number of parameters")
    for i in range(0, len(old)):
        val = float(new[i]) - float(old[i])
        if val < 0:
            val = new[i]
        delta.append(val)
    return 0, delta


def maintain_delta(new_vals, host, action):
    file_name = build_file_name(host, action)
    err, data = read_values(file_name)
    old_vals = data.split(';')
    new_vals = [str(int(time.time()))] + new_vals
    delta = None
    try:
        err, delta = calc_delta(old_vals, new_vals)
    except:
        err = 2
    write_res = write_values(file_name, ";" . join(str(x) for x in new_vals))
    return err + write_res, delta

sys.exit(main(sys.argv[1:]))
