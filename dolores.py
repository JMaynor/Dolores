'''
dolores.py
Author: Jordan Maynor
Date: Apr 2020

Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.

Majority of functionality has been organized into separate modules.
dolores.py - Main program file. Handles Discord-related functionality and events
audio.py - Handles all audio/yt-dlp related functionality
rolling.py - Handles all dice-rolling/randomization functionality
scheduling.py - Handles all Notion/Twitch scheduling functionality
text.py - Handles all text-related functionality
'''

# pylint: disable=line-too-long, bad-indentation, bare-except
import random
import asyncio
import sys
import os
from datetime import datetime
import yaml
import discord
from discord.ext import commands, bridge

from modules import *

intents = discord.Intents.all()
intents.members = True
bot = bridge.Bot(command_prefix='-', case_insensitive=True, intents=intents)

# Add all Cog modules
bot.add_cog(rolling(bot))
bot.add_cog(audio(bot))
bot.add_cog(scheduling(bot))
bot.add_cog(text(bot))

if os.name == 'nt':
	CONFIG_FILE = 'config\\config.yml'
else:
	CONFIG_FILE = '/home/dolores/config/config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)

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
	on_command_error overrides default py-cord command error behavior. If someone
	tries to use a command that does not exist, Dolores will reply with a snarky
	comeback. Any other error performs default behavior of logging to syserr.
	'''
	await ctx.defer()
	text_instance = text(bot)
	if isinstance(error, (commands.CommandNotFound)):
		await ctx.send(text_instance.generate_snarky_comment())
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
		text_instance = text(bot)
		clean_message = message.clean_content.replace('@Dolores', '')
		reply = text_instance.generate_reply(clean_message)
		ctx = await bot.get_context(message)
		await ctx.respond(reply)

	# Catches any mistypes when trying to use a slash command
	if message.clean_content.startswith('/'):
		text_instance = text(bot)
		ctx = await bot.get_context(message)
		snark_reply = text_instance.generate_snarky_comment()
		await ctx.respond(snark_reply)
	await bot.process_commands(message)


#---------------------------------------------------------------------------
# Program Main
#---------------------------------------------------------------------------
if __name__ == '__main__':
	print('Starting main program...')
	# bot.run(config['DISCORD']['test_bot_api_key'])
	bot.run(config['DISCORD']['bot_api_key'])
