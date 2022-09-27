# coding=utf-8
import os
import time
import re
import random
import threading
from slackclient import SlackClient
from Middagar_generator import generate
from Middagar_generator import parseString
from datetime import datetime
from threading import Timer
import subprocess

# TODO:

# Posta ett fredags demo!
# Posta nyheter ifrån slashdot?
# Posta gåtor varje fredag?
# -Statestik- , Veckans mest aktiva med X antal ord


# Rensa bort alla themes å tunes? det är ju inte demos..
demos = ["https://www.youtube.com/watch?v=MUa3tYhi-1o&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=3&t=0s",
         "https://www.youtube.com/watch?v=oAXN-43b5mQ&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=4&t=0s",
         "https://www.youtube.com/watch?v=pMW44Ih22Go&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=5&t=0s",
         "https://www.youtube.com/watch?v=E8oQ6l18cA4&t=0s&index=6&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=XA_264OfBtU&t=0s&index=7&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=B4gC397tdlY&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=8&t=0s",
         "https://www.youtube.com/watch?v=O3QiO0rPL-U&t=0s&index=9&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=ejss7u2hABo&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=10&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=HrnbJgyEB0g&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=11&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=t7S6qod6tZ8&t=0s&index=12&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=b39O1WkWdYc&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=13&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=fNe24yzNyGg&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=14&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=QGEkhciEoM4&t=0s&index=15&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=QxnULOCntpA&t=0s&index=16&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=nf29ShkoAiA&t=0s&index=17&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=Mvhxgfud0Qs&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=18&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=c3XOCUzAoeE&t=0s&index=19&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=oC3Q5ZZpMG8&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=20&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=HVyoAVFTlGI&t=0s&index=21&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=OR7BrNkBe7k&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=22&t=0s", #  The Secret of Monkey Island - Main Theme
         "https://www.youtube.com/watch?v=pH899QpQMrA&t=0s&index=23&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=DRqvpskK4zc&t=0s&index=24&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=_o-75551uC0&t=0s&index=25&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=baUX3sTvHZU&t=0s&index=26&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k", # "Bara" musik
         "https://www.youtube.com/watch?v=gILuCuYVS3Q&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=27&t=0s", # "Bara" musik
         "https://www.youtube.com/watch?v=N5CNlMGcARA&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=28&t=0s", # DRM UBISOFT Settler 7 Cracktro Razor1911
         "https://www.youtube.com/watch?v=xey4G0FQvbE&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=29&t=0s",
         "https://www.youtube.com/watch?v=JlXwmw8UY9w&t=0s&index=30&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=MD-k8Oxkalc&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=31&t=0s",
         "https://www.youtube.com/watch?v=DDLi11B8ezs&t=0s&index=32&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=HsXB7F0lQwY&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=33&t=0s",
         "https://www.youtube.com/watch?v=fBIIIX6xvos&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k&index=34&t=0s",
         "https://www.youtube.com/watch?v=LHRwFrVPM7A&t=0s&index=35&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=_BUbMubMxBs&t=0s&index=36&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=AJU4i2VXzy0&t=418s&index=37&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=ZazU4H2OZFg&t=150s&index=38&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=hhoa_K75BKI&t=11s&index=39&list=PL-NGVGr3ePHXRMPaaZ467zS2M7VzYrm_k",
         "https://www.youtube.com/watch?v=HW6p6q6a1Ds",
         "https://www.youtube.com/watch?v=upsriS-b03c",
         "https://www.youtube.com/watch?v=zI6iIRT5qjw",
	     "https://www.youtube.com/watch?v=xi5Awxd_9DY", # Sista ifrån demos2
         "https://www.youtube.com/watch?v=P77q90n19dI&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=2&t=0s", # Första ifrån demos
         "https://www.youtube.com/watch?v=CBzWsm3Zb2w&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=3&t=0s",
         "https://www.youtube.com/watch?v=Q76ZepI_44Y&index=4&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=GjDReXe9T3w&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=5&t=0s",
         "https://www.youtube.com/watch?v=XlMw38Cpeqo&index=6&t=58s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=nNbOiilNz2M&index=7&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=uUfuRBys1-U&index=8&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=4xUJl7qbueg&index=9&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=3yZmxjOnO30&index=10&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=Av_YF4ocPpk&index=11&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=WNemsvUMgDM&index=12&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=z9GorwPlPJc&index=13&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=IDOjDZ_NQ1Q&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=14&t=0s",
         "https://www.youtube.com/watch?v=v21g6sNMO9I&index=15&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=L8onlB0F1_A&index=16&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=iQqJm14sHRY&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=17&t=0s",
         "https://www.youtube.com/watch?v=ZfuierUvx1A&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=18&t=0s",
         "https://www.youtube.com/watch?v=YJosZfm560Q&index=19&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=Q5nh5HKAIlo&index=20&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=UY_YEbNwDmM&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=21&t=0s",
         "https://www.youtube.com/watch?v=5ImoF4CoA_M&index=22&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC",
         "https://www.youtube.com/watch?v=d2QQA7nYRcM&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=23&t=0s",
         "https://www.youtube.com/watch?v=GXdOLkLrnok&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC&index=24&t=0s",
         "https://www.youtube.com/watch?v=1MGZ7LTwwoc&index=25&t=0s&list=PL-NGVGr3ePHVcheCw83JhtIMalkPZzglC", # Sista ifrån demos
         "https://www.youtube.com/watch?v=QTvnYkmtleI" # Pico 8 demo
         ]

class SLACKBot(object):
    # constants
    RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
    EXAMPLE_COMMAND = "!"
    MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
    DM_REGEX = "^(!\S*)"
    BOT_ID = None
    SLACK_CLIENT = None

    failedAttempts = 0;
    maxAttempts = 4 # Antal misslyckande försök tills boten slutar svara på invalida commandon

    timeoutDict = {} # Här sparas Channel, Attempts för att hålla kolla på vilka channel's
    timerStarted = False

    trusted_users = ["XXXXXXX"]

    default_IDontKnow_respones = ["Jag har ingen aning om vad du pratar om..", "Va?","Vet du vem du pratar med?","Kom inte med sådan där skit","01011110101010111021010110111010","Svaret ligger i dimman"]

    def __init__(self, SMSbot=None):
        print("Starting slack bot..")
        self._SMSbot = SMSbot

    def run(self):

        # instantiate Slack client
        global SLACK_CLIENT
        SLACK_CLIENT = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

        for x in range(2):
            if SLACK_CLIENT.rtm_connect(with_team_state=False):
                print("Bosse Bot connected and running!")
                # Read bot's user ID by calling Web API method `auth.test`
                self.BOT_ID = SLACK_CLIENT.api_call("auth.test")["user_id"]
                print("My ID: {}".format(self.BOT_ID))

                while True:
                    try:
                        command, channel, isDirectMessage = self.parse_bot_commands(SLACK_CLIENT.rtm_read())

                        if command:
                            if channel in self.timeoutDict:
                                if self.timeoutDict[channel] < self.maxAttempts:
                                    if isDirectMessage:
                                        self.handle_directMessage_command(command, channel)
                                    else:
                                        self.handle_channel_command(command, channel)
                            else:
                                if isDirectMessage:
                                    self.handle_directMessage_command(command, channel)
                                else:
                                    self.handle_channel_command(command, channel)
                    except Exception as e:
                    	print("Error: {}".format(e))


                    time.sleep(self.RTM_READ_DELAY)
            else:
                print("Connection failed, trying add enviroment token..")
                call(["export", "SLACK_BOT_TOKEN=xoxb-239225624465-540275181282-6nd79pUEavpVM5mU0NrUWigR"])

        print("Connection failed. Exception traceback printed above.")

    def parse_bot_commands(self,slack_events):

        for event in slack_events:
            #print(event)
            if event["type"] == "message" and not "subtype" in event:
                print(event)
                # Determine if message is in Channel or Direct Message
                # This should be done with channel_type? but that is missing..

                # So we are doing this the cave man way,
                # If the first letter in 'channel' is:
                # D = Direct message
                # C = Channel
                # G = it's either a private channel or multi-person DM

                # Parse messages from a Direct Message, to see check for command
                if event["channel"][0] == 'D':
                    # D = DirectMessage
                    isDirectMessage = True

                    # TODO: Check if trusted user

                    return event["text"], event["channel"],isDirectMessage


                # Parse messages from a channel, to see if we are mentioned
                if event["channel"][0] == 'C':
                    isDirectMessage = False

                    # User regex to extract mention and command fom text
                    matches = re.search(self.MENTION_REGEX, event["text"])

                    user_id, message = (matches.group(1), matches.group(2).strip()) if matches else (None, None)

                    if user_id == self.BOT_ID:
                        return message, event["channel"], isDirectMessage

        return None, None, None


    def handle_channel_command(self,command, channel):
        print("Handle Command from a Channel: {} Channel: {}".format(command,channel))

        # Default response is help text for the user
        default_response = self.default_IDontKnow_respones[random.randint(0,len(self.default_IDontKnow_respones)-1)]

        # Finds and executes the given command, filling in response
        response = None

        #print("Answering with: {}".format(response or default_response))
        #self.send_message(channel,response or default_response) # if response is None, replay with default_response
        self.respondOrNotToRespond(channel ,response or default_response)


    def handle_directMessage_command(self,command, channel):
        print("Handle Command from a Direct Message: {} Channel: {}".format(command,channel))

        # Default response is help text for the user
        default_response = self.default_IDontKnow_respones[random.randint(0,len(self.default_IDontKnow_respones)-1)]

        # Finds and executes the given command, filling in response
        response = None

        # User regex to extract command fom text
        matches = re.search(self.DM_REGEX, command)

        if matches:
            # the first group contains the command
            if matches.group(1) == "!saldo":
                if not self._SMSbot:
                    response = ("Jag saknar min polare Bosse SMS! :(")
                else:
                    self.send_message(channel,"Ok, får se...")
                    # Call smsbot for saldo
                    response = self._SMSbot.dummy_sendUSSD("*101#")

        # Here is to check if we got a food generating request with the parseString function of middag gen
        response = parseString(joined_arguments)

        #print("Answering with: {}".format(response or default_response))
        #self.send_message(channel,response or default_response) # if response is None, replay with default_response
        self.respondOrNotToRespond(channel, response , default_response)


    def respondOrNotToRespond(self, channel, response, default_response):
        # Detta är ett försök att motverka flooding, så att channeln blir timeoutad i 20sec om mer
        # än self.maxAttempts försöks av felaktiga kommandon/text
        if not response:
            if channel in self.timeoutDict:
                self.timeoutDict[channel] += 1
                print("Adding attempts on channel {}  attempts: {}".format(channel,self.timeoutDict[channel]))
            else:
                self.timeoutDict[channel] = 1
                print("Adding channel {}  attempts: {}".format(channel,self.timeoutDict[channel]))

            if self.timeoutDict[channel] < self.maxAttempts:
                print("Answering with: {}".format(default_response))
                self.send_message(channel,default_response) # if response is None, replay with default_response
                self.failedAttempts += 1 # and add to failed attempts
            else:
                if not self.timerStarted:
                    print("Answering with: Äh, du får klara dig själv")
                    self.send_message(channel,"Äh, du får klara dig själv") # if response is None, replay with default_response
                    # Start reset timer for attempts
                    timer = threading.Timer(20.0, self.resetAttempts, [channel])
                    timer.start()
                    self.timerStarted = True
        else:
            print("Answering with: {}".format(response))
            self.send_message(channel,response)


    def resetAttempts(self, channel):
        print("Deleting {} from dictonary".format(channel))
        del self.timeoutDict[channel]
        self.timerStarted = False

    def send_message(self,channel,msg):
        SLACK_CLIENT.api_call(
            "chat.postMessage",
            channel=channel,
            text=msg
        )

if __name__ == "__main__":
    bot = SLACKBot()
    bot.run()
