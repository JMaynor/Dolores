'''
dolores.py
Author: Jordan Maynor
Date: Apr 2020

Dolores is a chatbot that connects to a Discord server. Her primary use
is in being able to roll dice for players of a tabletop roleplaying game
but she is also capable of doing some basic audio things.
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
import sqlalchemy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

intents = discord.Intents.all()
intents.members = True
bot = bridge.Bot(command_prefix='-', case_insensitive=True, intents=intents)

# Add all Cog modules
bot.add_cog(rolling(bot))

if os.name == 'nt':
	CONFIG_FILE = 'config\\config.yml'
else:
	CONFIG_FILE = '/home/dolores/config/config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)

sarcastic_names = config['DISCORD']['sarcastic_names']

chatbot = ChatBot('Dolores')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

notion_headers = {'Authorization': 'Bearer ' + config['NOTION']['api_key'],
				'Notion-Version': config['NOTION']['notion_version']
}

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
	if isinstance(error, (commands.CommandNotFound)):
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
	# Catches any mistypes when trying to use a slash command
	if message.clean_content.startswith('/'):
		ctx = await bot.get_context(message)
		await ctx.respond(random.choice(snarky_comments))
	await bot.process_commands(message)


#---------------------------------------------------------------------------
# Program Main
#---------------------------------------------------------------------------
if __name__ == '__main__':
	print('Starting main program...')
	# bot.run(config['DISCORD']['test_bot_api_key'])
	bot.run(config['DISCORD']['bot_api_key'])
