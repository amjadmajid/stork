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
from WWidgets import StorkWidget
from WModules import *
from WControlModules import WiBlockWrite, wrapHexLines
logger = logging.getLogger(__name__)

 ######  ########  #######  ########  ##    ## 
##    ##    ##    ##     ## ##     ## ##   ##  
##          ##    ##     ## ##     ## ##  ##   
 ######     ##    ##     ## ########  #####    
      ##    ##    ##     ## ##   ##   ##  ##   
##    ##    ##    ##     ## ##    ##  ##   ##  
 ######     ##     #######  ##     ## ##    ## 

# this module is stork as simple as possible,
# assumptions are:
#   the reactor is running

# ## Stork has been tested and reportedly working on the following readers:                        #
#    - Impinj Speedway R420 (FCC)                                                                   #
#    - Impinj Speedway R1000                                                                        #

# ## Example usage:
# from WStork import Stork
# from WModules import AccessSpecFactory
# Somewhere in "main()":
        # stork = Stork( send_util = AccessSpecFactory(wispID = args.wisp_targets[0][2:6], accessSpecID = 1, fac = fac),
        #     ID4hex= args.wisp_targets[0][2:6],
        #     hexlines=open(args.filenames[0], "r").readlines(),
        #     blockWritesPerAccessSpec = args.memline_parallel,
        #     constant_throttle = args.constant_throttle)
# Somewhere in "InventoryFinished()":
        # stork.start(finished_callback = storkCallback)

class Stork(object):
    """docstring for Stork"""

    T                  = [2,3,4,5,6,8,12,16,20,24,28,30] # Set of allowed values for S_p after throttle.
    TstartIndex        = 11         # start at T[10] = 30 = max
    TstartValue        = T[TstartIndex]
    ThrottleUpByXMSGs  = 2      # if receiving this amount of succesfull
                                # messages in a single handshake, throttle up
    TIMEOUT            = 0.5    # seconds


    def __init__(self,send_util,  ID4hex, hexlines,blockWritesPerAccessSpec = 4, constant_throttle = False, TstartValue = None ):
        super(Stork, self).__init__()
        self.ID         = ID4hex
        self.lines      = wrapHexLines(hexlines)

        self.lines      = self.lines[:-1]
        self.blockWritesPerAccessSpec = blockWritesPerAccessSpec

        self.stork_widget = StorkWidget(self, destroy_callback = self.iAmCanceled)

        # Throttle variables
        self.constant_throttle  = constant_throttle
        self.throttle_index     = None if constant_throttle else self.TstartIndex # start the throttle (messagepayload) at this T[index]
        self.message_payload    = constant_throttle if constant_throttle else self.TstartValue
        if(TstartValue):
            self.message_payload = TstartValue

        # Messages variables
        self.send_util                  = send_util # class that collect opspec parameters and sends the opspec in an accessspec to the reader
        self.mem_lines                  = []        # list of memline class objects
        self.lines_distributed          = 0         # number of hexlines that are already in the system en being processed
        self.check_data                 = dict()    # if a result is received from the wisp, then it will be searched in this dictionary and the corresponding ack will be executed
        # dict is of the form: {"expectedresult": function to execute when expected result is found,
        #                       "expectedresult2": func, etc}
        self.nr_of_handshakes           = 0         # count the number of times the wisp is seen, reset after each new accesspec

        logger.info(self.ID +": *****************************************")
        logger.info(self.ID +": * Wisp to program: %20s *"% self.ID)
        logger.info(self.ID +": * Words to send:       %4i in %2i lines *" % (self.getNrOfWords(), len(self.lines) ))
        logger.info(self.ID +": *****************************************")

    def getNrOfWords(self):
        return sum([(len(x) - 12)/4 for x in self.lines])

    def addCheck(self,data, ackfunc):
        logger.debug(self.ID +": check added: " + data)
        self.check_data[data] = ackfunc

    def start(self,  finished_callback, destroy_windows_after_Xsec_when_finished = None):
        self.callback = finished_callback
        self.destroy_windows_after_Xsec_when_finished = destroy_windows_after_Xsec_when_finished
        self.start_time = time.time()
        # activate some memory lines and make them prepare the first messages
        for i in range(self.blockWritesPerAccessSpec):
            newML = self.addNewMemline()
            logger.debug("Adding memline")

        self.nextRound()

        logger.info(self.ID + ": First reprogramming messages send --- Stork time elapsed: %.3f secs"% (time.time() - self.start_time))

    #### start a new round of stork
    def nextRound(self):
        #check all memlines: replace finished ones with new ones (clean up the trash and add new lines if there is space)
        for index in range(len(self.mem_lines)-1,-1,-1):
            if(self.mem_lines[index].finished()):
                del self.mem_lines[index]
                self.addNewMemline()
                if(len(self.mem_lines)<5):
                    self.blockWritesPerAccessSpec = 4

        # clear any old checks
        self.check_data.clear()

        # Prepare a blockwrite opspec for every memline
        BWcounter = 0
        for ml in self.mem_lines:
            self.sendMemLine(ml)
            BWcounter+=1
            if(BWcounter == self.blockWritesPerAccessSpec):
                break

        # If there were messages to send, send them
        if( not self.send_util.isEmpty()):
            # do a special tweak for method 2
            if(self.blockWritesPerAccessSpec >4):
                self.opSpecChangesForMethod2()
            self.send_util.sendOpspecs(OCV = 1, nack = self.timeout, time = self.TIMEOUT)
            self.nr_of_handshakes = 0
        else:
            self.iAmFinished()

    def opSpecChangesForMethod2(self):
        # do special stuff for the stork method 2 (BW*7+R)
        # insert message ID = result position into the messages and append them to the opspec list
        for i in range(0,len(self.send_util.opspecs)): # this can start with 1, because default messageID is zero (Warning: don't confuse messageID with OpSpecID!)
            self.send_util.opspecs[i]["WriteData"] = WiBlockWrite.changeMessageID(self.send_util.opspecs[i]["WriteData"],i)
        # add one read opspec at the end
        self.send_util.opspecs.append(OpSpecCreator.getRead(mb = 3,address = 0,nr_of_words = 2*len(self.send_util.opspecs)+1))

    def addNewMemline(self):
        if(self.lines_distributed >= len(self.lines)):
            return None
        newML = MemLine(self.ID, self.lines_distributed, self.lines[self.lines_distributed], stork_widget= self.stork_widget)
        self.mem_lines.append(newML)
        self.lines_distributed += 1
        return newML

    def sendMemLine(self, memline):
        self.send_util.addOpspec(memline.getNextStorkMessage(self.message_payload)) # in case of a failure this will prepare a previous message again, so the name "next" is ambigues
        if(self.blockWritesPerAccessSpec <5):
            self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,address = 0,nr_of_words = 3))
        self.addCheck(data = memline.getCheckdata(), ackfunc = memline.ack )


    def check(self, data):
        if data in self.check_data:
            self.send_util.stopTimerSuccesCheck() # stop the resend mechanism
            self.check_data[data]() # execute callback (=ack)
            logger.debug(data +" =  ack")
            del self.check_data[data]
            return True
        else:
            logger.debug(data +" =  NOT ack")
            return False

    def throttle(self, more):
        if(not self.constant_throttle):
            if(more):
                if(self.throttle_index < len(self.T)-1):
                    self.throttle_index = min (self.throttle_index+1,len(self.T)-1) #increase speed but don't go above max
                    self.message_payload = self.T[self.throttle_index]
                    logger.debug(self.ID +": Throttle up to %i"%self.message_payload)
                else:
                    if(self.blockWritesPerAccessSpec == 4 and not self.lines_distributed >= len(self.lines)):
                        self.blockWritesPerAccessSpec = 7
                        for i in range(3):
                            newML = self.addNewMemline()

            else:
                #throttle down if possible
                if(self.blockWritesPerAccessSpec == 7):
                    self.blockWritesPerAccessSpec = 4 # go to the safe method
                    return
                if(self.throttle_index>0):
                    self.throttle_index = max (self.throttle_index-2,0) #decrease speed but don't go below 0
                    self.message_payload = self.T[self.throttle_index]
                    logger.debug(self.ID +": Throttle down to %i "%self.message_payload)

    def handleMessage(self,opspecs, epc):
        logger.info(self.ID +": OpSpecResult = \033[1;32m{}\033[1;0m".format(opspecs))
        self.nr_of_handshakes += 1
        wisp_alive = all(opspecs[x]["Result"] == 0 for x in opspecs)

        opspecs = {x:opspecs[x] for x in opspecs if (opspecs[x]["Result"] == 0) } # get all successive opspecresults
        opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get all read opspecs

        nr_of_acks = 0 # keep hold of the number of acks
        if(not len(opspecs)):
            logger.debug("OpSpecs have no successive read data at all")
            if(self.check(epc[12:20])): # if wisp died DURING read OpSpec, then it wakes up with the result in the epc, because it was stored DURING the last BLOCKWRITE
                nr_of_acks += 1
                logger.info("EPC did encode a good result")
        else:
            logger.debug(self.ID +": ReadOpSpecResult = \033[1;32m{}\033[1;0m".format(opspecs))

            ###### This is where we extract the read result and check if it is the expected ack
            for ops in opspecs.values():
                data = ops["ReadData"]
                # logger.debug("readdata =" +  data)
                for d in range(0,len(data)/8):
                    if(self.check(data[d*8:d*8+8])):
                        nr_of_acks += 1

        if(nr_of_acks>0): # if there was at least one ack, then we can move on
            self.send_util.stopTimerSuccesCheck()
            if (wisp_alive or nr_of_acks>=self.ThrottleUpByXMSGs): # throttle up if wisp is full of energy
                self.throttle(more = True)

            self.nextRound()
        else:
            logger.debug(self.ID +": useless round: you should retry now")

        # flush textwidget text to screen
        self.stork_widget.root.update_idletasks()

    def timeout(self):
        if(self.nr_of_handshakes==0):
            logger.info("\033[1;31mWISENT TIMEOUT\033[1;0m wisp not seen")
            self.send_util.setUpTimer(func = self.timeout, time= .2)
        else:
            logger.debug("\033[1;31mWISENT TIMEOUT\033[1;0m wisp died")
            self.throttle(more = False)
            self.nextRound()


    def iAmFinished(self):

        self.send_util.stopTimerSuccesCheck()
        # Do a last redundant check:
        if(len(self.check_data)):
            logger.info(self.ID +": memlines = {}".format(self.mem_lines))
            logger.info(self.ID +": checkdata is not empty: {}".format(self.check_data))
            #raise NameError("checkdata is not empty: {}".format(self.check_data))

        logger.info(self.ID + ": stork end of file reached.          --- Stork time elapsed: %.3f secs\n"% (time.time() - self.start_time))
        # flush textwidget text to screen
        self.stork_widget.root.update_idletasks()
        if(self.destroy_windows_after_Xsec_when_finished):
            reactor.callLater(self.destroy_windows_after_Xsec_when_finished, self.stork_widget.destroy )
        # TODO: do some more stuff before returning?
        self.callback(module = self, success =True, log= 'Log stork: (BWperAS,payload)= (\t{},\t{}), time = \t{:.3f}, '.format(
                        self.blockWritesPerAccessSpec,
                        self.constant_throttle if self.constant_throttle else 'throttle',
                        time.time() - self.start_time))

    def stop(self):
        self.send_util.deleteMyAccessSpec()
        self.stork_widget.destroy()

    def iAmCanceled(self):
        self.send_util.deleteMyAccessSpec()
        if(len(self.check_data)):
            logger.info("!!Stork aborted by YOU!!")
            self.callback(module = self, success=False)

##     ## ######## ##     ##    ##       #### ##    ## ########
###   ### ##       ###   ###    ##        ##  ###   ## ##
#### #### ##       #### ####    ##        ##  ####  ## ##
## ### ## ######   ## ### ##    ##        ##  ## ## ## ######
##     ## ##       ##     ##    ##        ##  ##  #### ##
##     ## ##       ##     ##    ##        ##  ##   ### ##
##     ## ######## ##     ##    ######## #### ##    ## ########

# this object takes one memory line from the hexfile and extracts the data and prepares blockwrites from a memory line
class MemLine(object):
    """docstring for MemLine"""

    def __init__(self, wispID, line_number,line, stork_widget):
        super(MemLine, self).__init__()
        self.wispID = wispID
        self.line_number = line_number
        self.address = int("0x" + line[3:7], 0)
        self.mem = line[9:-3]
        self.blockwrite = None
        self.stork_widget = stork_widget

    def finished(self):
        return len(self.mem) == 0

    def ack(self):
        self.mem = self.mem[4*self.payload_size:]
        self.address += + 2*self.payload_size
        self.stork_widget.ack(self.line_number,self.payload_size) # do plot

    def getNextStorkMessage(self, message_payload):
        self.payload_size = min(message_payload, len(self.mem)/4)
        self.stork_widget.setTry(self.line_number, self.payload_size) # do plot
        if(self.payload_size == 0):
            raise NameError("payload of zero? [" + self.mem + "]")
        self.blockwrite = WiBlockWrite(wispID=self.wispID,
                                    mem_address=self.address,
                                    nr_of_words=self.payload_size,
                                    data=self.mem[:4*self.payload_size])

        return self.blockwrite.createOpspec()

    def getCheckdata(self):
        return self.blockwrite.getCheckdata()
