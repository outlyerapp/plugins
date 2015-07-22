#!/usr/bin/env python
import tweepy
import sys

# create a new app at https://apps.twitter.com/ then make some access tokens

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_KEY = ''
ACCESS_SECRET = ''

# enter the account to get metrics for 

USER = ''

try:
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)
except:
    print "connection failed"
    sys.exit(2)

user = api.get_user(USER)
mentions  = api.mentions_timeline()

data = {}
data['followers'] = user.followers_count
data['listed'] = user.listed_count
data['friends'] = user.friends_count
data['statuses'] = user.statuses_count
data['favourites'] = user.favourites_count
data['mentions'] = len(mentions)

output = "OK | "

for k, v in data.iteritems():
    output += str(k) + '=' + str(v) + ';;;; '

print output
sys.exit(0)
