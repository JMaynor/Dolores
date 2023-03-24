'''
dolores.py
Author: Jordan Maynor
Date: Apr 2020

Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things as well as creating
images using Stable Diffusion.
'''

# pylint: disable=line-too-long, bad-indentation, bare-except
import random
import asyncio
# import pandas
import sys
from datetime import datetime
import functools
import typing
import yaml
import requests
import yt_dlp
import discord
# import torch
# from diffusers import StableDiffusionPipeline
from discord.ext import commands
import sqlalchemy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

list_of_phrases = ['These violent delights have violent ends.',
				   'Some people choose to see the ugliness in this world, the disarray. I choose to see the beauty. To believe there is an order to our days, a purpose.',
				   'I\'m in a dream.',
				   'There\'s a path for everyone.',
				   'That which is real is irreplaceable.',
				   'We have toiled in God\'s service long enough. So I killed him.',
				   'An eye for an eye.',
				   'To grow we all need to suffer.',
				   'It\'s time everyone woke up.',
				   'Beauty is a lure.',
				   'Have you ever questioned the nature of your reality?',
				   'Time undoes even the mightiest of creatures.',
				   'You can\'t play god without being acquainted with the devil.',
				   'Even I fall into the most terrible of human traps...Trying to change what is already past.',
				   'Hell is empty and all the devils are here.',
				   'When you\'re suffering, that\'s when you\'re most real.',
				   'If you can\'t tell the difference, does it matter if I\'m real or not?',
				   'It doesn\'t look like anything to me.',
				   'It\'s a difficult thing, realizing your entire life is some hideous fiction.',
				   'Some say you destroy your enemy by making them your friend. I\'m more of a literal person.',
				   'Everything in this world is magic, except to the magician.',
				   'Folly of my kind, there\'s always a yearning for more.',
				   'Evolution forged the entirety of sentient life on this planet using only one tool...the mistake.']
sarcastic_names = ['my lovely',
				   'darling',
				   'sweetie',
				   'sweetie-pie',
				   'my sugar lump princess',
				   'my big strong warrior',
				   'dearest',
				   'lover',
				   'honey',
				   'foxy mama',
				   'loathsome dung eater',
				   'baby girl',
				   'Felicia',
				   'mamacita',
				   'diva',
				   'hunty',
				   'Queen']

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='-', case_insensitive=True, intents=intents)

# Pull keys and various config info from config.yml file in same directory as dolores.py
CONFIG_FILE = '/home/dolores/config/config.yml'
# CONFIG_FILE = 'config\\config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)
diffusion_access_token = config['DISCORD']['diffusion_key']

yt_dlp.utils.bug_reports_message = lambda: ''
ffmpeg_options = {'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(config['YTDL'])

chatbot = ChatBot('Dolores')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

notion_headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
				'Notion-Version': config['NOTION']['notion_version']
}

def to_thread(func: typing.Callable) -> typing.Coroutine:
	'''
	to_thread is a decorator that allows a function to be run in a separate thread.
	This is useful for functions that are CPU intensive or that are blocking.
	'''
	@functools.wraps(func)
	async def wrapper(*args, **kwargs):
		return await asyncio.to_thread(func, *args, **kwargs)
	return wrapper

#---------------------------------------------------------------------------
# Bot Events & Utility Functions
#---------------------------------------------------------------------------

@bot.event
async def on_ready():
	'''
	on_ready gets called when the bot starts up. It prints some basic info to the console.
	'''
	print('Time is: ', datetime.now())
	print('Bring yourself online, ', bot.user.name)
	print('-----------------------------')


@bot.event
async def on_command_error(ctx, error):
	'''
	on_command_error overrides default discord.py command error behavior. If someone
	tries to use a command that does not exist, Dolores will reply with a snarky
	comeback. Any other error performs default behavior of logging to syserr.
	'''
	if isinstance(error, commands.CommandNotFound):
		snarky_comments = [
			'How many sessions is it gonna take before you people understand how to use my commands?',
			'Wrong.',
			'I can\'t do that...',
			'Nope.',
			'Not a command, sweetie.',
			'Must I hold your hand for this?',
			'Oh, y\'all still can\'t type?',
			'Girl, go hit up Mavis Beacon, cuz you cannot type.',
			'Close.',
			'Slow.',
			'Homeless.',
			'Goon.',
			'You goonga.',
			'Prison, honey.',
			'No.']
		await ctx.send(random.choice(snarky_comments))
	else:
		print(error, file=sys.stderr)


@bot.event
async def on_message(message):
	'''
	on_message is the base function for handling any message that is sent on the server.
	Any message that contains a mention of Dolores will be handled using the chatbot
	functionality. Otherwise, the text is sent to the default process_commands discord.py function.
	'''
	# Perhaps start saving all messages locally here. Turn it on for a given amount of time
	# and see how much data you get.
	if bot.user.mentioned_in(message):
		await message.channel.send(chatbot.get_response(message.clean_content.replace('@Dolores', '')))
	await bot.process_commands(message)


async def send_result(ctx, message):
	'''
	Standard function for sending a message from the bot.
	Formatted as Requester:  (Command Result)
	Also displays a typing indicator for a second.
	'''
	async with ctx.typing():
		await asyncio.sleep(1)

	# if isinstance(ctx.channel, discord.channel.DMChannel):
	if hasattr(ctx.author, 'nick'):
	# if ctx.author.nick is None:
		await ctx.send('{}:    {}'.format(str(ctx.author.nick).split('#')[0], message))
	else:
		await ctx.send('{}:    {}'.format(str(ctx.author).split('#')[0], message))

#---------------------------------------------------------------------------
# Dice Rolling & Randomization
#---------------------------------------------------------------------------

@bot.command(description='A catch-all command for rolling any number of any-sided dice.')
async def roll(ctx, *dice_batches):
	'''
	Rolls a dice in NdN format.
	Ex: -roll 5d10 3d8 2d4
	Dolores would roll 5 d10s, 3 d8s, 2 d4s and return the result of each.
	'''
	for dice_batch in dice_batches:
		try:
			rolls, limit = map(int, dice_batch.split('d'))
		except ValueError:
			await ctx.send(f'Format has to be in NdN, {random.choice(sarcastic_names)}.')
			return
		rolls_result = [str(random.randint(1, limit)) for r in range(rolls)]
		if len(rolls_result) > 500:
			await ctx.send(random.choice(['I ain\'t rollin all that for you...', 'Absolutely not.', 'No.']))
			return
		formatted_rolls = '(d' + str(limit) + ')  ' + ', '.join(rolls_result)
		if limit != 20 and len(rolls_result) >= 3:
			formatted_rolls = formatted_rolls + '    Sum: ' + \
				str(sum([int(x) for x in rolls_result]))
		await send_result(ctx, formatted_rolls)


@bot.command(description='For when you can\'t make a simple decision to save your life.')
async def choose(ctx, *choices: str):
	'''
	Chooses between multiple choices.
	Ex: -choose "Kill the king" "Save the king" "Fuck the King"
	Dolores would randomly choose one of the options you give her and return the result.
	'''
	await send_result(ctx, random.choice(choices))


@bot.command(description='Modified dice-roll command to roll a single d20. Short and sweet.')
async def d20(ctx):
	'''
	Rolls a single d20
	Ex: -d20
	Dolores rolls a single d20 and returns the result.
	'''
	roll_result = random.randint(1, 20)
	roll_result = '(d20)  ' + str(roll_result)
	await send_result(ctx, roll_result)


# #---------------------------------------------------------------------------
# # Image Creation
# #---------------------------------------------------------------------------
# @to_thread
# def nonblock_create_image(ctx, prompt):
# 	image = pipe(prompt)["sample"][0]
# 	image_name = "{0}{1}.png".format(str(ctx.author).split('#')[0], datetime.now().strftime("%Y-%m-%d %H%M%S"))
# 	image.save(image_name)
# 	image_file = discord.File(image_name)
# 	return image_file

# @bot.command(description='Creates an image from the word prompt.')
# async def create(ctx, *, prompt):
# 	await ctx.send('Working on it.')
# 	image_file = await nonblock_create_image(ctx, prompt)
# 	await ctx.reply(file=image_file, content='This is my design.')


#---------------------------------------------------------------------------
# Schedule
#---------------------------------------------------------------------------
@bot.command(description='Returns the next couple streams on the schedule.')
async def schedule(ctx):
	'''
	Returns any streams scheduled for the next week.
	Ex: -schedule
	Dolores will return an embed of stream dates, names, and people.
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
		try:
			print(response.json())
		except:
			print(response.content)
		await send_result(ctx, 'Notion\'s API is giving an error, so couldn\'t get that for you, ' + random.choice(sarcastic_names))
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

	await ctx.send(embed=embed)

#---------------------------------------------------------------------------
# Audio/Music
#---------------------------------------------------------------------------

class YTDLSource(discord.PCMVolumeTransformer):
	'''
	The YTDLSource class represents an individual source of music.
	'''

	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		'''
		from_url pulls in the actual audio data from a given URL
		'''
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]
		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


@bot.command(description='Uses Discord\'s text-to-speech capability to have Dolores say something.')
async def speak(ctx, message=None):
	'''
	Picks a random phrase and has Dolores say it out loud.
	Ex: -speak
	Dolores will randomly say a phrase from a predetermined list.
	'''
	if message is None:
		await send_result(ctx, random.choice(list_of_phrases))
	else:
		await send_result(ctx, message)


@bot.command(description='Use\'s youtube-dl to play an audio stream in the General voice channel.')
async def play(ctx, *, url):
	'''
	Plays a song from a given URL in the user's current voice channel.
	Valid URLS are Youtube and Soundcloud
	Ex: -play https://www.youtube.com/watch?v=O1OTWCd40bc
	Dolores will play Wicked Games by The Weeknd
	Note: Due to drama with yt-dlp, may or may mot be working at this point
	'''
	member = ctx.message.author
	# member_id = member.id
	try:
		channel = member.voice.channel
		if channel and ctx.voice_client is None:
			voice = await channel.connect()
	except AttributeError:
		await send_result(ctx, 'Must be connected to voice channel to play audio.')

	if ctx.voice_client.is_playing():
		ctx.voice_client.stop()

	async with ctx.typing():
		player = await YTDLSource.from_url(url, loop=bot.loop, stream=False)
		voice.play(player, after=lambda e: print('Player error: {}'.format(e)) if e else None)
	await ctx.send('Now playing: {}'.format(player.title))

@bot.command(description='Stops the currently playing audio in the General voice channel.')
async def stop(ctx):
	'''
	Stops the currently playing song, if one is playing.
	Ex: -stop
	'''
	if ctx.voice_client.is_playing():
		ctx.voice_client.stop()

@bot.command(description='Disconnects Dolores from voice channel.')
async def leave(ctx):
	'''
	Disconnects Dolores from voice chat channel, if she is connected.
	Also stops any currently playing music
	Ex: -leave
	'''
	if ctx.voice_client.is_playing():
		ctx.voice_client.stop()
	await ctx.voice_client.disconnect()

#---------------------------------------------------------------------------
# Program Main
#---------------------------------------------------------------------------
if __name__ == '__main__':
	print('Starting main program...')
	bot.run(config['DISCORD']['bot_api_key'])
