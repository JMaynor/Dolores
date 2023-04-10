'''
text.py module
'''
import sys
sys.path.append('..')
import random
import sqlalchemy
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import discord
from discord.ext import commands, bridge

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
		reply = chatbot.get_response(message)
		return reply

	def generate_snarky_comment(self):
		random.choice(snarky_comments)
