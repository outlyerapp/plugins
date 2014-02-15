#!/usr/bin/env python

import os
import sys
import subprocess

tmp_space = "/tmp/"


def main():
    if len(sys.argv) == 2:
        url = sys.argv[1]
    else:
        print 'No URL specified to check'
        sys.exit(1)

    cmd = "wget -O " + tmp_space + "/index.html http://wordpress.org/download/"
    try:
        wget_process = subprocess.call(cmd, shell=True)

    except:
        print "Could not get http://wordpress.org/download/"
        sys.exit(1)
    
    version = ""
    
    f = open(tmp_space + 'index.html', 'r')
    for line in f.readlines():
        if line.startswith('			<p class="intro">The latest stable release of WordPress'):
            try:
                left_paren = line.index('(') 
            except:
                os.remove(tmp_space + 'index.html')
                print "Did not find left paren in http://wordpress.org/download/"
                sys.exit(1)
            try:
                right_paren = line.index(')')
            except:
                os.remove(tmp_space + 'index.html')
                print "Did not find right paren in http://wordpress.org/download/"
                sys.exit(1)
            version = line[left_paren+1:right_paren]
    f.close()

    if version == "":
        os.remove(tmp_space + 'index.html')
        print "Could not ascertain current version number on wordpress.org"
        sys.exit(1)

    version = version[8:]   
 
    os.remove(tmp_space + 'index.html')
   
    cmd = "wget -O " + tmp_space + "index.html " + url 
    wget_proc = subprocess.call(cmd, shell=True)

    url_line = ""
    f = open(tmp_space + 'index.html','r')
    for line in f.readlines():
        if line.startswith('<meta name="generator" content="WordPress'):
            try:
                left_paren = line.index('WordPress')
            except:
                os.remove(tmp_space + 'index.html')
                print "Left paren on %s not found." % url
                sys.exit(1)
            try:
                right_paren = line.index('/>')
            except:
                os.remove(tmp_space + 'index.html')
                print "Right paren on %s not found." % url
                sys.exit(1)
            url_line = line[left_paren+10:right_paren-2]

    os.remove(tmp_space + 'index.html')

    if version == url_line:
        print "Latest Wordpress Version %s is running on %s" % (version, url)
        sys.exit(0)
    else:
        print "Latest Wordpress Version is %s. %s version cannot be determined." % (version, url)
        sys.exit(1)

main()

