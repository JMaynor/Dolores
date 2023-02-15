import requests, yaml
from pprint import pprint
import discord

# Pull keys and various config info from config.yml file in same directory as dolores.py
# config_file = '/home/dolores/config/config.yml'
config_file = 'config\\config.yml'
with open(config_file) as c:
	config = yaml.safe_load(c)

headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
           'Notion-Version': config['NOTION']['notion_version']
        }

def retrieve_database():
    response = requests.get(config['NOTION']['base_url']
                            + 'databases/'
                            + config['NOTION']['database_id']
                            , headers=headers)

    pprint(response.json())

def query_database():
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
#     json_data = {
#     "filter": {
#         "and": [
#             {
#                 "property": "Date",
#                 "date": {
# 					"on_or_after": "2024-02-01"
# 				}
#             },
#             {
#                 "property": "Date",
#                 "date": {
# 					"on_or_before": "2024-02-28"
# 				}
#             }
#         ]
#     },
# 	"sorts": [
# 		{
# 			"property": "Date",
# 			"direction": "ascending"
# 		}
# 	]
# }

    response = requests.post(config['NOTION']['base_url']
                            + 'databases/'
                            + config['NOTION']['database_id']
                            + '/query'
                            , headers=headers
                            , json = json_data)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)
        return

    # Check for no streams
    if len(response.json()['results']) == 0:
        return 'No streams'

    embed = discord.Embed(title="Stream Schedule", description="Streams within the next week")

    embed.add_field()

    for elem in response.json()['results']:
        # Add try catches for each of these
        date = elem['properties']['Date']['date']['start']
        title = elem['properties']['Name']['title'][0]['plain_text']
        people = [person['name'] for person in elem['properties']['Tags']['multi_select']]

        print('Date: ' + str(date))
        print('Title: ' + title)
        print('People: ' + str(people))
        print()

if __name__ == '__main__':
    query_database()

    # send message https://stackoverflow.com/questions/44862112/how-can-i-send-an-embed-via-my-discord-bot-w-python
