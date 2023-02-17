import requests, yaml, datetime
from pprint import pprint
import discord
from discord.ext import commands

# Pull keys and various config info from config.yml file in same directory as dolores.py
# config_file = '/home/dolores/config/config.yml'
config_file = 'config\\config.yml'
with open(config_file) as c:
	config = yaml.safe_load(c)

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='-', case_insensitive=True, intents=intents)

notion_headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
           'Notion-Version': config['NOTION']['notion_version']
}

def retrieve_database():
    response = requests.get(config['NOTION']['base_url']
                            + 'databases/'
                            + config['NOTION']['database_id']
                            , headers=headers)

    pprint(response.json())

@bot.command(description='A catch-all command for rolling any number of any-sided dice.')
async def query(ctx):
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

    for elem in response.json()['results']:
        # Add try catches for each of these
        date = elem['properties']['Date']['date']['start']
        title = elem['properties']['Name']['title'][0]['plain_text']

        people = ', '.join([person['name'] for person in elem['properties']['Tags']['multi_select']])
        embed.add_field(name=str(date), value=title + '   (' + people + ')', inline=False)

    await ctx.send(embed=embed)

if __name__ == '__main__':
    # bot.run(config['DISCORD']['test_bot_api_key'])
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
                            , json = json_data)

    if response.status_code != 200:
        try: pprint(response.json())
        except: print(response.content)

    # Check for no streams
    if len(response.json()['results']) == 0:
        print('No streams')

    for elem in response.json()['results']:
        # Add try catches for each of these
        date = elem['properties']['Date']['date']['start']
        date_weekday = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        print(date_weekday)
        title = elem['properties']['Name']['title'][0]['plain_text']

        people = ', '.join([person['name'] for person in elem['properties']['Tags']['multi_select']])
