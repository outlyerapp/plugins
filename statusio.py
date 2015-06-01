#!/usr/bin/env python
import requests
import time
import json
import socket
import sys

"""
   The only config needed is the 4 variables below
   This does not manage individual containers status, it's all or nothing
"""

#Config - change these bits, hope for best.
api_id = "your-api-id"
api_key = "your-api-key"
statuspage_id = "your-status-page-id"
checks = {
    'endpoint 1': { 'id': "component-id", 'check_type': 'url', 'target' : 'https://agent.dataloop.io'},
    'endpoint 2': { 'id': "component-id", 'check_type': 'tcp', 'target' : 'graphite.dataloop.io:2003'},
}

#Useful Methods
def get_url(url,headers,options):
    session = requests.session()
    adaptor = requests.adapters.HTTPAdapter(max_retries=options['retries'])
    session.mount('http://', adaptor)
    session.mount('https//', adaptor)
    tried = 0

    """ 
    If it fails to connect to the server it will try the number of retries in the options
    If a http Error comes in it will try again until it reaches the options retry
    """
    while True:
        try:
            res = requests.get(url, headers=headers, timeout=options['timeout'])
            res.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if tried < options['retries']:
                tried += 1
                time.sleep(options['pause'])
                continue 
            else:
                return {'error': "Bad response", 'status_code': res.status_code, 'id': 1}
        except requests.exceptions.ConnectionError as e:
            return {'error': "Can't connect to domain", 'status_code': 500, 'id': '2'}
        except requests.exceptions.Timeout as e:
            return {'error': "Timeout", 'status_code': 500, 'id': '3'}
        break
    return res


def check_tcp(host, port, options):
    tried = 0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(options['timeout'])
    while True:
        result = sock.connect_ex((host,port))
        if result == 0:
            return True
        else:
            if tried < options['retries']:
                tried += 1
                time.sleep(opetions['pause'])
                continue
            else:
                break
    return False


# Class for all things status.io
class Statusio:
    #Constants
    DEFAULT_OPTS = {
        'timeout': 30,
        'retries': 3,
        'pause': 10
    }
    STATUSIO_API = "https://api.status.io/v2/"
    STATUS_SUMMARY = "status/summary/"
    COMPONENT_LIST = "component/list/"
    COMPONENT_STATUS_UPDATE = "component/status/update"
    #Codes That Status.io accepts
    STATUSIO_CODES = {
        'Operational': 100,
        'Planned Maintenance': 200,
        'Degraded Performance': 300,
        'Partial Service Disruption': 400,
        'Service Disruption': 500,
        'Security Event': 600
    }


    #Set up, api calls etc
    def __init__(self, api_id, api_key, status_page_id, options={}):
        
        self.api_id = api_id
        self.api_key = api_key
        self.status_page_id = status_page_id

        #Set defaults then update options
        self.options = self.DEFAULT_OPTS.copy()
        self.options.update(options)

        #Set up API headers
        self.headers = {
            'x-api-id': self.api_id, 
            'x-api-key': self.api_key, 
            'content-type': 'application/json'
        }
        self.infrastructure = {}
        self.nagios = {}
    
    #Return dict of infrastructure
    def get_infrastructure(self):
        uri = self.STATUSIO_API + self.COMPONENT_LIST + self.status_page_id
        comp_resp = get_url(uri, self.headers, self.options)
        #Convert response to structure that's useful
        #need to check for error not status code
        if 'error' not in comp_resp:
                        
            for component in comp_resp.json()['result']:
                contdetails = {}
                for container in component['containers']:
                    contdetails.update({container['name']: {'id': container['_id'], 'current_status': self.get_current_status(container['_id'], component['_id']) }}) 

                compdetails = {component['name']: { 'id': component['_id'], 'containers': contdetails}}
                self.infrastructure.update(compdetails)
        else:
            self.nagios_output(3,"no response from status.io")
        return self.infrastructure


    def get_containers(self, component_id):
        for name,component in self.infrastructure.iteritems():
            if component['id'] == component_id:
                return component['containers']


    def get_current_status(self, container_id,component_id):
        uri = self.STATUSIO_API + self.STATUS_SUMMARY + self.status_page_id
        response = get_url(uri, self.headers, self.options)
        if 'error' not in response:
            for component in response.json()['result']['status']:
                if component['id'] == component_id:
                    for container in component['containers']:
                        if container['id'] == container_id:
                            return container['status_code']
        else: 
            self.nagios_output(2, "no response from status.io")


    def incident_status_code_from_status_code(self,code):
        if code < 400:
            return self.STATUSIO_CODES['Operational']
        elif code >= 400 and code < 500:
            return self.STATUSIO_CODES['Partial Service Disruption']
        else:
            return self.STATUSIO_CODES['Service Disruption']


    def status_update(self, components, containers, reason, status):
        try:
            message = {
                "statuspage_id": self.status_page_id,
                "components": components,
                "containers": containers,
                "details": reason,
                "current_status": status
            }

            uri = self.STATUSIO_API + self.COMPONENT_STATUS_UPDATE

            data = json.dumps(message) 
            r = requests.post(uri, data=data, headers=self.headers)
            return r.status_code
        except requests.exceptions.RequestException as e:
            # A serious problem happened, like an SSLError or InvalidURL
            return "Error: {}".format(e)

    
    def nagios_output(self, exit_code, msg=""):
        if exit_code == 0:
            # Convert self.nagios into perf strings
            perf_string = ""
            for check,value in self.nagios.iteritems():
                perf_string += " " + check.replace(" ", "_").lower() + "=" + str(value['elapsed']) +"ms;;;;"
            print "OK |" + perf_string
            sys.exit(0)
        elif exit_code == 1:
            print "WARNING " + msg +" |"
            sys.exit(1)
        elif exit_code == 2:
            print "CRITICAL " + msg +" |"
            sys.exit(2)
        elif exit_code == 3:
            print "UNKNOWN " + msg +" |"
            sys.exit(3)


# Main
statusio = Statusio(api_id, api_key, statuspage_id)

#Get the current infrastructure and status and then store it in the statusio obj
statusio.get_infrastructure()

#Evaluate Checks 
for check,details in checks.iteritems():
    if details['check_type'] == 'url':
        resp = get_url(details['target'], statusio.headers, statusio.options)
        if 'error' not in resp:
            details['status'] = statusio.incident_status_code_from_status_code(resp.status_code)
            statusio.nagios.update({check: {'elapsed': resp.elapsed.microseconds / 1000}})
        else:
            details['status'] = statusio.incident_status_code_from_status_code(500)
    elif details['check_type'] == 'tcp':
        if check_tcp(details['target'].split(":")[0],int(details['target'].split(":")[1]),statusio.options):
            details['status'] = statusio.incident_status_code_from_status_code(200)
        else:
            details['status'] = statusio.incident_status_code_from_status_code(500)
    else:
        statusio.nagios_output(3, "Invalid Check_type")

    containers = statusio.get_containers(details['id'])
    incident_containers=[]
    message = "The situation is normal"
    raise_incident = False
    close_incident = False
    for name,container in containers.iteritems():
        if details['status'] < 300:
        #it's working
            if container['current_status'] != 200 and container['current_status'] != 100:
                #it is working
                #It is not in maintenance mode
                #It was not previously working
                incident_containers.append(container['id'])
                #TODO - Close incident
            else:
                #It is working and was working
                #It is working and was in maintenance
                continue
        else:
            #it's broken
            if container['current_status'] == 100:
                #Currently broken, Was working
                incident_containers.append(container['id'])
                message = "We have detected an issue and are currently investigating"
                #TODO - Raise Incident
            else:
                #Currently broken, in maintenance mode
                #Currently broken, was broken before
                #do nothing
                continue
    statusio.status_update(details['id'],incident_containers, message, details['status'])

statusio.nagios_output(0)
