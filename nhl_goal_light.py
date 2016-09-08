#!/usr/bin/python

import datetime
import time
import os
import random
import requests
# import requests_cache #If I can make the cache work to reduce data

import RPi.GPIO as GPIO  # comment this line out when running on a standard OS (not RPi)
#from lib import gpio_mock as GPIO # comment this line out when running on a RPi

# Setup GPIO on raspberry pi
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Tell the program you want to use pin number 15 as the input and pin 7 as output
GPIO.setup(15, GPIO.IN) # If no input button connected, comment this line out
GPIO.setup(7, GPIO.OUT)
GPIO.output(7, True)

# for requests_cache work
# requests_cache.install_cache()
# requests_cache.clear()


def get_team():
    """ Function to get team of user and return NHL team ID. Default team is CANADIENS. """
    team = raw_input("Enter team you want to setup (without city) (Default: CANADIENS) \n")
    if team is "":
        team = "Canadiens"
    team = team.title()
    # Set URL to list of NHL teams
    url = 'http://statsapi.web.nhl.com/api/v1/teams'
    team_list = requests.get(url)
    team_list = team_list.text[team_list.text.find(team) - 50:team_list.text.find(team)]
    team_id = team_list[team_list.find("id") + 6:team_list.find("id") + 8]
    return team_id


def activate_goal_light():
    """ Function to activate GPIO for goal light and Audio clip. """
    # select random audio clip
    songrandom = random.randint(1, 3) #Set random numbers depending on number of audio clips available
    # Set pin 7 output at high for goal light ON
    GPIO.output(7, False)
    # Prepare commande to play sound (change file name if needed)
    command_play_song = 'sudo mpg123 -q ./audio/goal_horn_{SongId}.mp3'.format(SongId=str(songrandom))
    # Play sound
    os.system(command_play_song)
    # Set pin 7 output at high for goal light OFF
    GPIO.output(7, True)


def fetch_score(team_id):
    """ Function to get the score of the game depending on the chosen team. Inputs the team ID and returns the score found on web. """
    # Get current time
    now = datetime.datetime.now()
    #Set URL depending on team selected and time
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?team_id={}&date={:%Y-%m-%d}'.format(team_id, now)
    # Avoid request errors (might still not catch errors)
    try:
        score = requests.get(url)
        score = score.text[score.text.find("id\" : {}".format(team_id)) - 37:score.text.find("id\" : {}".format(team_id)) - 36]
        score = int(score)
        # Print score for test
        print(score, now.hour, now.minute, now.second)
        return score
    except requests.exceptions.RequestException:
        print "Error encountered, returning 0"
        return 0


def check_season():
    """ Function to check if in season. Returns True if in season, False in off season. """
    # Get current time
    now = datetime.datetime.now()
    if now.month in (7, 8, 9):
        return False
    else:
        return True


def check_if_game(team_id):
    """ Function to check if there is a game now with chosen team. Inputs team ID. Returns True if game, False if NO game. """
    # embed()
    # Get current time
    now = datetime.datetime.now()
    #Set URL depending on team selected and time
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?team_id={}&date={:%Y-%m-%d}'.format(team_id, now)
    try:
        gameday_url = requests.get(url)
    except requests.exceptions.RequestException:    # This is the correct syntax
        pass

    if "gamePk" in gameday_url.text:
        return True
    else:
        return False


def sleep(sleep_period):
    """ Function to sleep if not in season or no game. Inputs sleep period depending if it's off season or no game."""
    # Get current time
    now = datetime.datetime.now()
    # Set sleep time for no game today
    if "day" in sleep_period:
        delta = datetime.timedelta(days=1)
    # Set sleep time for not in season
    elif "season" in sleep_period:
        # If in August, 31 days else 30
        if now.month is 8:
            delta = datetime.timedelta(days=31)
        else:
            delta = timedelta(days=30)
    next_day = datetime.datetime.today() + delta
    next_day = next_day.replace(hour=0, minute=0)
    sleep = next_day - now
    sleep = sleep.total_seconds()
    time.sleep(sleep)

if __name__ == "__main__":

    old_score = 0
    new_score = 0
    gameday = False
    season = False

    print("When a goal is scored, press the GOAL button...")
    try:
        team_id = get_team()  # choose and return team_id to setup code
        # infinite loop
        while (1):
            season = check_season()  # check if in season
            gameday = check_if_game(team_id)  # check if game

            time.sleep(2)  # sleep 2 seconds to avoid errors in requests (might not be enough...)

            if season:
                if gameday:
                    # Check score online and save score
                    new_score = fetch_score(team_id)

                    # If new game, replace old score with 0
                    if old_score > new_score:
                        old_score = 0

                    # If score change...
                    if new_score > old_score:
                        # save new score
                        old_score = new_score
                        activate_goal_light()
                        print "GOAL!"

                    # If the button is pressed
                    # Comment out this section if no input button is connected to RPi
                    if(GPIO.input(15) == 0):
                        # save new score
                        old_score = new_score
                        activate_goal_light()
                else:
                    print "No Game Today!"
                    sleep("day")
            else:
                print "OFF SEASON!"
                sleep("season")

    except KeyboardInterrupt:
        # requests_cache.clear() # Clear requests cache
        # print "\nCache cleaned!"
        
        # Restore GPIO to default state
        GPIO.cleanup()
        print "GPIO cleaned! Goodbye!"
