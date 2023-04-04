'''
schedule_test.py
This script is used to test the Twitch API schedule endpoint as well as the Notion API
'''
# pylint: disable=line-too-long, bad-indentation, bare-except, multiple-statements
import datetime
import os
import threading
from pprint import pprint
import yaml
import requests

# Pull keys and various config info from config.yml file in same directory as dolores.py
# CONFIG_FILE = '/home/dolores/config/config.yml'
CONFIG_FILE = 'config\\config.yml'
with open(CONFIG_FILE, 'r', encoding='UTF-8') as c:
	config = yaml.safe_load(c)

# intents = discord.Intents.all()
# intents.members = True
# bot = commands.Bot(command_prefix='-', case_insensitive=True, intents=intents)

notion_headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
           'Notion-Version': config['NOTION']['notion_version']
}

# twitch_headers = {'Auhtorization': 'Bearer ' + config['TWITCH']['api_key']}
twitch_headers = {'Auhtorization': '',
                  'Client-ID': config['TWITCH']['client_id'],}

def retrieve_database():
    '''
    Retrieve the Notion database details
    '''
    response = requests.get(config['NOTION']['base_url']
                            + 'databases/'
                            + config['NOTION']['database_id']
                            , headers=notion_headers
                            , timeout=30)
    pprint(response.json())

def query():
    '''
    Query the Notion database for the next week's streams
    '''
    json_data = {"filter": {
                "property": "Date",
                "date": {
                    "next_week": {}
                }
            },
            "sorts": [
                {
                    "property": "Date",
                    "direction": "ascending"
                }
            ]
        }

    response = requests.post(config['NOTION']['base_url']
                            + 'databases/'
                            + config['NOTION']['database_id']
                            + '/query'
                            , headers=notion_headers
                            , json = json_data
                            , timeout=30)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    # Check for no streams
    if len(response.json()['results']) == 0:
        print('No streams')

    for elem in response.json()['results']:
        date = elem['properties']['Date']['date']['start']
        date_weekday = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        print(date_weekday)
        title = elem['properties']['Name']['title'][0]['plain_text']

        people = ', '.join([person['name'] for person in elem['properties']['Tags']['multi_select']])
        print('Title: ' + title)
        print('People: ' + people)

def sync_schedules_job():
    '''
    This function is called every week on Sunday to sync the Twitch schedule with the Notion schedule
    First, clear twitch schedule
    Then, query Notion for the next week's streams
    Then, add each stream to Twitch schedule
    '''
    # Clear Twitch schedule first
    clear_twitch_sched()
    query()
    set_twitch_sched()

def clear_twitch_sched():
    '''
    Function to clear the Twitch schedule
    '''
    # Get token first
    json_data = {"client_id": config['TWITCH']['client_id'],
                "client_secret": config['TWITCH']['client_secret'],
                "grant_type": "client_credentials"
                }
    

# Function to get a bearer token for Twitch API calls
def get_twitch_token():
    '''
    Get access token from Twitch API
    '''
    # Get token first
    json_data = {"client_id": config['TWITCH']['client_id'],
                "client_secret": config['TWITCH']['client_secret'],
                "grant_type": "client_credentials"
                }

    response = requests.post('https://id.twitch.tv/oauth2/token'
                            , headers=twitch_headers
                            , json = json_data
                            , timeout=30)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    print(response.json())

def get_twitch_sched():
    '''
    Function to get the schedule from Twitch API
    '''
    # Get token first
    json_data = {"client_id": config['TWITCH']['client_id'],
                "client_secret": config['TWITCH']['client_secret'],
                "grant_type": "client_credentials"
                }

    response = requests.post('https://id.twitch.tv/oauth2/token'
                            , headers=twitch_headers
                            , json = json_data
                            , timeout=30)

    # If response isn't 200, print the error
    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    # pprint(response.json())
    twitch_token = response.json()['access_token']

    # Get the schedule
    twitch_headers['Authorization'] = 'Bearer ' + twitch_token
    json_data = {"broadcaster_id": config['TWITCH']['broadcaster_id']}
    response = requests.get('https://api.twitch.tv/helix/schedule'
                            , headers=twitch_headers
                            , params = json_data
                            , timeout=30)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    pprint(response.json())

if __name__ == '__main__':
    # get_twitch_sched()
    retrieve_database()
