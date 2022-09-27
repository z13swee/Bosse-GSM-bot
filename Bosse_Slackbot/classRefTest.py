class SMSBOT(object):
    def __init__(self):
        print("SMSBOT INIT")
    def sendussd(self):
        print("Sending ussd..")

class SLACK(object):
    def __init__(self, SMSbot):
        print("Starting slack bot..")
        self._SMSbot = SMSbot

    def handlecmd(self):
        self._SMSbot.sendussd()


if __name__=="__main__":

    smsBot=SMSBOT()
    # Start slack bot with a referense too smsbot
    slackBot = SLACK(smsBot)
    slackBot.handlecmd()
