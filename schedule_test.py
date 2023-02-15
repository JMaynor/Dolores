import requests, yaml
from pprint import pprint

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
    # json_data = {"filter": {
	# 	            "property": "Date",
	# 	            "date": {
	# 		            "next_week": {}
	# 	            }
    #             },
	#             "sorts": [
	# 	            {
	# 		            "property": "Date",
	# 		            "direction": "ascending"
	# 	            }
	#             ]
    #         }
    json_data = {
    "filter": {
        "and": [
            {
                "property": "Date",
                "date": {
					"on_or_after": "2024-02-01"
				}
            },
            {
                "property": "Date",
                "date": {
					"on_or_before": "2024-02-28"
				}
            }
        ]
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
                            , headers=headers
                            , json = json_data)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    # Check for no streams
    if len(response.json()['results']) == 0:
         print('No streams')

    # for elem in response.json()['results']:
    #     print(elem)
    #     print()
    #     print()

if __name__ == '__main__':
    query_database()
