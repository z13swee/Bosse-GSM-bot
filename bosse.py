# coding=utf-8
from bosse_slackBot import SLACKBot
from bosse_smsbot import SMS
import logging
"""
Detta script kommer sköta både SMS boten och Slack boten,
för att dom ska kunna kommunicera mellan varandra..
"""
bosse_banner2 = """\




+-----------------------------------------------------------------------------+
    ____         ______                                           ____
   |    ~.     .~      ~.              ..''''             ..'''' |
   |____.'_   |          |          .''                .''       |______
   |       ~. |          |       ..'                ..'          |
   |_______.'  `.______.'  ....''             ....''             |___________
+-----------------------------------------------------------------------------+
[                                 '-.-'                                       ]"""


if __name__=="__main__":

    try:
        print(bosse_banner2)

        # Start sms bot s=SMS(PORT,BAUD,loglevel=logging.DEBUG)
        smsBot=SMS("/dev/ttyS0",115200)

        # Start slack bot with a referense too smsbot
        slackBot = SLACKBot(smsBot)
        slackBot.run()

    except Exception as e:
        print("{} , exiting..".format(e))
        exit(1)
