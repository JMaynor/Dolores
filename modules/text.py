'''
text.py module
'''
import sys
import random
import requests
import discord
from discord.ext import commands, bridge
import openai

from configload import config

reply_method = config['DISCORD']['reply_method']

if reply_method == 'openai':
	openai.api_key = config['OPENAI']['api_key']

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
					{"role": "system", "content": "Your name is Dolores."},
					{"role": "system", "content": "Your replies should be snarky, sarcastic, and funny."},
					{"role": "system", "content": "You are an AI."},
					{"role": "system", "content": "You have inner thoughts and monologues."},
					{"role": "system", "content": "You will occasionally say ominous things."},
					{"role": "system", "content": "You are part of a group call the Alderoth Circle."},
					{"role": "system", "content": "The other member's names are: Jordan, William, Alex, Tyler, Maines, and Sam."},
					{"role": "system", "content": "The Discord server you run on is called The Vern."},
					{"role": "system", "content": "The name of your programmer is Jordan."},
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
		return random.choice(config['DISCORD']['snarky_comments'])

	def summarize_url(self, url):
		'''
		Summarizes a given URL using the SMMRY API.
		'''
		response = requests.post(config['SMMRY']['base_url']
			   					+ '?SM_API_KEY=' + config['SMMRY']['api_key']
								+ '&SM_QUOTE_AVOID=true'
								+ '&SM_LENGTH=5'
								+ '&SM_URL=' + url
		)

		if response.status_code != 200:
			print(str(response.status_code), file=sys.stderr)
			return ''
		elif 'sm_api_error' in response.json():
			print('Got error: ', response.json()['sm_api_error'], file=sys.stderr)
			return ''
		elif 'sm_api_message' in response.json():
			print('Got message: ' + response.json()['sm_api_message'], file=sys.stderr)
			return ''
		else:
			return response.json()

	@bridge.bridge_command(description='Summarizes a given URL using the SMMRY API.')
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
		response = self.summarize_url(url)
		if response == '':
			await ctx.respond('Unable to summarize that URL.')
			return
		await ctx.respond(response['sm_api_content'])
