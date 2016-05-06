#!/usr/bin/env python2

# https://github.com/SickRage/sickrage-issues/wiki/Post-Processing#extra-scripts



# argv[0]: File-path to Script
# argv[1]: Final full path to the episode file
# argv[2]: Original full path of the episode file
# argv[3]: Show indexer ID
# argv[4]: Season number
# argv[5]: Episode number
# argv[6]: Episode Air Date


import sys
import httplib
import urllib
import base64
import string
import json
import os.path
import yaml


SCRIPT_FILE_PATH = sys.argv[0]
EP_FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else None
ORIG_EP_FILE_PATH = sys.argv[2] if len(sys.argv) > 2 else None
SHOW_ID = sys.argv[3] if len(sys.argv) > 3 else None
SEASON = sys.argv[4] if len(sys.argv) > 4 else None
EPISODE = sys.argv[5] if len(sys.argv) > 5 else None
AIR_DATE = sys.argv[6] if len(sys.argv) > 6 else None



def basic_auth(username, password):
    # base64 encode the username and password
    return base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

def show_name(json_string):
    data = json.loads(json_string)
    if data['result'] == 'error':
      print data['message']
      return "N/A"

    return data["data"]["show_name"]


def new_connection(hostname, https):
    if https == True:
        return httplib.HTTPSConnection(hostname)
    return httplib.HTTPConnection(hostname)


def request_response(conn, type, path, params, headers):
    params = urllib.urlencode(params, True)
    conn.request(type, path, params, headers)
    response = conn.getresponse()
    return response


def run():
    if SHOW_ID == None or SEASON == None or EPISODE == None or AIR_DATE == None:
        print("Missing needed arguments")
        return

    yaml_path = os.path.join(os.path.dirname(__file__), "notify-message-cache.yaml")

    if os.path.isfile(yaml_path) == False:
      print("YAML config file is missing. Should be: %s" % yaml_path)
      return

    config = yaml.safe_load(open(yaml_path))

    # Get Show name
    conn = new_connection(config['sickrage']['host'], False)
    response = request_response(conn, "GET", "/api/" + config['sickrage']['api_key'] + "/?cmd=show&indexerid=" + SHOW_ID, {}, {})
    show = show_name(response.read()) if (response.status == 200) else "N/A"
    conn.close()

    params = {"message": "New episode downloaded.",
              "meta[season]": SEASON,
              "meta[episode]": EPISODE,
              "meta[air_date]": AIR_DATE,
              "meta[show_id]": SHOW_ID,
              "meta[show]": show,
              "meta[notifier]": "sickrage",
              "meta[channel]": "tv"}

    auth = basic_auth(config['message_cache']['basic_auth']['username'], config['message_cache']['basic_auth']['password'])
    headers = {"content-type": "application/x-www-form-urlencoded",
               "authorization": "Basic %s" % auth}

    conn = new_connection(config['message_cache']['host'], False)
    response = request_response(conn, "POST", config['message_cache']['path'], params, headers)
    conn.close()


# Run that shit!
run()
