#!/usr/bin/env python

import httplib2
import time
import shelve
import traceback
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
from oauth2client.client import AccessTokenRefreshError

"""
Google Analytics Nagios Plugin

Description:
Uses a Google Analytics service account to grab GA metrics via the GA API. The following metrics are returned by default:
    * Unique Visitors
    * Page Load Time
    * Event Counts

Setup:
This plugin requires the Python Google Analytics client to be installed:

    https://developers.google.com/api-client-library/python/start/installation

If you see the following error when running the plugin: 'ImportError: cannot import name SignedJwtAssertionCredentials'
you will need to also run 'easy_install pyopenssl'

Once the Python library is installed, you need to setup a new service account:

    1. Login to Google's Developer Console: https://cloud.google.com/console/project
    2. Create a new project that has 'Analytics API' enabled
    3. Under 'Credentials', click 'CREATE NEW CLIENT ID' button and create a new Service Account
    4. Download the private key file and upload it to the server you will be running the plugin and put the full path
       under OAUTH2_PRIVATE_KEY_FILE below
    5. Take the email address (e.g. 123456789-....@developer.gserviceaccount.com) and edit SERVICE_ACCOUNT_EMAIL below
    6. Add the email address to your Google Analytics users under Admin->Account->User Management with 'Read & Analyse'
       permissions. It may take a few minutes until the user is enabled

Once setup, your service account will be able to access the GA APIs securely using the private key file.

Output:

OK | ga:visitors=xxx;;;; ga:avgPageLoadTime=xxxs;;;; ga:signups=xxx;;;; ga:contact_us=xxx;;;;;

Editing:
To add additional metrics from Google Analytics refer to this page on list of available metrics:

    https://developers.google.com/analytics/devguides/reporting/core/dimsmets

"""

# Set Variables to access Google Analytics

# Full Path to OAuth2.0 private key file on server running plugin
OAUTH2_PRIVATE_KEY_FILE = 'google-privatekey.p12'
# Service Account Email address given in Google Developer Console
SERVICE_ACCOUNT_EMAIL = 'xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx@developer.gserviceaccount.com'
# Profile ID - this is the profile ID of the we property beginning with UA-
PROFILE_ID = 'UA-XXXXXXXXX-X'


# Main method
def main():

    # Open tmpDB file via shelve. This will be used to store values between plugin runs
    tmpdb = _open_tmpdb()

    try:

        # Initialise API client
        service = _get_ga_service()
        # Get internal system profile ID from UA-... ID
        profileId = _get_profile_id(service, PROFILE_ID)

        # Exit if no valid profileId found
        if profileId is None:
            print 'No valid profile was found. Exiting.'
            exit(2)

        # Get today's date, must be in YYYY-MM-DD Format
        todaysDate = time.strftime("%Y-%m-%d")

        uniqueVisitors = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:visitors')
        avgPageLoadTime = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:avgPageLoadTime')
        totalSignups = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:totalEvents', 'ga:eventCategory==SignupForm')
        totalContacts = get_total_metric(service, profileId, todaysDate, todaysDate, 'ga:totalEvents', 'ga:eventCategory==ContactForm')

        # Check if any signups or contacts have appeared since last plugin run. If so send an alert
        alert = False
        alertmsg = ""
        if _get_tmpdb_difference('totalSignups', totalSignups, tmpdb) > 0:
            alert = True
            alertmsg = " New Signup"
        if _get_tmpdb_difference('totalContacts', totalContacts, tmpdb) > 0:
            alert = True
            alertmsg += " New Contact"

        # Write latest values to tmpdb
        tmpdb['uniqueVisitors'] = uniqueVisitors
        tmpdb['avgPageLoadTime'] = avgPageLoadTime
        tmpdb['totalSignups'] = totalSignups
        tmpdb['totalContacts'] = totalContacts
        tmpdb.sync()

        # Print Nagios Format Output
        if alert:
            print alertmsg + ' | ' + 'ga:visitors=' + uniqueVisitors + ';;;;' \
                  + ' ga:avgPageLoadTime=' + avgPageLoadTime + 's;;;;' \
                  + ' ga:signups=' + totalSignups + ';;;;' \
                  + ' gs:contact_us=' + totalContacts + ';;;;'
            exit(2)
        else:
            print 'OK | ' + 'ga:visitors=' + uniqueVisitors + ';;;;' \
                  + ' ga:avgPageLoadTime=' + avgPageLoadTime + 's;;;;' \
                  + ' ga:signups=' + totalSignups + ';;;;' \
                  + ' ga:contact_us=' + totalContacts + ';;;;'
            exit(0)

    except TypeError, error:
        # Handle errors in constructing a query.
        print 'There was an error in constructing your query : %s' % error
        traceback.print_exc()
        exit(2)

    except HttpError, error:
        # Handle API errors.
        print 'Arg, there was an API error : %s : %s' % (error.resp.status, error._get_reason())
        traceback.print_exc()
        exit(2)

    except AccessTokenRefreshError:
        # Handle Auth errors.
        print 'The credentials have been revoked or expired, ' \
              'please check your private key file and SERVICE_ACCOUNT_EMAIL are valid'
        traceback.print_exc()
        exit(2)

    except IOError, error:
        # Handle file system errors
        print 'There was an error opening a file: %s' % error
        traceback.print_exc()
        exit(2)

    finally:
        # Close tmpdb file and save changes back
        tmpdb.close()

# Helper method to get a total metric value for a given metric from API with optional filters
def get_total_metric(service, profileId, start_date, end_date, metric, filters=None):

    if filters is not None:
        return service.data().ga().get(
            ids='ga:' + profileId,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            metrics=metric).execute().get('totalsForAllResults').get(metric)
    else:
        return service.data().ga().get(
            ids='ga:' + profileId,
            start_date=start_date,
            end_date=end_date,
            metrics=metric).execute().get('totalsForAllResults').get(metric)

# Initialises and gets a new authorised service object to access the GA APIs
def _get_ga_service():

    # Get the private key from the Google supplied private key file.
    f = file(OAUTH2_PRIVATE_KEY_FILE, "r")
    key = f.read()
    f.close()

    # Create the JWT
    credentials = SignedJwtAssertionCredentials(
        SERVICE_ACCOUNT_EMAIL, key,
        scope="https://www.googleapis.com/auth/analytics.readonly"
    )

    # Create an authorized http instance
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Create a service call to the calendar API
    service = build("analytics", "v3", http=http)

    return service


# Utility method to get the system profile ID for a property given the UA-.... ID
# Will return None if not found
def _get_profile_id(service, profileId):

    # Get list of accounts and iterate till we find UA-... profile ID
    webProperties = service.management().webproperties().list(accountId='~all').execute()

    if webProperties.get('items'):

        # Iterate through all web properties until match with 'id' field, return system 'defaultProfileId'
        for profile in webProperties.get('items'):
            id = profile.get('id')
            if id == profileId:
                return profile.get('defaultProfileId')

        # Didn't find the profile ID
        print 'Profile ID ' + "'" + profileId + "'" + ' was not found for your Account.'
        return None

    else:
        # The account has no web properties
        print 'No Web Properties found for Service User Account. Check Service Account has permissions to access web properties.'
        return None


# Creates/opens a tmpdb, will clear all data if date has changed since last run so file is only
# storing current days values
def _open_tmpdb():

    # Open/Create tmpdb file
    tmpdb = shelve.open(__file__ + ".tmpDB")
    todaysDate = time.strftime("%Y-%m-%d")

    if tmpdb.get('date') is not None:
        dbDate = tmpdb.get('date')
        if dbDate != todaysDate:
            tmpdb.clear()
            tmpdb.sync()
    else:
        tmpdb['date'] = todaysDate
        tmpdb.sync()

    return tmpdb


# Helper function to return the difference between a value in tmpdb and another value for a key
def _get_tmpdb_difference(key, currentValue, tmpdb):

    prevvalue = 0
    if tmpdb.has_key(key):
        prevvalue = tmpdb[key]
    else:
        # Assume plugin is being run first time so shouldn't alert
        prevvalue = currentValue

    return int(currentValue) - int(prevvalue)

# Run Main
main()