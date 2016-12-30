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
import random
from WModules import *
logger = logging.getLogger(__name__)


##      ## ####  ######  ##       ########    ###    ########
##  ##  ##  ##  ##    ## ##       ##         ## ##   ##     ##
##  ##  ##  ##  ##       ##       ##        ##   ##  ##     ##
##  ##  ##  ##  ##       ##       ######   ##     ## ########
##  ##  ##  ##  ##       ##       ##       ######### ##   ##
##  ##  ##  ##  ##    ## ##       ##       ##     ## ##    ##
 ###  ###  ####  ######  ######## ######## ##     ## ##     ##
# clear a part of the memory

class WiClear(object):
    """docstring for WiClear"""

    SPECIAL_CLEAR_COMMAND   = '00'   # if you change this here, also change it on the wisp!
    BYTES_PER_CLEAR         = 0x100  # if you change this here, also change it on the wisp!
    SPECIAL_CLEAR_TINY_COMMAND = '7f'   # if you change this here, also change it on the wisp!
    BYTES_PER_TINY_CLEAR    = 0x020  # if you change this here, also change it on the wisp!
    def __init__(self, send_util,  ID4hex, start_address, end_address):
        super(WiClear, self).__init__()
        self.ID             = ID4hex
        self.send_util      = send_util
        self.start_address  = int(start_address)
        self.end_address    = int(end_address)
        if ((end_address- start_address) % self.BYTES_PER_TINY_CLEAR) is not 0 :
            raise NotImplementedError("WiClear can only clear blocksizes of multiples of 0x"+i2h(self.BYTES_PER_TINY_CLEAR)+", your end_address- start_address = 0x" + i2h(end_address- start_address))
        logger.info('*'*50)
        logger.info("** ** ** Delete wispmem from " + i2h(start_address) +" to " + i2h(end_address)+ " ** ** **")
        logger.info('*'*50)

        clear_message = []
        # do as much use CLEARS as possible
        while(self.start_address+self.BYTES_PER_CLEAR<=self.end_address):
            addr = i2h(self.start_address)
            clear_message.append(self.SPECIAL_CLEAR_COMMAND + calcChecksum(addr) + addr)
            self.start_address += self.BYTES_PER_CLEAR
        # do some small clears at the end
        while(self.start_address+self.BYTES_PER_TINY_CLEAR<=self.end_address):
            addr = i2h(self.start_address)
            clear_message.append(self.SPECIAL_CLEAR_TINY_COMMAND + calcChecksum(addr) + addr)
            self.start_address += self.BYTES_PER_TINY_CLEAR

        self.clearMemMessenger = MultiMessenger(self.send_util, self.ID, messages= clear_message, readThis = clear_message, OCV = 1)

    def start(self,finished_callback):
        self.callback   = finished_callback
        self.clearMemMessenger.start(finished_callback = self.iAmFinished)

    def handleMessage(self,opspecs, epc):
        self.clearMemMessenger.handleMessage(opspecs,epc)

    def stop(self):
        self.send_util.stopTimerSuccesCheck()

    def iAmFinished(self, module = None, **parameters):
        self.stop()
        self.callback(module = self)


##      ## ####    ########  ########    ###    ########
##  ##  ##  ##     ##     ## ##         ## ##   ##     ##
##  ##  ##  ##     ##     ## ##        ##   ##  ##     ##
##  ##  ##  ##     ########  ######   ##     ## ##     ##
##  ##  ##  ##     ##   ##   ##       ######### ##     ##
##  ##  ##  ##     ##    ##  ##       ##     ## ##     ##
 ###  ###  ####    ##     ## ######## ##     ## ########
# clear a part of the memory

class WiRead(object):
    """docstring for WiRead"""

    SPECIAL_READ_COMMAND    = '1F'
    BYTES_PER_READ          = 0x20 # this is the max wisp can do

    def __init__(self, send_util,  ID4hex, start_address, end_address, message_size= None, metadata = None):
        super(WiRead, self).__init__()
        self.ID             = ID4hex
        self.send_util      = send_util
        self.start_address  = int(start_address)
        self.end_address    = int(end_address)
        self.metadata= metadata
        if(message_size):
            self.bytes_per_read = message_size
        elif((end_address- start_address)< self.BYTES_PER_READ):
            self.bytes_per_read = (end_address- start_address)
        else:
            self.bytes_per_read = self.BYTES_PER_READ

        if ((end_address- start_address) % self.bytes_per_read) is not 0 :
            raise NotImplementedError("WiRead can only read blocksizes of multiples of 0x"+i2h(self.bytes_per_read)+", your end_address- start_address = 0x" + i2h(end_address- start_address))
        logger.info('*'*50)
        logger.info("** ** ** Read wispmem from " + i2h(start_address) +" to " + i2h(end_address)+ " ** ** **")
        logger.info('*'*50)

        read_message = []
        startA = self.start_address
        while(startA<self.end_address):
            addr = i2h(startA)
            read_message.append(self.SPECIAL_READ_COMMAND + calcChecksum(addr) + addr)
            startA += self.bytes_per_read

        self.readMemMessenger = MultiMessenger(self.send_util, self.ID, messages= read_message, readAndReport_NrOfWords = self.bytes_per_read/2, OCV = 1)

    def start(self,finished_callback):
        self.callback   = finished_callback
        self.readMemMessenger.start(finished_callback = self.iAmFinished)

    def handleMessage(self,opspecs, epc):
        self.readMemMessenger.handleMessage(opspecs,epc)

    def stop(self):
        self.send_util.stopTimerSuccesCheck()

    def iAmFinished(self, readData, module = None, **parameters):
        self.stop()
        self.callback(readData, module = self)

##      ## ####    ########     ###    ##    ## ########   #######  ##     ##
##  ##  ##  ##     ##     ##   ## ##   ###   ## ##     ## ##     ## ###   ###
##  ##  ##  ##     ##     ##  ##   ##  ####  ## ##     ## ##     ## #### ####
##  ##  ##  ##     ########  ##     ## ## ## ## ##     ## ##     ## ## ### ##
##  ##  ##  ##     ##   ##   ######### ##  #### ##     ## ##     ## ##     ##
##  ##  ##  ##     ##    ##  ##     ## ##   ### ##     ## ##     ## ##     ##
 ###  ###  ####    ##     ## ##     ## ##    ## ########   #######  ##     ##

# refresh the random numbers
# this function is very specific and randomizes the random number table on the wisp
class WiRandom(object):
    """docstring for WiRandom"""

    def __init__(self, send_util,  ID4hex):
        super(WiRandom, self).__init__()
        self.ID             = ID4hex
        self.send_util      = send_util
        logger.info('*'*50)
        logger.info("** ** ** re-Random wisps random table: mem from " + i2h(0x1800) +" to " + i2h(0x1840)+ " ** ** **")
        logger.info('*'*50)

        random_message = []
        random_reply = []
        for addr in range(0x1800,0x1840,8):
            blockwrite = WiBlockWrite(wispID= self.ID, mem_address= addr, nr_of_words = 8, data= "{:032x}".format( random.randrange(16**(2*2*8))) )
            random_message.append(blockwrite.getMessageData())
            random_reply.append(blockwrite.getCheckdata())

        self.randomMessenger = MultiMessenger(self.send_util, self.ID, messages= random_message, readThis = random_reply, OCV = 1)

    def start(self,finished_callback):
        self.callback   = finished_callback
        self.randomMessenger.start(finished_callback = self.iAmFinished)

    def handleMessage(self,opspecs, epc):
        self.randomMessenger.handleMessage(opspecs,epc)

    def stop(self):
        self.send_util.stopTimerSuccesCheck()

    def iAmFinished(self, module = None, **parameters):
        self.stop()
        self.callback(module = self)


########  ##        #######   ######  ##    ##    ##      ## ########  #### ######## ########
##     ## ##       ##     ## ##    ## ##   ##     ##  ##  ## ##     ##  ##     ##    ##
##     ## ##       ##     ## ##       ##  ##      ##  ##  ## ##     ##  ##     ##    ##
########  ##       ##     ## ##       #####       ##  ##  ## ########   ##     ##    ######
##     ## ##       ##     ## ##       ##  ##      ##  ##  ## ##   ##    ##     ##    ##
##     ## ##       ##     ## ##    ## ##   ##     ##  ##  ## ##    ##   ##     ##    ##
########  ########  #######   ######  ##    ##     ###  ###  ##     ## ####    ##    ########

# The WiBlockWrite class represents one blockwrite message and contains info and functions
# to create the data for a blockwrite message suitable for the WISENT protocol
class WiBlockWrite(object):
    """docstring for WiBlockWrite"""
    def __init__(self, wispID, mem_address, nr_of_words, data, word_swap = True):
        super(WiBlockWrite, self).__init__()
        self.op_spec_id = None
        self.wispID = wispID
        self.address = mem_address
        self.nr_of_words = nr_of_words
        if(word_swap):
            self.data = self.swapHighLowBytes( data)
        else:
            self.data = data

        self.checksum = None

    # get the blockwrite data words
    def getMessageData(self):
        message = i2h(self.address) + self.data
        self.checksum = calcChecksum(message)
        message = i2h(self.nr_of_words,2) + self.checksum + message
        # Be carefull: resultposition will change the first 3 bits of the message later on!
        return message

    # get the expected result
    def getCheckdata(self):
        if(self.checksum is None):
            raise NameError("Message is not yet send")
        if(i2h(self.nr_of_words,2) == '00'):
            raise NameError("Message of zero words?"+ str(self.nr_of_words) )
        return i2h(self.nr_of_words,2) + self.checksum + i2h(self.address)

    def createOpspec(self):
        return OpSpecCreator.getBlockWrite(words=self.getMessageData())

    # In the wisp the 16 bit integers are stored as b7b6b5b4b3b2b1b0-b15b14b13b12b11b10b9b8
    # so the high and low bytes must be swapped somewhere, that is why we do it on the pc side instead of in the wisp
    def swapHighLowBytes(self, data): # while(not empty): swap first+second with third+fourth, jump four
        if(len(data)%4 ==0):
            ret = ""
            for i in range(len(data)/4):
                ret += data[i*4+2:i*4+4] + data[i*4:i*4+2]
            return ret
        else:
            raise NameError("data(%s) is not divisible by 4"%data)

    #
    @staticmethod
    def changeMessageID( message,ID): # change the first, second and third bits to encode the message ID, which is used for the resultposition in the wisp
        message = message.encode("hex")
        length = int("0x"+message[0:2],0) # get the lenght
        result_and_length = (ID<<5) + length # insert ID in the length part at position 7,6,5 and length stays in 4,3,2,10
        ret = i2h(result_and_length,2)+message[2:] # glue the message together
        return  ret.decode("hex")


######## ##     ## ######## ########     ###       ######## ##     ## ##    ##  ######  ######## ####  #######  ##    ##  ######
##        ##   ##     ##    ##     ##   ## ##      ##       ##     ## ###   ## ##    ##    ##     ##  ##     ## ###   ## ##    ##
##         ## ##      ##    ##     ##  ##   ##     ##       ##     ## ####  ## ##          ##     ##  ##     ## ####  ## ##
######      ###       ##    ########  ##     ##    ######   ##     ## ## ## ## ##          ##     ##  ##     ## ## ## ##  ######
##         ## ##      ##    ##   ##   #########    ##       ##     ## ##  #### ##          ##     ##  ##     ## ##  ####       ##
##        ##   ##     ##    ##    ##  ##     ##    ##       ##     ## ##   ### ##    ##    ##     ##  ##     ## ##   ### ##    ##
######## ##     ##    ##    ##     ## ##     ##    ##        #######  ##    ##  ######     ##    ####  #######  ##    ##  ######
#
#  _
# | |
# | |__    ___ __  __ __      __ _ __   __ _  _ __   _ __    ___  _ __
# | '_ \  / _ \\ \/ / \ \ /\ / /| '__| / _` || '_ \ | '_ \  / _ \| '__|
# | | | ||  __/ >  <   \ V  V / | |   | (_| || |_) || |_) ||  __/| |
# |_| |_| \___|/_/\_\   \_/\_/  |_|    \__,_|| .__/ | .__/  \___||_|
#                                            | |    | |
#                                            |_|    |_|


# modify the hexfile such that it has longer memory lines (max length is now a magic number 0x2FF)
# [Warning:] destroys the checksum, which is ignored for the Stork application
def wrapHexLines(lines):
    # logger.info("lines = {}".format(pprint.pformat(lines)))
    wrapped_lines = []
    current_line = lines[0]
    #init
    address =  int("0x" + current_line[3:7], 0)
    data = current_line[9:-3]
    length = len(data)/2 # length in bytes

    for i in range(1,len(lines)):
        current_line = lines[i]

        c_address = int("0x" + current_line[3:7], 0)
        c_data = current_line[9:-3]
        c_length = len(c_data)/2 # length in bytes

        #logger.info("a1+l = %i, a2 = %i"%(address + length,c_address))
        if(address + length == c_address and length + c_length <= 0x2FF):
            # combine the lines
            length += c_length
            data += c_data
        else:
            # add the previous line to wrapped lines
            if(length<0x100):
                wrapped_lines.append(":"+i2h(length,2)+i2h(address) +"00" + data + "FF\n" )
            else:
                wrapped_lines.append(":"+"FF"+i2h(address) +"00" + data + "FF\n" )
            address = c_address
            length = c_length
            data = c_data

    if(current_line != ":00000001FF\n"):
        raise NameError("You made a wrong hexfile EOF assumption (%s)"%current_line)

    total_words_to_send = 0
    for i in range(len(wrapped_lines)):
        total_words_to_send += ((len(wrapped_lines[i]) - 12)/4) # 12 characters are non word parts
        if((len(wrapped_lines[i]) - 12)%4 != 0):
            raise NameError("something went wrong with this line: "+ str(len(wrapped_lines[i]))+" "+wrapped_lines[i])
    logger.debug("total words to send: " + str(total_words_to_send))
    # finally add end of file:
    wrapped_lines.append(":00000001FF\n")
    # logger.info("wrapped lines = {}".format(pprint.pformat(wrapped_lines)))
    return wrapped_lines



######### get hexlines
def getRandomHexLines(size,address = 0x6400,bytes_per_line = 32):
    return [":{:02x}{:04x}00{:0{width}x}FF\n".format( # format like a hexline
        bytes_per_line,address+x,random.randrange(16**(2*bytes_per_line)),width = bytes_per_line*2 # add parameters
        )for x in range(0,size,bytes_per_line)] + [":00000001FF\n"] # do this for each line and add end-of-file-line at the end
