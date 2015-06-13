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

headers = {"X-Auth-Project-Id": OS_TENANT_NAME, "Content-Type": "application/json",
           "X-Auth-Token": auth_token_id_nova[0]}
try:
    resp = requests.get('http://127.0.0.1:8774/v2/' + auth_token_id_nova[1] + "/servers/detail", headers=headers).json()
except:
    print "nova is down!"
    sys.exit(2)

print "OK | instance_count=%s;;;;" % len(resp['servers'])
