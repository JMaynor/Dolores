'''
text.py module
'''
import sys
sys.path.append('..')
import random
import requests
import os
import yaml
import discord
from discord.ext import commands, bridge
import openai

if os.name == 'nt':
	CONFIG_FILE = 'config\\config.yml'
else:
	CONFIG_FILE = '/home/dolores/config/config.yml'
with open(CONFIG_FILE, 'r', encoding='utf-8') as c:
	config = yaml.safe_load(c)

reply_method = config['DISCORD']['reply_method']

if reply_method == 'openai':
	openai.api_key = config['OPENAI']['api_key']

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
		if reply_method == 'openai':
			response = openai.ChatCompletion.create(
				model = config['OPENAI']['model']
				, messages=[
					{"role": "system", "content": "You are a snarky and sarcastic, but helpful AI named Dolores. You were created by someone named Jordan."},
					{"role": "user", "content": message}]
				, max_tokens=config['OPENAI']['max_tokens']
				, temperature=config['OPENAI']['temperature']
				, top_p=config['OPENAI']['top_p']
				, frequency_penalty=config['OPENAI']['frequency_penalty']
				, presence_penalty=config['OPENAI']['presence_penalty']
			)
			reply = response['choices'][0]['message']['content']
		# Use a self-hosted LLM to generate a reply
		elif reply_method == 'self':
			reply = ''
		# If reply method not specified, return empty string
		else:
			reply = ''
		return reply

	def generate_snarky_comment(self):
		'''
		Generates a snarky comment to be used when a user tries to use a command that does not exist.
		'''
		random.choice(snarky_comments)

	def summarize_url(self, url):
		'''
		Summarizes a given URL using the SMMRY API.
		'''
		response = requests.post(config['SMMRY']['base_url']
			   					+ '?SM_API_KEY=' + config['SMMRY']['api_key']
								+ '&SM_URL=' + url
		)

		if response.status_code != 200:
			print(str(response.status_code), file=sys.stderr)
			return ''

		if 'sm_api_error' in response.json():
			print('Got error: ', response.json()['sm_api_error'], file=sys.stderr)
			return ''

		if 'sm_api_message' in response.json():
			print('Got message: ' + response.json()['sm_api_message'], file=sys.stderr)
			return ''

		summary = response.json()['sm_api_content']
		return summary

	@bridge.bridge_command()
	async def summarize(self, ctx, *, url):
		'''
		Summarizes a given URL using the SMMRY API.
		Ex: -summarize https://www.newsite.com/article
		Dolores would provide a brief summary of the article.
		'''
		await ctx.defer()
		# Sanitize URL first, get rid of any query parameters
		url = url.split('?')[0]
		print('Summarizing URL: ' + url)
		summarized = self.summarize_url(url)
		if summarized == '':
			await ctx.respond('Unable to summarize that URL.')
			return
		await ctx.respond(summarized)
