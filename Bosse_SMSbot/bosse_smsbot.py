# coding=utf-8
from serial import Serial
#from pynput.keyboard import Key, Listener
import os
import queue
#import RPi.GPIO as IO, atexit, logging, sys
import logging,sys,re,binascii,time,sys

from time import sleep
from enum import IntEnum
from datetime import datetime
from Middagar_generator import generate

# TODO: Problem om sms svaret blir för långt?
# TODO: !commands Respones (ex, !lists skickar alla tillgängliga listor till förfrågaren)
    # !listor ger tillgängliga listor (som är publika)
    # !saldo  ger pengar på kortet

# TODO: Logga sms to fil
# TODO: Se till att inte ha 70st sms i SM memorey, för då kan du inte ta emot fler, dom sms kommer när det finns plats isf

# TODO: Fixa så att man kan kombinera listor
# TODO: Fixa så Middagarna kan han text assioserat till dem, som inköps lista eller länk till recept ( kanske ha det som inköps lista, och om man har länk så detekteras det)

# TODO: Låt bosse användas som en 'reminder', Skicka påminnelse sms när någon fyller år etc.


PORT="/dev/ttyS0"
BAUD=115200
DATE_FMT='"%y/%m/%d,%H:%M:%S%z"'

BALANCE_USSD="*101#"

class ATResp(IntEnum):
    ErrorNoResponse=-1
    ErrorDifferentResponse=0
    OK=1

class SMSMessageFormat(IntEnum):
    PDU=0
    Text=1

class SMSTextMode(IntEnum):
    Hide=0
    Show=1

class SMSStatus(IntEnum):
    Unread=0
    Read=1
    Unsent=2
    Sent=3
    All=4

class RSSI(IntEnum):
    """
    Received Signal Strength Indication as 'bars'.
    Interpretted form AT+CSQ return value as follows:

    ZeroBars: Return value=99 (unknown or not detectable)
    OneBar: Return value=0 (-115dBm or less)
    TwoBars: Return value=1 (-111dBm)
    ThreeBars: Return value=2...30 (-110 to -54dBm)
    FourBars: Return value=31 (-52dBm or greater)
    """

    ZeroBars=0
    OneBar=1
    TwoBars=2
    ThreeBars=3
    FourBars=4

    @classmethod
    def fromCSQ(cls, csq):
        csq=int(csq)
        if csq==99: return cls.ZeroBars
        elif csq==0: return cls.OneBar
        elif csq==1: return cls.TwoBars
        elif 2<=csq<=30: return cls.ThreeBars
        elif csq==31: return cls.FourBars

class NetworkStatus(IntEnum):
    NotRegistered=0
    RegisteredHome=1
    Searching=2
    Denied=3
    Unknown=4
    RegisteredRoaming=5

class SMS(object):

    last_SMS_Phonenumber = ""
    last_SMS_Message = ""
    last_SMS_date = ""

    def __init__(self, port="/dev/ttyS0", baud=115200, logger=None, loglevel=logging.DEBUG):
        print("Starting SMS bot..")

        self._port=port
        self._baud=baud

        self._ready=False
        self._serial=None


        if logger:
            self._logger=logger
        else:
            # Check if there is more then 1 handle?
            #print(len(self._logger.handlers))

            self._logger=logging.getLogger("SMS")
            handler=logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(asctime)s : %(levelname)s -> %(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(loglevel)

            self._logger.propagate = False

        self.setup()
        print("[      PORT= {}   BAUD= {}    DATE= {}    ]".format(self._port,self._baud,datetime.now()))
        #if not s.turnOn(): exit(1)     #disabling this so i can see with minicom whats happening..
        if not self.setEcho(0): exit(1)

        # TODO: Add sending pin code..

        self.setCharset("GSM")

    def setup(self):
        self._logger.debug("Setup")
        self._serial=Serial(self._port, self._baud)




    def reset(self):

        self._logger.debug("Reset (duration ~6.2s)")
        IO.output(GSM_ON, IO.HIGH)
        sleep(1.2)
        IO.output(GSM_ON, IO.LOW)
        sleep(5.)

    def sendATCmdWaitResp(self, cmd, response, timeout=.5, interByteTimeout=.1, attempts=1, addCR=False):

        self._logger.debug("Send AT Command: {}".format(cmd))
        self._serial.timeout=timeout
        self._serial.inter_byte_timeout=interByteTimeout

        status=ATResp.ErrorNoResponse
        for i in range(attempts):
            bcmd=cmd.encode('utf-8')+b'\r'
            if addCR: bcmd+=b'\n'

            self._logger.debug("Attempt {}, ({})".format(i+1, bcmd))
            #self._serial.write(cmd.encode('utf-8')+b'\r')
            self._serial.write(bcmd)
            self._serial.flush()

            lines=self._serial.readlines()
            lines=[l.decode('utf-8').strip() for l in lines]
            lines=[l for l in lines if len(l) and not l.isspace()]
            self._logger.debug("Lines: {}".format(lines))
            if len(lines)<1: continue
            line=lines[-1]
            self._logger.debug("Line: {}".format(line))

            if not len(line) or line.isspace(): continue
            elif line==response: return ATResp.OK
            else: return ATResp.ErrorDifferentResponse
        return status

    def sendATCmdWaitReturnResp(self, cmd, response, timeout=.5, interByteTimeout=.1):

        self._logger.debug("Send AT Command: {}".format(cmd))
        self._serial.timeout=timeout
        self._serial.inter_byte_timeout=interByteTimeout

        self._serial.write(cmd.encode('utf-8')+b'\r')
        self._serial.flush()

        lines=self._serial.readlines()
        for n in range(len(lines)):
            try:
                lines[n]=lines[n].decode('utf-8').strip()
            except UnicodeDecodeError:
                lines[n]=lines[n].decode('latin1').strip()

        lines=[l for l in lines if len(l) and not l.isspace()]
        self._logger.debug("Lines: {}".format(lines))

        if not len(lines): return (ATResp.ErrorNoResponse, None)

        _response=lines.pop(-1)

        self._logger.debug("Response: {}".format(response))
        self._logger.debug("_response: {}".format(_response))

        if not len(_response) or _response.isspace(): return (ATResp.ErrorNoResponse, None)
        elif response==_response: return (ATResp.OK, lines)

        return (ATResp.ErrorDifferentResponse, None)

    def parseReply(self, data, beginning, divider=',', index=0):

        self._logger.debug("Parse Reply: {}, {}, {}, {}".format(data, beginning, divider, index))
        if not data.startswith(beginning): return False, None
        data=data.replace(beginning,"")
        data=data.split(divider)
        try: return True,data[index]
        except IndexError: return False, None

    def getSingleResponse(self, cmd, response, beginning, divider=",", index=0, timeout=.5, interByteTimeout=.1):

        status,data=self.sendATCmdWaitReturnResp(cmd,response,timeout=timeout,interByteTimeout=interByteTimeout)

        print("status = {}".format(status))
        print("Data = {}".format(data))

        if status!=ATResp.OK: return None
        if len(data)!=1: return None
        ok,data=self.parseReply(data[0], beginning, divider, index)
        if not ok: return None
        return data




    def sendATCommand(self, cmd, response, timeout=.5, interByteTimeout=.1):
        # Om AT+CSCS=USC2 så måste alla commandon vara codat till USC2

        self._logger.debug("Send AT Command: {}".format(cmd))
        self._serial.timeout=timeout
        self._serial.inter_byte_timeout=interByteTimeout

        self._serial.write(cmd.encode('utf-8')+b'\r')
        self._serial.flush()

        lines=self._serial.readlines()
        for n in range(len(lines)):
            try:
                lines[n]=lines[n].decode('utf-8').strip()
            except UnicodeDecodeError:
                lines[n]=lines[n].decode('latin1').strip()

        lines=[l for l in lines if len(l) and not l.isspace()]
        self._logger.debug("Lines: {}".format(lines))

        if not len(lines): return (ATResp.ErrorNoResponse, None)

        _response=lines.pop(-1)
        self._logger.debug("Response: {}".format(_response))
        if not len(_response) or _response.isspace(): return (ATResp.ErrorNoResponse, None)
        elif response==_response: return (ATResp.OK, lines)

        return (ATResp.ErrorDifferentResponse, None)


    def turnOn(self):
        # Turn on the module
        self._logger.debug("Turn On")
        for i in range(2):
            status=self.sendATCmdWaitResp("AT", "OK", attempts=5)
            if status==ATResp.OK:
                self._logger.debug("GSM module ready.")
                self._ready=True
                return True
            elif status==ATResp.ErrorDifferentResponse:
                self._logger.debug("GSM module returned invalid response, check baud rate?")
            elif i==0:
                self._logger.debug("GSM module is not responding, resetting...")
                self.reset()
            else: self._logger.error("GSM module failed to respond after reset!")
        return False

    def setEcho(self, toggle):
        if toggle:
            self._logger.debug("Set Echo On")
            status=self.sendATCmdWaitResp("ATE1", "OK")
            return status==ATResp.OK
        else:
            self._logger.debug("Set Echo Off")
            status=self.sendATCmdWaitResp("ATE0", "OK")
            return status==ATResp.OK




    def getLastError(self):

        self._logger.debug("Get Last Error")
        error=self.getSingleResponse("AT+CEER","OK","+CEER: ")
        return error

    def getIMEI(self):

        self._logger.debug("Get International Mobile Equipment Identity (IMEI)")
        status,imei=self.sendATCmdWaitReturnResp("AT+GSN","OK")
        if status==ATResp.OK and len(imei)==1: return imei[0]
        return None

    def getVersion(self):

        self._logger.debug("Get TA Revision Identification of Software Release")
        revision=self.getSingleResponse("AT+CGMR","OK","Revision",divider=":",index=1)
        return revision

    def getSIMCCID(self):

        self._logger.debug("Get SIM Integrated Circuit Card Identifier (ICCID)")
        status,ccid=self.sendATCmdWaitReturnResp("AT+CCID","OK")
        if status==ATResp.OK and len(ccid)==1: return ccid[0]
        return None

    def getNetworkStatus(self):

        self._logger.debug("Get Network Status")
        status=self.getSingleResponse("AT+CREG?","OK","+CREG: ",index=1)
        if status is None: return status
        return NetworkStatus(int(status))

    def getRSSI(self):

        self._logger.debug("Get Received Signal Strength Indication (RSSI)")
        csq=self.getSingleResponse("AT+CSQ","OK","+CSQ: ")
        if csq is None: return csq
        return RSSI.fromCSQ(csq)

    def enableNetworkTimeSync(self, enable):
        self._logger.debug("Enable network time synchronisation")
        status=self.sendATCmdWaitResp("AT+CLTS={}".format(int(enable)),"OK")
        return status==ATResp.OK

    def getTime(self):

        self._logger.debug("Get the current time")
        time=self.getSingleResponse("AT+CCLK?","OK","+CCLK: ", divider="'")
        if time is None: return time
        return datetime.strptime(time[:-1]+'00"', DATE_FMT)

    def setTime(self, time):

        self._logger.debug("Set the current time: {}".format(time))
        time=datetime.strftime(time, DATE_FMT)
        if time[-4]!="+": time=time[:-1]+'+00"'
        status=self.sendATCmdWaitResp("AT+CCLK={}".format(time),"OK")
        return status==ATResp.OK

    def setCharset(self,set):
        """
        Set charecter set
        "GSM"       GSM 7 bit default alphabet (3GPP TS 23.038);
        "UCS2"      16-bit universal multiple-octet coded character set (ISO/IEC10646) UCS2  character  strings  are  converted  to  hexadecimal     numbers     from     0000     to     FFFF;     e.g. "004100620063" equals three 16-bit characters with decimal values 65, 98 and 99
        "IRA"       International  reference alphabet (ITU-T T.50)
        "HEX"       Character strings consist only of hexadecimal bers from 00 to FF;
        "PCCP"      PC  character  set  Code
        "PCDN"      PC  Danish/Norwegian  character  set
        "8859-1"    ISO 8859 Latin 1 character set

        cmd             Response
        AT+CSCS=?       +CSCS: (list of supported <chset>s)
                        OK
        AT+CSCS?        +CSCS: <chset>
                        OK
        AT+CSCS=<chset> OK

        ERROR           +CME ERROR: <err>

        """

        #TODO: Check if set = valid charset
        self._logger.debug("Setting to use Unicode ({})".format(time,set))

        status=self.sendATCmdWaitResp("AT+CSCS=\"{}\"".format(set), "OK",addCR=True)
        return status==ATResp.OK

    def stringToUSC2(self, sting):
        txt = sting.encode("UTF-16BE")
        return txt.hex()

    def setSMSMessageFormat(self, format):

        status=self.sendATCmdWaitResp("AT+CMGF={}".format(format), "OK")
        return status==ATResp.OK

    def setSMSTextMode(self, mode):
        status=self.sendATCmdWaitResp("AT+CSDH={}".format(mode), "OK")
        return status==ATResp.OK

    def getNumSMS(self):

        self._logger.debug("Get Number of SMS")
        if not self.setSMSMessageFormat(SMSMessageFormat.Text):
            self._logger.error("Failed to set SMS Message Format!")
            return False

        if not self.setSMSTextMode(SMSTextMode.Show):
            self._logger.error("Failed to set SMS Text Mode!")
            return False

        num=self.getSingleResponse('AT+CPMS?', "OK", "+CPMS: ", divider='"MT",', index=1)
        if num is None: return num
        n,t,*_=num.split(',')
        return int(n),int(t)

    def readSMS(self, number):

        self._logger.debug("Read SMS: {}".format(number))

        # Reset last values
        self.last_SMS_Phonenumber = ""
        self.last_SMS_Message = ""
        self.last_SMS_date = ""

        # AT+CMGR = Read SMS
        status,params=self.sendATCmdWaitReturnResp("AT+CMGR={}".format(number),"OK")

        # return (ATResp.OK, lines)
        #print("Params len: {}".format(len(params)))
        #print("Params: \n{}".format(params))

        #Hm, beroende på om man har GSM eller UCS2 får man olika här? ibland innehåller params 2 (i GSM?)
        # och 3 om vi har UCS2? osäker om det stämmer dock

        # om så är fallet, så kan man bara sätta params när det är GSM, och params[1] när det är USC2
        stat,oa,alpha,scts1,scts2,tooa,fo,pid,dcs,sca,tosca,length=params[0][7:].split(',')


        #if status!=ATResp.OK or not params.startswith("+CMGR: "): return None

        # stat   : message status = "REC UNREAD", "REC READ", "STO UNSENT", "STO SENT", "ALL"
        # oa     : originating address
        # alpha  : string of "oa" or "da"
        # scts   : service center timestamp "YY/MM/DD,HH:MM:SS+ZZ"
        # tooa   : originating address type
        # fo     :
        # pid    : protocol ID
        # dcs    : data coding scheme
        # sca    :
        # tosca  :
        # length : length of the message body
        #stat,oa,alpha,scts1,scts2,tooa,fo,pid,dcs,sca,tosca,length=params[7:].split(',')

        scts=scts1+','+scts2
        tz=scts[-2:]
        scts=scts[:-1]+'00"'
        scts=datetime.strptime(scts, DATE_FMT)

        self.last_SMS_Phonenumber = oa[1:-1]
        self.last_SMS_Message = params[1]   #params[1] = GSM  params[2]=UCS2
        self.last_SMS_date = scts

        return params[1]    #params[1] = GSM  params[2]=UCS2

    def readAllSMS(self, status=SMSStatus.All):
        self._logger.debug("Read All SMS")
        if not self.setSMSMessageFormat(SMSMessageFormat.Text):
            self._logger.error("Failed to set SMS Message Format!")
            return None

        if not self.setSMSTextMode(SMSTextMode.Show):
            self._logger.error("Failed to set SMS Text Mode!")
            return None

        status,msgs=self.sendATCmdWaitReturnResp('AT+CMGL="{}"'.format(SMSStatus.toStat(status)), "OK")
        if status!=ATResp.OK or not msgs[0].startswith("+CMGL: ") or len(msgs)%2!=0: return None

        formatted=[]
        for n in range(0, len(msgs), 2):
            params,msg=msgs[n:n+2]
            if n==0: params=params[7:]
            loc,stat,oa,alpha,scts1,scts2,tooa,fo,pid,dcs,sca,tosca,length=params.split(',')
            scts=scts1+','+scts2
            tz=scts[-2:]
            scts=scts[:-1]+'00"'
            scts=datetime.strptime(scts, DATE_FMT)
            formatted.append((loc,SMSStatus.fromStat(stat),oa[1:-1],scts,msg))
        return formatted

    def deleteSMS(self, number):

        self._logger.debug("Delete SMS: {}".format(number))
        if not self.setSMSMessageFormat(SMSMessageFormat.Text):
            self._logger.error("Failed to set SMS Message Format!")
            return False
        status=self.sendATCmdWaitResp("AT+CMGD={:03d}".format(number), "OK")
        return status==ATResp.OK

    def sendSMS(self, phoneNumber, msg):
        # TODO: Check if we are sending in PDU mode or TEXT mode. Useing USC2 or GSM
        # ( USC2 need every AT string to be encoded in USC2)

        # Check what mode we are sending in..
          # Get mode.


        self._logger.debug("Send SMS: {} '{}'".format(phoneNumber, msg))

        if not self.setSMSMessageFormat(SMSMessageFormat.Text):
            self._logger.error("Failed to set SMS Message Format!")
            return False


        status=self.sendATCmdWaitResp('AT+CMGS="{}"'.format(phoneNumber), ">", addCR=True)
        if status!=ATResp.OK:
            self._logger.error("Failed to send CMGS command part 1! {}".format(status))
            return False

        cmgs=self.getSingleResponse(msg+"\r\n\x1a", "OK", "+", divider=":", timeout=40., interByteTimeout=1.2)

        return cmgs=="CMGS"

    def sendSMSinUnicode(self, phoneNumber, msg):
        self._logger.debug("Send SMS (in Unicode): {}  \"{}...\"".format(phoneNumber, msg[:5]))

        # TODO: Split up long sms and send multiple sms..
        #       split up sms can be 256 chars of length in UCS2 charset

        # Set to TEXT mode
        if not self.setSMSMessageFormat(SMSMessageFormat.Text):
            self._logger.error("Failed to set SMS Message Format!")
            return False

        self.setCharset("UCS2")

        nr = self.stringToUSC2(phoneNumber)

        MessageLength = len('\n'.join(replayMessage))

        if MessageLength > 255:

            #MSG_Chunks = [msg[i:i+255] for i in range(0, len(msg), 255)]

            # This will chunk up the message in chunks of maximum 254 chars
            # while not breaking in the middle of a food title
            MSG_Chunks = [""]
            index = 0
            for i in replayMessage:
                if (len(i) + len(MSG_Chunks[index]) + len("\n")) < 255:
                    MSG_Chunks[index] += i + "\n"
                else:
                    MSG_Chunks.append(i)
                    index = index + 1
            """
            # Cap the number of sms allowed
            if len(MSG_Chunks) > 5:
                self._logger.error("To many sms, MSG is too long!")
                self.setCharset("GSM")
                return False
            """
            # We are going to cap the number of sms allowed to send. So if user requests
            # more then 6 sms, we still sending those first 6 sms and add message to alert
            # user that maxium nr of sms is reached

            # TODO: Adding alert message to sms
            if len(MSG_Chunks) > 5:
                nrOfChunks = 5
                self._logger.error("To many sms, sending maxium 6 sms (requested: {})".format(len(MSG_Chunks)))
            else:
                nrOfChunks = len(MSG_Chunks)

            #for x in MSG_Chunks:
            for x in range(nrOfChunks):
                txt = self.stringToUSC2(MSG_Chunks[x])

                # Set phoneNumber
                status=self.sendATCmdWaitResp('AT+CMGS="{}"'.format(nr), ">", addCR=True)
                if status!=ATResp.OK:
                    self._logger.error("Failed to send CMGS command part 1! {}".format(status))
                    return False

                # Send Message
                cmgs=self.getSingleResponse(txt+"\r\n\x1a", "OK", "+", divider=":", timeout=11., interByteTimeout=1.2)
        else:
            txt = self.stringToUSC2('\n'.join(msg))

            # Set phoneNumber
            status=self.sendATCmdWaitResp('AT+CMGS="{}"'.format(nr), ">", addCR=True)
            if status!=ATResp.OK:
                self._logger.error("Failed to send CMGS command part 1! {}".format(status))
                return False

            # Send Message
            cmgs=self.getSingleResponse(txt+"\r\n\x1a", "OK", "+", divider=":", timeout=11., interByteTimeout=1.2)

        # Change back to GSM
        self.setCharset("GSM")

        return cmgs=="CMGS"

    def sendUSSD(self, ussd):
        self._logger.debug("Send USSD: {}".format(ussd))
        reply=self.getSingleResponse('AT+CUSD=1,"{}"'.format(ussd), "OK", "+CUSD: ", index=1, timeout=11., interByteTimeout=1.2)

        return reply

    def dummy_sendUSSD(self, ussd):
        self._logger.debug("Send USSD: {}".format(ussd))

        self.setCharset("UCS2")

        ussdUnicode = self.stringToUSC2(ussd)

        #reply=self.getSingleResponse('AT+CUSD=1,"{}"'.format(ussd), "OK", "+CUSD: ", index=1, timeout=11., interByteTimeout=1.2)
        reply=self.ekman_sendAT('AT+CUSD=1,"{}"'.format(ussdUnicode), "OK", timeout=11., interByteTimeout=1.2, addCR=True)

        # Change back to GSM
        self.setCharset("GSM")

        match = re.findall(r'(^.*?),(.*),(.*)', str(reply))

        #print(match[0][0]) # +CUSD: 0
        #print(match[0][1]) # Meddelandet
        #print(match[0][2]) # Cell Broadcast Data Coding Scheme in integer format   (default 0)

        #Convert USC2 numbers to readable string
        removeQuotes = re.findall(r'\"(.*?)\"',match[0][1])
        return binascii.unhexlify(removeQuotes[0]).decode('utf-16-be')


    def ekman_sendAT(self, cmd, response, timeout=.5, interByteTimeout=.1, addCR=False):

        self._logger.debug("Send AT Command: {}".format(cmd))
        self._serial.timeout=timeout
        self._serial.inter_byte_timeout=interByteTimeout

        bcmd=cmd.encode('utf-8')+b'\r'
        if addCR: bcmd+=b'\n'
        print(bcmd)

        self._serial.write(bcmd)
        self._serial.flush()

        lines=self._serial.readlines()
        #lines=[l.decode('utf-8').strip() for l in lines]
        lines=[l.strip() for l in lines]
        lines=[l for l in lines if len(l) and not l.isspace()]
        self._logger.debug("Lines: {}".format(lines))

        line=lines[-1]
        self._logger.debug("Line: {}".format(line))

        if not len(lines): return (ATResp.ErrorNoResponse, None)

        _response=lines.pop(-1) # Detta är första raden och ska vara "OK" (om valid write command)

        #self._logger.debug("Response: {}".format(response))
        #self._logger.debug("_response: {}".format(_response))

        if not len(_response) or _response.isspace(): return "ErrorNoResponse"

        return _response


if __name__=="__main__":

    try:
        s=SMS(PORT,BAUD,loglevel=logging.DEBUG)
        s.setup()

        #if not s.turnOn(): exit(1)     #disabling this so i can see with minicom whats happening..
        if not s.setEcho(0): exit(1)

        s.setCharset("GSM")

        response = s.dummy_sendUSSD("*101#")

        #print("Type: {}".format(type(response)))
        print("Response:\n{}".format(response.decode('utf-16-be')))

        exit(1)

    except Exception as e:
        s._logger.error("{} , exiting..".format(e))
        exit(1)


    # och här börjar jag lyssna för SMS att svara på
    s._logger.debug("Listening for incomming SMS...")
    while True:
        #reply = (s._serial.read(s._serial.inWaiting()))
        #decodedReply = reply.decode('utf-8')

        lines=s._serial.readlines()
        lines=[l.decode('utf-8').strip() for l in lines]
        lines=[l for l in lines if len(l) and not l.isspace()]



        if len(lines)>0:
            s._logger.debug("Lines: {}".format(lines))
            lastLine=lines[-1]
            s._logger.debug("Last Line: {}".format(lastLine))

            #if len(line) or not line.isspace():
                #self._logger.debug("Line: {}".format(line))

            #if decodedReply != "":
            #    print("UART:\n{}".format(reply))


            if "+CMTI:" in lastLine:
                s._logger.debug("SMS Received")

                #Using some fancy regular expression here to get sms index number
                try:
                    smsIndex = re.search(',(\d{1,3})',lastLine).group(1)
                except AttributeError as e:
                    smsIndex = ""
                    s._logger.debug("ERROR: {}".format(e))

                # Borde snygga till denna funktionen och något snyggt sätt att spara alla parametrar ifrån sms't...
                s.readSMS(smsIndex)

                try:
                    s._logger.debug("Writeing to SMS log file")
                    smsLogFile = open("smslog.txt", "a")
                    smsLogFile.write("{}: {} {}\n".format(s.last_SMS_date, s.last_SMS_Phonenumber, s.last_SMS_Message))
                    smsLogFile.close()
                except OSError as err:
                    print("OS error: {0}".format(err))
                except ValueError:
                    print("Could not convert data to an integer.")
                except:
                    print("Unexpected error:", sys.exc_info()[0])


                match = ""
                match = re.findall(r'(\d{1,3}).(\w{3,64})(\s\w{3,64})?(\s\w{3,64})?(\s\w{3,64})?(\s\w{3,64})?', s.last_SMS_Message)

                if match:

                    replayMessage = []
                    try:
                        for regexMatch in match:
                            #print(regexMatch[0]) # Number

                            #Create a list of list
                            ListOfMiddags = []
                            for middag in range(1,len(regexMatch)):
                                if regexMatch[middag] != '':
                                    ListOfMiddags.append(regexMatch[middag])

                            #Generate List
                            s._logger.debug("Requested Number of Middagar: {} from {}".format(int(regexMatch[0]),ListOfMiddags))

                            if not replayMessage:
                                replayMessage = generate(int(regexMatch[0]),ListOfMiddags)
                            else:
                                for x in generate(int(regexMatch[0]),ListOfMiddags):
                                    replayMessage.append(x)

                            if replayMessage:
                                s._logger.debug("Generated Middagar: {}".format(len(replayMessage)))
                            else:
                                s._logger.debug("Error: Couldn't generate reply message")
                                continue

                    except NameError as e:
                    	print("Error: {}".format(e))


                    if replayMessage:
                        if(s.sendSMSinUnicode(s.last_SMS_Phonenumber, replayMessage)):
                            s._logger.debug("Successfull sent SMS")
                        else:
                            s._logger.debug("No SMS sent")
                    else:
                        s._logger.debug("Empty replay message, not sending SMS")
                else:
                    s._logger.debug("Invalid requst: {}".format(s.last_SMS_Message))
