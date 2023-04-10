'''
text.py module
'''
import sys
sys.path.append('..')
import random
import os
import yaml
import sqlalchemy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import discord
from discord.ext import commands, bridge
import openai

if os.name == 'nt':
	CONFIG_FILE = 'config\\config.yml'
else:
	CONFIG_FILE = '/home/dolores/config/config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)

if config['DISCORD']['reply_method'] == 'openai':
	openai.api_key = config['AI']['openai_key']

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
	'No.',
	'Big Dumb.']

chatbot = ChatBot('Dolores')
trainer = ChatterBotCorpusTrainer(chatbot)
trainer.train("chatterbot.corpus.english")

class text(commands.Cog):
	'''
	Commands for generating dialogue.
	'''
	def __init__(self, bot):
		self.bot = bot

	def generate_reply(self, message):
		'''
		Generates a reply to a given message. Currently using chatterbot. Intent is to use a proper LLM in the future.
		'''
		if config['DISCORD']['reply_method'] == 'chatterbot':
			reply = chatbot.get_response(message)
		elif config['DISCORD']['reply_method'] == 'openai':
			# chat_completion = openai.Completion.create(
			# 	model = config['OPENAI']['model']
			# 	, messages=[{"role": "user", "content": message}]
			# 	, max_tokens=config['OPENAI']['max_tokens']
			# 	, temperature=config['OPENAI']['temperature']
			# 	, top_p=config['OPENAI']['top_p']
			# 	, frequency_penalty=config['OPENAI']['frequency_penalty']
			# 	, presence_penalty=config['OPENAI']['presence_penalty']
			# )
			# reply = chat_completion.choices[0].message.content
			reply = ''
		elif config['AI']['reply_method'] == 'self':
			# Use a self-hosted LLM to generate reply
			reply = ''
		else:
			reply = ''
		return reply

	def generate_snarky_comment(self):
		'''
		Generates a snarky comment to be used when a user tries to use a command that does not exist.
		'''
		random.choice(snarky_comments)
