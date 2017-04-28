#!/usr/bin/env python

# Script to aid zfs performance tuning on Linux.  calculates rates from cumlitive values.
# Oliver Greenaway 2017
# Oytlyer.com

import sys
import os
import pickle 

############### config ##################
stats_files = {"arcstats_file": '/proc/spl/kstat/zfs/arcstats', "zilstats_file": '/proc/spl/kstat/zfs/zil', "dmustats_file": '/proc/spl/kstat/zfs/dmu_tx'}
cumulative_results_keywords = ["hits", "misses"]
stats_in_bytes = ['c', 'c_max']
discard_cumulative = True
convert_to_gb = True
tmp_dir = '/opt/dataloop/tmp/'
tmp_file = 'dataloop-zfs'

################ code #####################

def query_zfs(file_locations)
    """Queries zfs stats in proc
    accepts: List of files to query.  
    returns: dict of results from files with each metric as a key"""
    stats = {}
    for sfile, location in file_locations.iteritems():
        try:
            with open(sfile, 'r') as f:
                garbage = f.readline()
                header = f.readline()
                stats = f.read()
                for i in stats.split('\n')
                    stats[i.split[0]] = i.split[2]
        
        except Exception as E:
            print "CRITICAL - failed to parse arcstats: %s" % E
            sys.exit(2)
    
def bytes_to_gb(results):
    """ converts bytes to gb 
    accepts: dict of results
    returns: dict of results with bytes converted to gb"""
    for key in results:
        for metric in state_in_bytes:
            if key == metric:
                results[key] =  str(round(float(results[key]) / 1024 / 1024 / 1024, 2) + GB)
    return results

def get_last_resuls(results_file):
    """ recovers a dict of the previous results form a tempory file
    accepts: location of tempory file
    returns: dict of results form that file"""
    with open(results_file, 'rb') as handle:
        b = pickle.load(handle)
    return b

def save_current_results(results_filei, results):
    """Saves current results to a tempory file
    accepts: results to save, location of tempory file"""
    with open(resuts_files, 'wb') as handle:
        pickle.dump(results, handle, protocol=pickle.HIGHEST_PROTOCOL)

def add_rate_results(results, old_results, cumulative_results, discard_cumulative):
    """adds rate results to a results dict, optionaly overwriting cumulative result
    accepts: results dict, old results dict list of cumulative result keywords to process 
    and weather to throw away the cumulative results 
    returns: results dict"""
   for metric, value in results.iteritems():
       for item in cumlative_results:
           if item in metric:
               if discard_cumulative:
                   results[metric] = results[metric] - old_results[metric]
               else:
                   results[(metric + "-rate")] = results[metric] - old_results[metric]
    return results
                   
                   
if not os.path.exists(tmp_dir):
    print "tempory directory does not extst!  exiting..."
    sys.exit(3)

current_results = query_zfs(stats_files)
last_results = get_last_results((tmp_dir + tmp_file)
save_current_results(current_results)
rateifyed_results = add_rate_results(current_results, last_results, cumulative_results_keywords, discarde_cumulative)
if convert_to_gb:
    rateifyed_results = bytes_to_gb(rateifyed_results)

message = "OK | "

#for line in stats_lines:
#    fields = line.split()
#    if len(fields) > 0:
#        for stat in gbstats:
#            if stat == fields[0]:
#                message += "%s=%sgb;;;; " % (fields[0] + '_GB', bytes_to_gb(fields[2]))
#        message += "%s=%s;;;; " % (fields[0], fields[2])
#

for key in rateifyed_results:
    message += "%s=%s;;;; " % (key, rateifyed_results[key])



print message
