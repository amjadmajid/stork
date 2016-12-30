# -*- coding: utf-8 -*-
#  Copyright (c) 2016, [blinded for review]                                                         #
#  All rights reserved.                                                                             #
#                                                                                                   #
# Redistribution and use in source and binary forms, with or without                                #
# modification, are permitted provided that the following conditions are met:                       #
#     * Redistributions of source code must retain the above copyright                              #
#       notice, this list of conditions and the following disclaimer.                               #
#     * Redistributions in binary form must reproduce the above copyright                           #
#       notice, this list of conditions and the following disclaimer in the                         #
#       documentation and/or other materials provided with the distribution.                        #
#     * Neither the name of the <organization> nor the                                              #
#       names of its contributors may be used to endorse or promote products                        #
#       derived from this software without specific prior written permission.                       #
#                                                                                                   #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND                   #
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED                     #
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE                            #
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY                                #
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES                        #
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;                      #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND                       #
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT                        #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS                     #
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.                                      #

import logging
import pprint
import time
import random
from twisted.internet import reactor, defer
import sllurp.llrp as llrp
from sllurp.llrp_proto import DEFAULT_MODULATION, Modulation_DefaultTari

logger = logging.getLogger(__name__)

##     ## ########  ######   ######  ######## ##    ##  ######   ######## ########
###   ### ##       ##    ## ##    ## ##       ###   ## ##    ##  ##       ##     ##
#### #### ##       ##       ##       ##       ####  ## ##        ##       ##     ##
## ### ## ######    ######   ######  ######   ## ## ## ##   #### ######   ########
##     ## ##             ##       ## ##       ##  #### ##    ##  ##       ##   ##
##     ## ##       ##    ## ##    ## ##       ##   ### ##    ##  ##       ##    ##
##     ## ########  ######   ######  ######## ##    ##  ######   ######## ##     ##

# simple multifunctional messaging unit
# usage example:
# self.gotobios = Messenger(send_util, ID4hex, finished_callback, message= "ea4e",epctail ='ea4e', readThis = 'ea4e')
# self.gotobios = Messenger(send_util, ID4hex, finished_callback, message= "b105", epctail ='b105', readThis = 'b105')
# self.gotoboot = Messenger(send_util, ID4hex, finished_callback, message= "b007", epctailnot ='b105', readThis = 'b007')
class Messenger(object):
    """docstring for Messenger"""
    def __init__(self, send_util,  ID4hex, message =None, epctail = None, epctailnot = None, readThis = None, readAndReport_NrOfWords = None, OCV = 5):
        super(Messenger, self).__init__()
        self.ID         = ID4hex
        self.send_util  = send_util
        self.message    = message
        self.epctail    = epctail
        self.epctailnot = epctailnot
        self.readThis   = readThis
        self.readAndReport_NrOfWords = readAndReport_NrOfWords
        self.wispIsSeen = False
        self.OCV        = OCV
        self.time_start = time.time()

    def start(self,finished_callback):
        self.callback   = finished_callback
        self.time_start = time.time()
        self.nextRound()

    def nextRound(self):
        if(self.message):
            self.send_util.addOpspec(OpSpecCreator.getBlockWrite(words=self.message))

        if(self.readThis):
            self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,nr_of_words = len(self.readThis)/4))
        elif(self.readAndReport_NrOfWords):
            while(self.readAndReport_NrOfWords>16):
                self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,nr_of_words = 16))
                self.readAndReport_NrOfWords -=16
            self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,nr_of_words = self.readAndReport_NrOfWords))

        self.send_util.sendOpspecs(OCV=self.OCV,nack = self.timeout, time = .2)
        self.wispIsSeen = False

    def handleMessage(self,opspecs, epc):
        self.wispIsSeen = True
        logger.debug(self.ID +": OpSpecResult = \033[1;32m{}\033[1;0m".format(opspecs))

        if(self.epctail):
            if (epc[-1*len(self.epctail) : ] == self.epctail):
                self.iAmFinished()
                return

        if(self.epctailnot):
            if (epc[-1*len(self.epctailnot) : ] != self.epctailnot):
                self.iAmFinished()
                return

        if(self.readThis):
            opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get the read opspec
            if(len(opspecs) == 1):
                data = opspecs.values()[0]["ReadData"]
                if(data == self.readThis):
                    self.iAmFinished()
                    return

        if(self.readAndReport_NrOfWords):
            opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get the read opspec
            if(len(opspecs) == 1):
                self.iAmFinished(opspecs.values()[0])
            else:
                raise NotImplementedError("The messenger only sends one readopspec, how could you have received multiple?")

    def timeout(self):
        if(self.wispIsSeen):
            self.nextRound()
        else:
            self.send_util.setUpTimer(func = self.timeout, time = .2)

    def stop(self):
        self.send_util.stopTimerSuccesCheck()

    def iAmFinished(self, callback_parameter = None):
        self.stop()
        if(callback_parameter):
            self.callback(callback_parameter = callback_parameter, module = self, time = time.time() - self.time_start)
        else:
            self.callback(module = self, time = time.time() - self.time_start)

##     ## ##     ## ##       ######## ####         ##     ## ########  ######   ######  ######## ##    ##  ######   ######## ########
###   ### ##     ## ##          ##     ##          ###   ### ##       ##    ## ##    ## ##       ###   ## ##    ##  ##       ##     ##
#### #### ##     ## ##          ##     ##          #### #### ##       ##       ##       ##       ####  ## ##        ##       ##     ##
## ### ## ##     ## ##          ##     ##  ####### ## ### ## ######    ######   ######  ######   ## ## ## ##   #### ######   ########
##     ## ##     ## ##          ##     ##          ##     ## ##             ##       ## ##       ##  #### ##    ##  ##       ##   ##
##     ## ##     ## ##          ##     ##          ##     ## ##       ##    ## ##    ## ##       ##   ### ##    ##  ##       ##    ##
##     ##  #######  ########    ##    ####         ##     ## ########  ######   ######  ######## ##    ##  ######   ######## ##     ##

# simple multifunctional messaging unit
# usage example:
# self.clearMem = Messenger(send_util, ID4hex, finished_callback, message= ["00646400"], readThis = ['00646400'])
# self.clearMem = Messenger(send_util, ID4hex, finished_callback, message= ["1F646400", "1F846420"], readAndReport_NrOfWords = <<< 16 OR [16 16]>>>)

class MultiMessenger(object):
    """docstring for MultiMessenger"""
    OPSPECOFFSET = 10
    def __init__(self, send_util,  ID4hex, messages, readThis = None, readAndReport_NrOfWords = None, OCV = 5):
        super(MultiMessenger, self).__init__()
        self.ID         = ID4hex
        self.send_util  = send_util
        self.messages    = messages if isinstance(messages,list) else [messages] # making sure messages is a list
        if (not readThis) and (not readAndReport_NrOfWords):
            logger.info("not safe to do this!")
            # raise NotImplementedError("What is it that you want?")
        self.readThis   = readThis
        self.readAndReport_NrOfWords = readAndReport_NrOfWords
        # the next line creates the possibility for the user to give either one readsize or a list.
        if(readAndReport_NrOfWords):
            self.readAndReport_NrOfWords = readAndReport_NrOfWords if isinstance(readAndReport_NrOfWords,list) else [readAndReport_NrOfWords for _ in range(len(self.messages))]
            self.readAndReport_NrOfWords = {opsid+self.OPSPECOFFSET:self.readAndReport_NrOfWords[opsid] for opsid in  range(len(self.readAndReport_NrOfWords))}
        elif(readThis):
            self.readAndReport_NrOfWords = readAndReport_NrOfWords
            self.readThis = {opsid+self.OPSPECOFFSET:self.readThis[opsid] for opsid in  range(len(self.readThis))}
            logger.debug("Messages to send are: {}".format(pprint.pformat(self.messages)))

        self.messages = {opsid+self.OPSPECOFFSET:self.messages[opsid] for opsid in  range(len(self.messages))}
        self.wispIsSeen = False
        self.OCV        = OCV
        self.returnParameter = dict()

    def start(self,finished_callback):
        self.callback   = finished_callback
        self.nextRound()

    def nextRound(self):
        self.send_util.stopTimerSuccesCheck() # just to be sure

        counter = 0
        for key in self.messages.keys() :
            if(counter >= AccessSpecFactory.MaxNumOpSpecsPerAccessSpec):
                break

            if(self.readAndReport_NrOfWords):
                self.send_util.addOpspec(OpSpecCreator.getBlockWrite(words=self.messages[key]))
                self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,nr_of_words = self.readAndReport_NrOfWords[key], OpSpecID = key))
                counter+=2
            elif(self.readThis): # self.readThis
                self.send_util.addOpspec(OpSpecCreator.getBlockWrite(words=self.messages[key]))
                self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,nr_of_words = len(self.readThis[key])/4 ,OpSpecID = key))
                counter+=2
            else:
                self.send_util.addOpspec(OpSpecCreator.getBlockWrite(words=self.messages[key], OpSpecID = key))
                counter+=1


        self.send_util.sendOpspecs(OCV=self.OCV,nack = self.timeout, time = .2)
        self.wispIsSeen = False

    def handleMessage(self,opspecs, epc):
        self.wispIsSeen = True
        logger.debug(self.ID +": OpSpecResult = \033[1;32m{}\033[1;0m".format(opspecs))

        if(self.readThis):
            opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get the read opspecs
            m =0
            for ops in opspecs.values()[::-1]: # reversed order, because we are deleting
                opspecid = ops["OpSpecID"]
                data = ops["ReadData"]
                if(opspecid in self.readThis):
                    logger.debug("checking now : id-"+ str(opspecid) + " data-" + data + " against-" + self.readThis[opspecid])
                    # check if this data is the same for the readThis at the correct location
                    if(data == self.readThis[opspecid].lower()):
                        del self.readThis[opspecid]
                        del self.messages[opspecid]


        elif(self.readAndReport_NrOfWords):
            opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get the read opspec
            for ops in opspecs.values()[::-1]:
                opspecid = ops["OpSpecID"]
                data = ops["ReadData"]
                if(opspecid in self.readAndReport_NrOfWords):
                    if(ops["Result"] ==0):
                        self.returnParameter[opspecid] = data
                        del self.readAndReport_NrOfWords[opspecid]
                        del self.messages[opspecid]
        else:
            opspecs = {x:opspecs[x] for x in opspecs if opspecs[x]["Result"] == 0 } # get the opspec
            for ops in opspecs.values()[::-1]:
                opspecid = ops["OpSpecID"]
                if(opspecid in self.messages):
                    del self.messages[opspecid]


        if(len(self.messages)):
            self.nextRound()
            logger.info("msgs to go: %i"%len(self.messages) )
        else:
            self.iAmFinished([self.returnParameter[x] for x in sorted(self.returnParameter)]) # return the opspecs in order of opspecid = input order

    def timeout(self):
        if(self.wispIsSeen):
            self.nextRound()
        else:
            self.send_util.setUpTimer(func = self.timeout, time = .2)

    def stop(self):
        self.send_util.stopTimerSuccesCheck()

    def iAmFinished(self, callback_parameter, module = None):
        self.stop()
        if(len(callback_parameter)):
            self.callback(callback_parameter, module = self)
        else:
            self.callback(module = self)



 ######  ######## ##    ## ########     ##     ## ######## #### ##
##    ## ##       ###   ## ##     ##    ##     ##    ##     ##  ##
##       ##       ####  ## ##     ##    ##     ##    ##     ##  ##
 ######  ######   ## ## ## ##     ##    ##     ##    ##     ##  ##
      ## ##       ##  #### ##     ##    ##     ##    ##     ##  ##
##    ## ##       ##   ### ##     ##    ##     ##    ##     ##  ##
 ######  ######## ##    ## ########      #######     ##    #### ########

# The AccessSpecFactory class provides function to collect Opspec messages and
# attach them into AccessSpec parameters, according to the Wisp it is attached to
# Also adds the target info created with use of the wisp ID
class AccessSpecFactory(object):
    """docstring for AccessSpecFactory"""

    MaxNumOpSpecsPerAccessSpec = 8
    latest_access_spec_id = 0

    def __init__(self, wispID, accessSpecID, fac):
        super(AccessSpecFactory, self).__init__()
        self.message_list = []
        self.as_id = accessSpecID
        self.fac = fac
        self.opspecs = []
        self.target = {
            "MB" : 1, # EPC = 1, userMem = 3
            "M": 1,
            "Pointer" : 32,
            "MaskBitCount": 16,
            "TagMask": "\xFF\xFF",#"\x00\xFF\xFF\x00",#\xFF\xFF\xFF\xFF",
            "DataBitCount": 16,#16*2,
            "TagData": wispID.decode("hex"),#"\xF1\x65\x34\x00",  # \xF1\x65\x34\x00\x00\x34\xB0\x07" # tag 269 needs 34000269
        }
        self.successCheck = None

    @staticmethod
    def nextASID():
        AccessSpecFactory.latest_access_spec_id += 1
        if(AccessSpecFactory.latest_access_spec_id > 0xFFFF):
            AccessSpecFactory.latest_access_spec_id = 1
        return AccessSpecFactory.latest_access_spec_id

    # send the opspecs wrapped in an accessspec
    def sendOpspecs(self, OCV = 1, nack = None, time = 0.3):
        nr_of_opspecs = len(self.opspecs)
        logger.debug("opspecs to send: {}".format(pprint.pformat(self.opspecs)))

        # give all distinct Opspec IDs:
        for i in range(nr_of_opspecs):
            if(self.opspecs[i]["OpSpecID"] == 0):
                self.opspecs[i]["OpSpecID"] = i+1

        # do the command only once or OCV times
        self.fac.nextAccessSpec(opSpecs=self.opspecs, accessSpec = {"ID":self.as_id,
            "StopParam": {"AccessSpecStopTriggerType": 1, "OperationCountValue": OCV,},"target": self.target,})

        logger.debug("sending {} opspecs".format(len(self.opspecs)))

        # make sure that you have some result after a while otherwise do nack
        if(nack):
            self.setUpTimer(func=nack,time = time)
        self.opspecs = []

    # cancel the timer that runs in the background, the timer that checks if there is a result soon enough
    def stopTimerSuccesCheck(self):
        if(self.successCheck):
            try:
                self.successCheck.cancel()
            except Exception as e:
                logger.debug("stopTimerSuccesCheck: tried to remove an already called event")

            self.successCheck = None

    def setUpTimer(self, func, time):
        self.successCheck = reactor.callLater(time, func)

    def addOpspec(self,opspec):
        if(len(self.opspecs) <= self.MaxNumOpSpecsPerAccessSpec):
            self.opspecs.append(opspec)
        else:
            raise NotImplementedError("You can send a maximum of 8 opspecs per time, current opspecs: {}".format(pprint.pformat(self.opspecs)))

    def deleteMyAccessSpec(self):
        self.stopTimerSuccesCheck()
        self.fac.deleteAccessSpec(self.as_id)

    def isEmpty(self):
        return len(self.opspecs) == 0

 #######  ########   ######  ########  ########  ######   ######  ########  ########    ###    ########  #######  ########
##     ## ##     ## ##    ## ##     ## ##       ##    ## ##    ## ##     ## ##         ## ##      ##    ##     ## ##     ##
##     ## ##     ## ##       ##     ## ##       ##       ##       ##     ## ##        ##   ##     ##    ##     ## ##     ##
##     ## ########   ######  ########  ######   ##       ##       ########  ######   ##     ##    ##    ##     ## ########
##     ## ##              ## ##        ##       ##       ##       ##   ##   ##       #########    ##    ##     ## ##   ##
##     ## ##        ##    ## ##        ##       ##    ## ##    ## ##    ##  ##       ##     ##    ##    ##     ## ##    ##
 #######  ##         ######  ##        ########  ######   ######  ##     ## ######## ##     ##    ##     #######  ##     ##

class OpSpecCreator(object):
    """docstring for OpSpecCreator"""
    def __init__(self):
        super(OpSpecCreator, self).__init__()

    # create a write opspec
    @staticmethod
    def getWrite(word,address=0,OpSpecID =0):
        if(len(word) ==4):
            return {
                "OpSpecID": OpSpecID,
                "MB": 3,
                "WordPtr": address,
                "AccessPassword": 0,
                "WriteDataWordCount": len(word)/4,
                "WriteData": word.decode("hex"),
                }
        else:
            raise NameError("len(word) != 4")

    # create a blockwrite opspec
    @staticmethod
    def getBlockWrite(words, OpSpecID =0):
        if(len(words)%4 ==0):
            return {
                "OpSpecID": OpSpecID,
                "MB": 3,
                "WordPtr": 0,
                "AccessPassword": 0,
                "WriteDataWordCount": len(words)/4,
                "WriteData": words.decode("hex"),
                }
        else:
            raise NameError("len(words) is not divisible by 4: words = {}".format(words))

    # create a read opspec
    @staticmethod
    def getRead(mb,nr_of_words,address = 0, OpSpecID = 0):
        return {
            "OpSpecID": OpSpecID,
            "MB": mb, # EPC = 1 user memory = 3
            "WordPtr": address,
            "AccessPassword": 0,
            "WordCount": nr_of_words,
            }

######## ##     ## ######## ########     ###       ######## ##     ## ##    ##  ######  ######## ####  #######  ##    ##  ######
##        ##   ##     ##    ##     ##   ## ##      ##       ##     ## ###   ## ##    ##    ##     ##  ##     ## ###   ## ##    ##
##         ## ##      ##    ##     ##  ##   ##     ##       ##     ## ####  ## ##          ##     ##  ##     ## ####  ## ##
######      ###       ##    ########  ##     ##    ######   ##     ## ## ## ## ##          ##     ##  ##     ## ## ## ##  ######
##         ## ##      ##    ##   ##   #########    ##       ##     ## ##  #### ##          ##     ##  ##     ## ##  ####       ##
##        ##   ##     ##    ##    ##  ##     ##    ##       ##     ## ##   ### ##    ##    ##     ##  ##     ## ##   ### ##    ##
######## ##     ##    ##    ##     ## ##     ##    ##        #######  ##    ##  ######     ##    ####  #######  ##    ##  ######

#  _____                                   _
# /  __ \                                 | |
# | /  \/  ___   _ __  __   __  ___  _ __ | |_   ___  _ __  ___
# | |     / _ \ | '_ \ \ \ / / / _ \| '__|| __| / _ \| '__|/ __|
# | \__/\| (_) || | | | \ V / |  __/| |   | |_ |  __/| |   \__ \
#  \____/ \___/ |_| |_|  \_/   \___||_|    \__| \___||_|   |___/


#convert hex to int
def h2i(hexadecimal):
    if(hexadecimal[:2] == "0x"):
        return int(hexadecimal,0)
    else:
        return int("0x"+hexadecimal,0)

#convert int to hex (length string is 4)
def i2h(integer,length = 4):
    if(integer/pow(16,length)>0xF):
        raise NameError("integer is too large! ["+ str(integer) +"]")
    if(length == 4):
        return "{:04x}".format(integer)
    elif(length == 2):
        return "{:02x}".format(integer)
    else:
        raise NotImplementedError()

# calculate the cyclic checksum of data
def calcChecksum(message):
    checksum = 0
    for i in range(0, len(message),2):
        checksum += h2i(message[i:i+2])
    return i2h(checksum % 256,2)


 #  _         ____     _____         _           _   _
 # | |       / __ \   / ____|       (_)         (_) | |
 # | |      | |  | | | |  __         _   _ __    _  | |_
 # | |      | |  | | | | |_ |       | | | '_ \  | | | __|
 # | |____  | |__| | | |__| |       | | | | | | | | | |_
 # |______|  \____/   \_____|       |_| |_| |_| |_|  \__|



# here the logging format is set
def init_logging (args):
    logLevel  = (args.debug and logging.DEBUG or logging.INFO)
    logFormat = "<%(asctime)s> %(message)s"
    formatter = logging.Formatter(logFormat)

    stderr = logging.StreamHandler()
    stderr.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logLevel)
    root.handlers = [stderr,]

    if args.logfile:
        fHandler = logging.FileHandler(args.logfile)
        fHandler.setFormatter(formatter)
        root.addHandler(fHandler)


    logger.log(logLevel, "log level: {}".format(logging.getLevelName(logLevel)))
    showFlag()

def showFlag():
    sside = 36
    s6 ="\033[1;44m  * "*6+' \033[1;0m'+ '\033[1;31m'+'█'*sside+'\033[1;0m'+'\n  '
    s5 = '\033[1;44m  '+ "\033[1;44m  * "*5+'   \033[1;0m'+ '█'*sside+'\n  '
    logger.info('\n\n  '+ (s6+s5)*4+s6+ ( '█'*(sside+25)+ '\n  '+ '\033[1;31m'+'█'*(sside+25)+ '\033[1;0m'+'\n  ')*4)

 #  ______                  _                                _           _   _
 # |  ____|                | |                              (_)         (_) | |
 # | |__      __ _    ___  | |_    ___    _ __   _   _       _   _ __    _  | |_
 # |  __|    / _` |  / __| | __|  / _ \  | '__| | | | |     | | | '_ \  | | | __|
 # | |      | (_| | | (__  | |_  | (_) | | |    | |_| |     | | | | | | | | | |_
 # |_|       \__,_|  \___|  \__|  \___/  |_|     \__, |     |_| |_| |_| |_|  \__|
 #                                                __/ |
 #                                               |___/

# function to initialize the Reader (Rospec)
def initFactory(args, inventoryFinished, tagReportCallback, finish):
    # Called when all connections have terminated normally.
    onFinish = defer.Deferred()
    onFinish.addCallback(finish)

    # special case default Tari values
    if args.modulation in Modulation_DefaultTari:
        t_suggested = Modulation_DefaultTari[args.modulation]
        if args.tari:
            logger.warn("recommended Tari for {} is {}".format(args.modulation,
                        t_suggested))
        else:
            args.tari = t_suggested
            logger.info("selected recommended Tari of {} for {}".format(args.tari,
                        args.modulation))

    factory = llrp.LLRPClientFactory(onFinish=onFinish,
            disconnect_when_done=True,
            modulation=args.modulation,
            tari=args.tari,
            session=args.session,
            tag_population=args.population,
            start_inventory=True,
            tx_power=args.tx_power,
            report_every_n_tags=args.every_n,
            inventory_round_time = args.inventory_round_time,
            tag_content_selector={
                "EnableROSpecID": False,
                "EnableSpecIndex": True,
                "EnableInventoryParameterSpecID": False,
                "EnableAntennaID": True,
                "EnableChannelIndex": False,
                "EnablePeakRRSI": True,
                "EnableFirstSeenTimestamp": False,
                "EnableLastSeenTimestamp": True,
                "EnableTagSeenCount": True,
                "EnableAccessSpecID": True
            })

    # The "main loop" for tags. (set the callback to tagReportCallback)
    factory.addTagReportCallback(tagReportCallback)

    # Start transfer session. (set the callback to inventoryFinished)
    factory.addStateCallback(llrp.LLRPClient.STATE_INVENTORYING, inventoryFinished)

    return factory

 #  _____                          _                            _                    _
 # |  __ \                        | |                          | |                  | |
 # | |__) |   ___    __ _    ___  | |_    ___    _ __     ___  | |_    __ _   _ __  | |_
 # |  _  /   / _ \  / _` |  / __| | __|  / _ \  | '__|   / __| | __|  / _` | | '__| | __|
 # | | \ \  |  __/ | (_| | | (__  | |_  | (_) | | |      \__ \ | |_  | (_| | | |    | |_
 # |_|  \_\  \___|  \__,_|  \___|  \__|  \___/  |_|      |___/  \__|  \__,_| |_|     \__|


# All initializations are done, so fire the engine!!
def startReactor (factory, args):

    # Add nack_counter to reader connect attempt.
    for host in args.host:
        reactor.connectTCP(host, args.port, factory, timeout=15)

    # Catch Ctrl-C and to politely shut down system.
    reactor.addSystemEventTrigger("before", "shutdown", factory.politeShutdown)

    # Start the sllurp reactor.
    reactor.run()

 #                              _____                                             _           __                   _   _
 #     /\                      |  __ \                                           | |         / _|                 | | | |
 #    /  \     _ __    __ _    | |__) |   __ _   _ __   ___    ___   _ __      __| |   ___  | |_    __ _   _   _  | | | |_   ___
 #   / /\ \   | '__|  / _` |   |  ___/   / _` | | '__| / __|  / _ \ | '__|    / _` |  / _ \ |  _|  / _` | | | | | | | | __| / __|
 #  / ____ \  | |    | (_| |   | |      | (_| | | |    \__ \ |  __/ | |      | (_| | |  __/ | |   | (_| | | |_| | | | | |_  \__ \
 # /_/    \_\ |_|     \__, |   |_|       \__,_| |_|    |___/  \___| |_|       \__,_|  \___| |_|    \__,_|  \__,_| |_|  \__| |___/
 #                     __/ |
 #                    |___/

# handle user start input
def parse_args (parser):

    parser.add_argument("host", help="IP address of RFID reader", nargs="*")
    parser.add_argument("-p", "--port", default=llrp.LLRP_PORT, type=int, help="port to connect to (default {})".format(llrp.LLRP_PORT))
    parser.add_argument("-t", "--time", default=10, type=float, help="number of seconds for which to inventory (default 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="show debugging output")
    parser.add_argument("-n", "--report-every-n-tags", default=5, type=int, dest="every_n", metavar="N", help="issue a TagReport every N tags")
    parser.add_argument("-X", "--tx-power", default=0, type=int, dest="tx_power", help="Transmit power (default 0=max power)")
    parser.add_argument("-M", "--modulation", default="WISP5", help="modulation (default WISP5)")
    parser.add_argument("-T", "--tari", default=0, type=int, help="Tari value (default 0=auto)")
    parser.add_argument("-s", "--session", default=2, type=int, help="Gen2 session (default 2)")
    parser.add_argument("-P", "--tag-population", default=32, type=int, dest="population", help="Tag Population value (default 32)")
    parser.add_argument("-I", "--inventory-round-time", default=None, type=int, dest="inventory_round_time", help="Time of an inventory round")
    parser.add_argument("-l", "--logfile")

    # parser.add_argument("-f", "--filenames", nargs="+",type=str, help="the Intel Hexs file to transfer")
    # parser.add_argument("-m", "--throttleindex", default=None, type=int, help="start size of message payload in words according to set T")
    # parser.add_argument("-w", "--wisp_targets", nargs="+",default ="all", type=str, help="the wisps that needs to be programmed")
    # parser.add_argument("-c", "--constant_throttle",default = None, type=int, help="set the throttle constant")
    # parser.add_argument("-b", "--memline_parallel",default = 4, type=int, help="set the number of parallel memlines i.e. number of blockwrites per opspec")
    return parser.parse_args()
