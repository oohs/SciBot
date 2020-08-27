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

TOKEN = "NzQ3NTk3MTM1MDE2NDkzMzg3.X0RMFg.um6yCeMKhXr91LPLWBvVZ-5XxiA"

bot = commands.Bot(command_prefix = 'sci ')

#get questions from Science Bowl
sb_questions = json.loads(open(os.path.join("corpus", "sb_questions_mcq.json")).read())
questions = sb_questions['questions']

players = []
team_a = []
team_b = []
score_a = 0
score_b = 0

#use this if i ever feel like keeping track of individual score
#class Player():
#	def __init__ (self, user,  score = 0):
#		self.user = user
#		self.score = score
		
def get_team(user):
	if user in team_a:
		return team_a
	elif user in team_b:
		return team_b
	else:
		return None

@bot.event
async def on_ready():
	print(f'{bot.user.name} had connected to Discord!')

@bot.command()
async def join(ctx):

	try:
		await ctx.voice_client.disconnect()
		await ctx.send("Leaving a voice channel to join yours")
	except:
		await ctx.send("Joining!")
	finally:
		try:	
			channel = ctx.author.voice.channel
			await channel.connect()	
		except AttributeError:
			await ctx.send("Make sure you are in a voice channel before using this command")

@bot.command()
async def leave(ctx):
	try:
		await ctx.voice_client.disconnect()
	except:
		await ctx.send("I'm not in a voice channel! :(")

@bot.command()
async def scores(ctx):
	await ctx.send(f"Team A has {score_a} points!\nTeam B has {score_b} points!")

@bot.command()
async def reset(ctx):
	global score_a, score_b, team_a, team_b
	score_a, score_b = 0, 0
	team_a, team_b = [], []
	await ctx.send("The game has reset.\nThe scores are now 0 for both teams.\nPlease join a team!")

@bot.command(aliases = ["lt"])
async def leaveteam(ctx):
	global players,team_a, team_b
	if ctx.author.name not in players:
		await ctx.send("You aren't even in a team")
		return
	else:
		players.remove(ctx.author.name)
		if ctx.author.name in team_a:
			team_a.remove(ctx.author.name)
		elif ctx.author.name in team_b:
			team_b.remove(ctx.author.name)
		else:
			await ctx.send("Something went wrong")
			return
		await ctx.send("You have successfully left your team!")

@bot.command(aliases = ["jt"])
async def jointeam(ctx, name):

	if name == None or (name != 'a' and name != 'b'):
		await ctx.send("Please specify your team: sci team a or sci team b")
	elif ctx.author.name in team_a or ctx.author.name in team_b:
		await ctx.send("You are already in a team!")
	else:
		players.append(ctx.author.name)
		if name == 'a':
			
			team_a.append(ctx.author.name)
			await ctx.send("You have successfully joined team A!")
		else:
			team_b.append(ctx.author.name)
			await ctx.send("You have successfully joined team B!")
	print(team_a)
	print(team_b)


@bot.command(name = "start")
async def mcq(ctx):
	global score_a
	global score_b

	rand_question = random.choice(questions)
	bonus = False
	question = rand_question
	answer = "W"
	if rand_question["tossup_format"] == "Multiple Choice":
		question = rand_question["tossup_question"]
		answer = rand_question["tossup_answer"]
		gTTS(text = "Tossup, " + rand_question['category'] + ", Multiple Choice.",lang = 'en-uk').save('preamble.mp3')
	elif rand_question["bonus_format"] == "Multiple Choice":
		bonus = True
		question = rand_question["bonus_question"]
		answer = rand_question["bonus_answer"]
		gTTS(text='Bonus ' + rand_question['category'] + ", Multiple Choice.",lang='en-uk').save('preamble.mp3')
	
	gTTS(text=question, lang='en-uk', slow=False).save('test.mp3') 
	
	audio = MP3('test.mp3')
	audio_info = audio.info
	length_in_secs = int(audio_info.length)
	
	already_buzzed = []

	print(repr(question))
	
	vc = ctx.voice_client
	vc.play(discord.FFmpegPCMAudio('preamble.mp3'))
	time.sleep(5)
	
	finished = False

	while len(already_buzzed) < 2:
	
		vc.play(discord.FFmpegPCMAudio('test.mp3'), after=lambda e:(print(f"Audio Done: {e}")))
		start = time.time()
		
		message = await ctx.send("BUZZ by reacting to this message")
		await message.add_reaction('\U0001F44D')
	
		print("already_buzzed",already_buzzed)
		
		def check(reaction, user):
			username = str(user)[:-5]
			print("get_team(username)",get_team(username))
			print("username",username)
			return user != bot.user and str(reaction.emoji) == '\U0001F44D' and (username in players) and (get_team(username) not in already_buzzed)


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
					username = str(message.author)[:-5]
					for i in users[1:]:
						j = str(i)[:-5]
						if (j in players) and (get_team(j) not in already_buzzed):
							print("username 2",username)
							return username == j
				
				await ctx.send(f'{user.mention} buzzed first!\nType your answer choice (W,X,Y,Z)!')

				msg = None
				try:
					msg = await bot.wait_for('message',timeout=3.0, check=check2)
				except asyncio.TimeoutError:		
					await ctx.send("Stop stalling! No points.")
				finally:
					user_answer = None
					already_buzzed.append(get_team(user.name))
					print("user.name",user.name)
					print(already_buzzed)
					if msg != None:
						user_answer = msg.content.lower() 


					if user_answer == answer[0].lower():
						await ctx.send(f"That's right! {user.mention}")
						if get_team(user.name) == team_a:
							score_a += 4
						elif get_team(user.name) == team_b:
							score_b += 4
					elif len(already_buzzed) == 1:
						await ctx.send(f"I'm sorry that is incorrect! {user.mention}")

						await ctx.send("The other team now has 5.0 seconds to type an answer (W,X,Y,Z).")
	
						def check3(message):
							username=str(message.author)[:-5]
							return get_team(username) not in already_buzzed and username in players
							
						try:
							msg = await bot.wait_for('message',timeout = 5.0, check =check3)
						except asyncio.TimeoutError:
							await ctx.send("Nobody gets points!")
						finally:
							user_answer = None
							if msg != None:
								user_answer = msg.content.lower() 
							
							
							if user_answer == answer[0].lower():
								await ctx.send(f"That's right! {msg.author.name} ")
								if get_team(user.name) == team_a:
									score_a += 4
								elif get_team(user.name) == team_b:
									score_b += 4
							else:
								await ctx.send(f"I'm sorry, that is incorrect!")	

						
					else:
						await ctx.send("Both teams were incorrect.")
					break
		
			else:
				await ctx.send(f'{user.mention} INTERRUPTED and buzzed first!\nType for answer choice (W,X,Y,Z)!')
			
				users = await reaction.users().flatten()
			
				def check2(message):
					username = str(message.author)[:-5]
					for i in users[1:]:
						j = str(i)[:-5]
						if (j in players) and (get_team(j) not in already_buzzed):
							return username == j
				msg = None
				try:
					msg = await bot.wait_for('message',timeout=3.0, check=check2)
				except asyncio.TimeoutError:
					await ctx.send("Stop stalling! No points.")
				finally:
					user_answer = None
					if msg != None:
						user_answer = msg.content.lower() 

					if user_answer== answer[0].lower():
						await ctx.send(f"That's right! {user.mention}")
						if get_team(user.name) == team_a:
							score_a += 4
						elif get_team(user.name) == team_b:
							score_b += 4
						break
					else:
						await ctx.send(f"I'm sorry that is incorrect! {user.mention}")
						
						if get_team(user.name) == team_a:
							score_b += 4
						elif get_team(user.name) == team_b:
							score_a += 4
						if len(already_buzzed) == 0:
							await ctx.send("I'm going to repeat the question now and the other team has a chance to answer.")	
						else:
							await ctx.send("Both teams got it wrong!")
							break
		
				already_buzzed.append(get_team(str(user.name)))
				print("pro-interrupt already buzzed:",already_buzzed)
				await message.clear_reaction('\U0001F44D')


	await ctx.send("The question was:\n"+question)
	await ctx.send("The correct answer was:\n"+answer)


bot.run(TOKEN)



