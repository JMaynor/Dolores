'''
dolores.py
Author: Jordan Maynor
Date: Apr 2020

Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of keeping track of player's inventories and "talking"
to the players through a few different commands.
'''

# pylint: disable=line-too-long
import random
import asyncio
import sqlite3
import pandas
import sys
import json
import yaml
import datetime
import youtube_dl
import discord
from discord.ext import commands
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
				   'foxy mama']

bot = commands.Bot(command_prefix='-', case_insensitive=True)

# Pull keys and various config info from config.yml file in same directory as dolores.py
config_file = '/home/dolores/config/config.yml'
with open(config_file) as c:
	config = yaml.load(c)
bot_api_key = config['DISCORD']['bot_api_key']
general_chat_id = config['DISCORD']['general_chat_id']
general_voice_id = config['DISCORD']['general_voice_id']
log_rolls = config['DATABASE']['log_rolls']
admins = config['DISCORD']['admin_users']
inv_admins = config['DISCORD']['inv_admin_users']

# In-container location, use volume for local file storage
db_loc = 'file:/home/dolores/config/roll_history.db?mode=rw'

youtube_dl.utils.bug_reports_message = lambda: ''
ffmpeg_options = {'options': '-vn'}
ytdl = youtube_dl.YoutubeDL(config['YTDL'])

chatbot = ChatBot('Dolores')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

#---------------------------------------------------------------------------
# Bot Events & Utility Functions
#---------------------------------------------------------------------------

@bot.event
async def on_ready():
	print('Time is: ', datetime.datetime.now())
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
			'Close.']
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
	if isinstance(ctx.channel, discord.channel.DMChannel):
		await ctx.send('{}:    {}'.format(str(ctx.author).split('#')[0], message))
	else:
		await ctx.send('{}:    {}'.format(str(ctx.author.nick).split('#')[0], message))


@bot.command(description='Sets nickname of everyone to whichever campaign is now active.')
async def setcamp(ctx, campaign: str):
	'''
	setcamp sets everyone's nicknames to the character
	they play in whichever campaign is specified. Command
	only usable by server owner.
	Ex: -setcamp ternov
	Dolores would set everyone's names to whatever character they play in the "ternov" campaign
	'''
	if str(ctx.author).split('#')[0] in admins:
		# Contains everyone's names for each campaign that has been run
		chars = pandas.DataFrame(data=config['CHARACTERS'], index=config['USERS'])
		for user in ctx.guild.members:
			try:
				newnick = chars.loc[user.name, campaign]
				print('New nickname for {} is {} in campaign {}'.format(user.name, newnick, campaign) )
				if newnick is not None:
					await user.edit(nick=newnick)
			except KeyError: print('No value found for user/camp combo: {} {}'.format(user, campaign))
			except discord.Forbidden: print('Couldn\'t change the nickname of user: {}'.format(user))
		await send_result(ctx, 'I have performed the ritual of renaming.')
	else: await send_result(ctx, 'You ain\'t got the authority to do that, sir or madam.')

@bot.command(description='Reloads config file so any changes to characters section can be used without restarting Dolores')
async def reload_config(ctx):
	if str(ctx.author).split('#')[0] in admins:
		with open(config_file) as c:
			global config
			config = yaml.load(c)
		await send_result(ctx, 'I have reloaded my configuration file.')


@bot.command(description='Command for transferring DM power to a user.')
async def dm(ctx, member: discord.Member):
	'''
	dm transfers DM powers to a given user.
	It first removes the DM user from any users that already have it.
	Should only ever be one user, but might as well loop through all.
	Ex: -dm Makamatin
	Dolores would remove DM role from all users, then would assign role to user Makamatin
	'''
	if str(ctx.author).split('#')[0] in admins:
		dm_role = discord.utils.get(ctx.guild.roles, name='DM')
		for user in ctx.guild.members:
			await bot.remove_roles(user, dm_role)
			if member in str(user.name):
				await bot.add_roles(user, dm_role, reason='Campaign switch.')
		await send_result(ctx, 'The Ritual has been performed.')
	else: await send_result(ctx, 'Only the Old King of this land may wield such power.')


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
			await ctx.send('Format has to be in NdN, {}.'.format(random.choice(sarcastic_names)))
			return
		rolls_result = [str(random.randint(1, limit)) for r in range(rolls)]
		if len(rolls_result) > 500:
			await ctx.send(random.choice(['I ain\'t rollin all that for you...', 'Absolutely not.', 'No.']))
			return
		if len(rolls_result) < 100 and log_rolls:
			for r in rolls_result: log_roll(ctx, limit, r)
		formatted_rolls = ', '.join(rolls_result)
		formatted_rolls = '(d' + str(limit) + ')  ' + formatted_rolls
		if len(rolls_result) >= 3:
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
	if log_rolls:
		log_roll(ctx, '20', roll_result)
	roll_result = '(d20)  ' + str(roll_result)
	await send_result(ctx, roll_result)


def log_roll(ctx, dtype, roll):
	'''
	Logs a die roll someone does into a sqlite database for later perusing.
	'''
	row = [str(ctx.author).split('#')[0], dtype, roll]
	try:
		c.execute("INSERT INTO rolls VALUES (?,?,?, DATETIME('now', 'localtime'))", row)
		conn.commit()
	except:
		print('ERROR INSERTING ROLL INTO rolls SQLITE TABLE.')


#---------------------------------------------------------------------------
# Inventory System
#---------------------------------------------------------------------------

@bot.command(description='Adds or removes an item to someone\'s inventory.')
# @commands.has_any_role('Admin', 'Inventory Admin')
async def inv(ctx, person: str, item: str, count=1):
	'''
	Add/remove item to specified person\'s inventory. Positive num for add, negative for subtract
	Ex: -inv Dieter "Cursed Book" 1
	Dolores will add 1 cursed book to Dieter's inventory
	'''
	print('Person ', person, ' Item ', item, ' Count ', count)

	if str(ctx.author).split('#')[0] in [*inv_admins, *admins]:
		amount_person_has = get_item_amount(person, item)
		if amount_person_has + count <= 0:
			c.execute("DELETE FROM inventory WHERE person = ? and item = ?", [person, item])
			conn.commit()
			await send_result(ctx, 'Character has no more of that item now.')
		elif count < 0:
			if amount_person_has is None:
				await send_result(ctx, 'Person does not have that item in inventory.')
			else:
				try:
					c.execute("UPDATE inventory SET count=count-? WHERE person = ? and item = ?", [abs(count), person, item])
					conn.commit()
					await send_result(ctx, 'Edited that item count.')
				except:
					await send_result(ctx, 'ERROR SUBSTRACTING THAT ITEM')
		else:
			try:
				c.execute("INSERT INTO inventory(person,count,item) VALUES (?,?,?) ON CONFLICT(person,item) DO UPDATE SET count=count+? WHERE person = ? AND item = ?",
						[person, count, item, count, person, item])
				conn.commit()
				await send_result(ctx, 'Edited that item count.')
			except:
				await send_result(ctx, 'ERROR ADDING ITEM')


@bot.command(description='Show a character\'s inventory.')
async def invshow(ctx, person=None):
	'''
	Shows a person\'s inventory. Person can be specified, if not it will show inventory of person who called function.
	Ex: -invshow Legion
	Legion's inventory will be displayed.
	'''
	if person is None: person = get_character(str(ctx.author).split('#')[0])
	try:
		print('Returning inventory for: ', person)
		c.execute("SELECT count, item from inventory WHERE person = ? ORDER BY item", [person])
		text_result = '```\n'
		for row in c.fetchall():
			text_result = text_result + str(row[0]) + '	' + str(row[1]) + '\n'
		text_result = text_result + '```'
		await send_result(ctx, text_result)
	except: await send_result(ctx, 'ERROR SELECTING FROM THE inventory TABLE.')


def get_item_amount(person, item):
	'''
	Utility function for fetching current amount of item a person has
	Will return None if character does not have an item at all.
	'''
	c.execute("SELECT count FROM inventory WHERE person = ? AND item = ?", [person, item])
	result = c.fetchone()
	return 0 if result is None else result[0]


@bot.command(description='Set the active campaign for the inventory commands.')
async def set_character(ctx, user, character):
	'''
	set_campaign sets the currently active campaign to the given ID
	This is for use with the inventory system, it allows each user to
	have a character in each campaign
	SYSTEM NOT CURRENTLY BEING USED
	'''
	if str(ctx.author).split('#')[0] in [*inv_admins, *admins]:
		try:
			c.execute("UPDATE user_character SET character=? WHERE user=?", [character, user])
			await send_result(ctx, 'Set user\'s active character.')
		except: await send_result(ctx, 'ERROR SETTING ACTIVE CAMPAIGN')


def get_character(user):
	'''
	Utility function for returning the ID of the currently active campaign
	'''
	return c.execute("SELECT character from user_character WHERE user=?", [user]).fetchone()[0]


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
	if str(ctx.author).split('#')[0] in admins:
		channel = bot.get_channel(general_chat_id)
		async with channel.typing():
			await asyncio.sleep(1)
		await channel.send(message)
	else: await ctx.send(random.choice(list_of_phrases), tts=True)


@bot.command(description='Use\'s youtube-dl to play an audio stream in the General voice channel.')
async def play(ctx, *, url):
	'''
	Plays a song from a given URL in the General voice channel.
	Valid URLS are Youtube and Soundcloud
	Ex: -play https://www.youtube.com/watch?v=O1OTWCd40bc
	Dolores will play Wicked Games by The Weeknd
	Note: Due to drama with youtube-dl, may or may mot be working at this point
	'''
	if ctx.voice_client is None: await bot.get_channel(general_voice_id).connect()
	if ctx.voice_client.is_playing(): ctx.voice_client.stop()

	async with ctx.typing():
		player = await YTDLSource.from_url(url, loop=bot.loop, stream=False)
		ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
	await ctx.send('Now playing: {}'.format(player.title))


@bot.command(description='Stops the currently playing audio in the General voice channel.')
async def stop(ctx):
	'''
	Stops the currently playing song, if one is playing.
	Ex: -stop
	Dolores stops whatever current song is.
	'''
	if ctx.voice_client.is_playing(): ctx.voice_client.stop()


#---------------------------------------------------------------------------
# Program Main
#---------------------------------------------------------------------------
if __name__ == '__main__':
	print('Starting main program...')
	try:
		conn = sqlite3.connect(db_loc, uri=True)
		c = conn.cursor()
	except sqlite3.OperationalError:
		print('DATABASE NOT FOUND')
		exit()

	bot.run(bot_api_key)
