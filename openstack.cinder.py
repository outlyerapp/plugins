#!/usr/bin/env python
"""
Update the settings block below
"""
import sys
import os
import requests
from keystoneclient.v2_0 import client
from keystoneclient import exceptions

# Settings
OS_USERNAME = ""
OS_TENANT_NAME = ""
OS_PASSWORD = ""
OS_AUTH_URL = "http://keystone.domain.com:5000/v2.0/"
CINDER_URL = 'http://127.0.0.1:8776/v2/'


def _get_keystone_token():
    token_id = []
    try:
        c_keystone = client.Client(username=OS_USERNAME,
                                   tenant_name=OS_TENANT_NAME,
                                   password=OS_PASSWORD,
                                   auth_url=OS_AUTH_URL,
                                   insecure=True)
        if not c_keystone.authenticate():
            raise Exception("Authentication failed")

    except:
        print "Plugin Failed!"
        sys.exit(2)

    token_id.append(c_keystone.auth_token)
    token_id.append(c_keystone.tenant_id)
    return token_id


auth_token_id_nova = _get_keystone_token()


def get_data(path):
    return requests.get(CINDER_URL + auth_token_id_nova[1] + path, headers=headers).json()


headers = {"X-Auth-Project-Id": OS_TENANT_NAME, "Content-Type": "application/json",
           "X-Auth-Token": auth_token_id_nova[0]}
try:
    quotas = get_data('/os-quota-sets/' + OS_TENANT_NAME + '/defaults')
    volumes = get_data('/volumes/detail')
    snapshots = get_data('/snapshots/detail')

except Exception, e:
    print "cinder is down!"
    sys.exit(2)

print "OK | quota_count=%s;;;; volume_count=%s;;;; snapshot_count=%s;;;;" % (
    len(quotas),
    len(volumes['volumes']),
    len(snapshots['snapshots'])
)