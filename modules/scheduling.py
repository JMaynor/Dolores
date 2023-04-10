'''
scheduling.py
'''
import os
import random
from datetime import datetime
import yaml
import requests
import discord
from discord.ext import commands, bridge

if os.name == 'nt':
	CONFIG_FILE = 'config\\config.yml'
else:
	CONFIG_FILE = '/home/dolores/config/config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)

notion_headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
				'Notion-Version': config['NOTION']['notion_version']
}

sarcastic_names = config['DISCORD']['sarcastic_names']

class scheduling(commands.Cog):
	'''
	Commands for getting and writing schedule info.
	'''
	def __init__(self, bot):
		self.bot = bot

	@bridge.bridge_command(description='Returns the next couple streams on the schedule.')
	async def schedule(self, ctx):
		'''
		Returns any streams scheduled for the next week.
		Ex: -schedule
		Dolores will return an embed of stream dates, names, and people.
		'''
		await ctx.defer()
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
			try:
				print(response.json())
			except:
				print(response.content)
			await ctx.respond('Notion\'s API is giving an error, so I couldn\'t get that for you, ' + random.choice(sarcastic_names))
			return

		embed = discord.Embed(title="Stream Schedule", description="Streams within the next week.")
		# Check for no streams
		if len(response.json()['results']) == 0:
			embed.add_field(name='Nada', value='We ain\'t got shit scheduled, ' + random.choice(sarcastic_names))
		else:
			for elem in response.json()['results']:
				try:
					date = elem['properties']['Date']['date']['start']
					date_weekday = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
				except:
					date = ''
					date_weekday = ''
				try:
					title = elem['properties']['Name']['title'][0]['plain_text']
				except:
					title = ''
				try:
					people = ', '.join([person['name'] for person in elem['properties']['Tags']['multi_select']])
				except:
					people = ''

				embed.add_field(name=date +  ' ' + date_weekday
								, value=title + '   (' + people + ')'
								, inline=False)
		await ctx.respond(embed=embed)

# def get_notion_schedule():
# 	'''
# 	Returns the next couple streams on the schedule.
# 	'''
# 	print()

# def clear_twitch_schedule():
# 	'''
# 	Clears the Twitch schedule of all recurring segments
# 	'''
# 	print()

# def add_twitch_segment():
# 	'''
# 	Adds a recurring segment to the Twitch schedule
# 	'''
# 	print()
