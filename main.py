import discord
import json
import os
import random
import asyncio
import time

from mutagen.mp3 import MP3

from gtts import gTTS


from discord.ext import commands
from discord.voice_client import VoiceClient

TOKEN ="NzQ3NTk3MTM1MDE2NDkzMzg3.X0RMFg.RtOaFd0Y0UMtcRCbwrEewnx6FqQ" 
bot = commands.Bot(command_prefix = 'sci ')

#get questions from Science Bowl
sb_questions = json.loads(open(os.path.join("corpus", "sb_questions_mcq.json")).read())
questions = sb_questions['questions']

@bot.event
async def on_ready():
	print(f'{bot.user.name} had connected to Discord!')

@bot.command()
async def join(ctx):
	channel = ctx.author.voice.channel
	await channel.connect()	

@bot.command()
async def leave(ctx):
	await ctx.voice_client.disconnect()


@bot.command(name = "start")
async def mcq(ctx):
	rand_question = random.choice(questions)
	bonus = False
	question = rand_question
	answer = "W"
	if rand_question["tossup_format"] == "Multiple Choice":
		question = rand_question["tossup_question"]
		answer = rand_question["tossup_answer"]
	elif rand_question["bonus_format"] == "Multiple Choice":
		bonus = True
		question = rand_question["bonus_question"]
		answer = rand_question["bonus_answer"]
	question = question.strip('\n')
	gTTS(text=question, lang='en', slow=False).save('test.mp3') 
	
	audio = MP3('test.mp3')
	audio_info = audio.info
	length_in_secs = int(audio_info.length)
	
	already_buzzed = []

	print(repr(question))
	
	vc = ctx.voice_client
	finished = False

	while len(already_buzzed) < 2:
		vc.play(discord.FFmpegPCMAudio('test.mp3'), after=lambda e:(print(f"Audio Done: {e}")))
		start = time.time()
		
		message = await ctx.send("BUZZ by reacting to this message")
		await message.add_reaction('\U0001F44D')
	

		def check(reaction, user):
			return user != bot.user and str(reaction.emoji) == '\U0001F44D' and user not in already_buzzed


		try:
			reaction, user = await bot.wait_for('reaction_add', timeout=length_in_secs + 5, check=check)
		except asyncio.TimeoutError:
			await ctx.send("Nobody Answered!")
			break
		else:
			vc.pause()
			end = time.time()

			elapsed = end - start
			if elapsed > length_in_secs:
				finished = True
			if finished:
				users = await reaction.users().flatten()
		
				def check2(message):
					return message.author == users[1] and message.author not in already_buzzed 

				await ctx.send(f'{user.mention} buzzed first!\nType your answer choice (W,X,Y,Z)!')
				msg = None
				try:
					msg = await bot.wait_for('message',timeout=3.0, check=check2)
				except asyncio.TimeoutError:		
					await ctx.send("Stop stalling! No points.")
				finally:
					if msg != None:
						if msg.content.lower() == answer[0].lower():
							await ctx.send(f"That's right! {user.mention}")
					elif len(already_buzzed) == 0:
						await ctx.send(f"I'm sorry that is incorrect! {user.mention}")
						already_buzzed.append(users[1])

						await ctx.send("The other team now has 5.0 seconds to type an answer (W,X,Y,Z).")
	
						def check3(message):
							return message.author not in already_buzzed
						try:
							msg = await bot.wait_for('message',timeout = 5.0, check =check3)
						except asyncio.TimeoutError:
							await ctx.send("Nobody gets points!")
						finally:
							if msg != None:
								if msg.content.lower() == answer[0].lower():
									await ctx.send(f"That's right! {user.mention}")
							else:
								await ctx.send(f"I'm sorry, that is incorrect! {user.mention}")	

						
					else:
						await ctx.send("Both teams  were incorrect.")
					break
		
			else:
				await ctx.send(f'{user.mention} INTERRUPTED and buzzed first!\nType for answer choice (W,X,Y,Z)!')
			
				users = await reaction.users().flatten()
			
				def check2(message):
					return message.author == users[1] and message.author not in already_buzzed
				msg = None
				try:
					msg = await bot.wait_for('message',timeout=3.0, check=check2)
				except asyncio.TimeoutError:
					await ctx.send("Stop stalling! No points.")
				finally:
					if msg != None: 
						if msg.content.lower() == answer[0].lower():
							await ctx.send(f"That's right! {user.mention}")
							break
					else:
						await ctx.send(f"I'm sorry that is incorrect! {user.mention}")
						if len(already_buzzed) == 0:
							await ctx.send("I'm going to repeat the question now and the other team has a chance to answer.")	
						else:
							await ctx.send("Both teams got it wrong!")
							break
				already_buzzed.append(users[1])
				await message.clear_reaction('\U0001F44D')

	await ctx.send("The question was:\n"+question)
	await ctx.send("The correct answer was:\n"+answer)
bot.run(TOKEN)



