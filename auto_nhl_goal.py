#!/usr/bin/env python

from datetime import datetime
import time, os, random
import requests
import RPi.GPIO as GPIO
#import subprocess, ctypes

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#Tell the program you want to use pin number 15 as the input and pin 7 as output
GPIO.setup(15, GPIO.IN)
GPIO.setup(7,GPIO.OUT)
GPIO.output(7,True)

def activate_goal_light():
	#select random audio clip
	songrandom=random.randint(1, 3)
	#Set pin 7 output at high for goal light ON
	GPIO.output(7,False)
	#Play sound
	command_play_song="sudo mpg123 ./audio/goal_horn_%s.mp3" % str(songrandom)
	os.system(command_play_song)
	#Set pin 7 output at high for goal light OFF
	GPIO.output(7,True)

def fetch_score(game_id):
	season_id = game_id[:4] + str(int(game_id[:4])+1)
        url="http://live.nhle.com/GameData/%s/%s/gc/gcbx.jsonp" % (season_id,game_id)
	score=requests.get(url)
	score=score.text[score.text.find("goalSummary"):]
	score=score.cout('t1...MTL')
	return score

def check_season():
	now = datetime.now()
	while now.month in (7, 8, 9):
            if now.day < 23 and now.month < 9:
            	print "OFF SEASON!"
		time.sleep(604800)
		now = datetime.datetime.now()

def check_if_game():
	now=datetime.now()
        url="http://live.nhle.com/GameData/GCScoreboard/%s.jsonp" % (now.strftime("%Y-%m-%d"))
        MTL=requests.get(url)
	while "NYI" not in MTL.text:
		print "No game today!"
		time.sleep(43200)
		now=datetime.now()
        	url="http://live.nhle.com/GameData/GCScoreboard/%s.jsonp" % (now.strftime("%Y-%m-%d"))
        	MTL=requests.get(url)
	game_id=MTL.text[MTL.text.find("ISLANDERS"):MTL.text.find("id")+14]
	game_id = game_id[game_id.find("id")+4:]
	return game_id
	

#MAIN

#init        	
old_score=0
new_score=0

print ("When a goal is scored, please press the GOAL button...")
try:
	while (1):
	
		#check_season() #check if in season
		game_id=check_if_game() #check if game tonight/need to update with today's date
		#check the state of the button/site two times per second
		time.sleep(0.5)
		
		#Check score online and save score
		new_score=fetch_score(game_id)
			    
		#If new game, replace old score with 0
		if old_score > new_score:
			old_score=0
			
		#If score change...
		if new_score > old_score:
			#save new score
			old_score=new_score
			activate_goal_light()
	
		#If the button is pressed
		if(GPIO.input(15)==0):
			#save new score
			old_score=new_score
			activate_goal_light()

except KeyboardInterrupt:					
	#Restore GPIO to default state
	GPIO.cleanup()
	print ("'\nGPIO cleaned! Goodbye!")
