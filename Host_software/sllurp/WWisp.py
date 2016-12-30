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

import time
import logging
import pprint
from twisted.internet import reactor
from WWidgets import StorkWidget
from WRam import PerfectWispMemory
from WModules import Messenger
from WStork import Stork

########################################################################################################
#
# WWWWWWWW                           WWWWWWWW       iiii
# W::::::W                           W::::::W      i::::i
# W::::::W                           W::::::W       iiii
# W::::::W                           W::::::W
#  W:::::W           WWWWW           W:::::W      iiiiiii          ssssssssss        ppppp   ppppppppp
#   W:::::W         W:::::W         W:::::W       i:::::i        ss::::::::::s       p::::ppp:::::::::p
#    W:::::W       W:::::::W       W:::::W         i::::i      ss:::::::::::::s      p:::::::::::::::::p
#     W:::::W     W:::::::::W     W:::::W          i::::i      s::::::ssss:::::s     pp::::::ppppp::::::p
#      W:::::W   W:::::W:::::W   W:::::W           i::::i       s:::::s  ssssss       p:::::p     p:::::p
#       W:::::W W:::::W W:::::W W:::::W            i::::i         s::::::s            p:::::p     p:::::p
#        W:::::W:::::W   W:::::W:::::W             i::::i            s::::::s         p:::::p     p:::::p
#         W:::::::::W     W:::::::::W              i::::i      ssssss   s:::::s       p:::::p    p::::::p
#          W:::::::W       W:::::::W              i::::::i     s:::::ssss::::::s      p:::::ppppp:::::::p
#           W:::::W         W:::::W               i::::::i     s::::::::::::::s       p::::::::::::::::p
#            W:::W           W:::W                i::::::i      s:::::::::::ss        p::::::::::::::pp
#             WWW             WWW                 iiiiiiii       sssssssssss          p::::::pppppppp
#                                                                                     p:::::p
#                                                                                     p:::::p
#                                                                                    p:::::::p
#                                                                                    p:::::::p
#                                                                                    p:::::::p
#                                                                                    ppppppppp
#
# this file contains all functionality to resprogramm a single wisp
#############################################################################################################
logger = logging.getLogger(__name__)

# this class represents all the communication between the pc and a single wisp.
# For every wisp you need to create one object
# The wisp can be in different states, the default sequence is:
# waiting -> gotobios  ---*A*--> programming -> endmemcheck -> unlockboot -> gotoboot -> boot
# You could also delete the parts of bios and boot, then Wisp will not execute the newly written data

# [*A*] new feature: sniffing wisp: the state sequence for a sniffer is:
# ... gotobios -> gotosnif -> sniffing   -> programming ... etc
# if there are wisps around this wisp that should sniff the communication of this wisp the sequence is:
# ... gotobios ->      wait4sniffers     -> programming ... etc
class Wisp(object):
    """docstring for Wisp"""
    # list of all states of the wisp:
    STATE_WAITING     =-1 # state in which Wisp is after initialization
    STATE_GOTOBIOS    = 0 # wisp needs to go to bios before programming
    STATE_PROGRAMMING = 1 # wisp is programming
    STATE_GOTOBOOT    = 2 # wisp needs to go into the boot programm
    STATE_FINISHED    = 3 # wisp is in the bootloadable
    STATE_GOTOSNIF    = 4 # wisp should sniff
    STATE_SNIFFING    = 5 # wisp is sniffing
    STATE_STOPSNIFFING =6 # wisp needs to go to normal mode again
    STATE_WAIT4SNIFFERS=7 # wisp needs to wait for sniffers to get ready to sniff
    STATE_TRANSFORMING =8 # wisp is doing it"s transformation, so ignore incoming messages
    STATE_MEMCHECK     =9 # wisp needs a memory check at the end of programming
    STATE_DECOMPRESS   =10 # TODO
    STATE = {   STATE_WAITING       : "WAITING",
                STATE_GOTOBIOS      : "GOTOBIOS",
                STATE_PROGRAMMING   : "PROGRAMMING",
                STATE_GOTOBOOT      : "GOTOBOOT",
                STATE_FINISHED      : "FINISH",
                STATE_GOTOSNIF      : "GOTOSNIF",
                STATE_SNIFFING      : "SNIFFING",
                STATE_STOPSNIFFING  : "STOPSNIFFING",
                STATE_WAIT4SNIFFERS : "WAIT4SNIFFERS",
                STATE_TRANSFORMING  : "TRANSFORMING",
                STATE_MEMCHECK      : "MEMCHECK",
                STATE_DECOMPRESS    : "DECOMPRESS",
            } # Just a list of strings for representation of the states on the gui

    MODE_SIMPLE         = -1 # NORMAL PROGRAMMING: send the data, do memcheck, execute mem
    MODE_IWILLBESNIFFED =  0 # In this mode I will be sniffed, so in the starting phase I must be sure sniffers are ready to sniff
    MODE_IAMSNIFFER     =  1 # If WISP is in this mode, it must sniff someone else his communication
    MODE_IWASASNIFFER   =  2 # Wisp was a sniffer, but needs to receive all not sniffed data.
    MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS = 3 # act like you were a sniffer, so first get a memory check, but also wait on sniffers
    MODE_UPDATE_ONLY    = MODE_IWASASNIFFER # act like you were a sniffer, so first get a memory check
    MODE_IAM_UPDATE_ONLY_SNIFFER = MODE_IAMSNIFFER # act like a normal sniffer, after sniffing, do memcheck
    TstartValue        = None
    constant_throttle  = False      # don"t throttle if this is true
    MEMLINE_PARALLEL   = 4          # do this amount of memory lines parallel

    bios_and_boot      = None
    destroy_windows_after_Xsec_when_finished = None

    # initialize the wisp
    def __init__(self, ID, filename = None, hexlines = None, compressed_data = False, accessSpecID = 1,
                    mode = None, send_util = None, wispFinishedCallback = None,
                    snifferReadyCallback = None, wrepWidget = None):
        super(Wisp, self).__init__()
        self.ID             = ID          # ID of the wisp
        self.filename       = filename    # file to load into the wisp (bootloadable hexfile)
        self.mode           = mode if mode!=None else self.MODE_SIMPLE   # wisp is default a normal wisp
        self.compressed_data= compressed_data
        self.finishedCallback     = wispFinishedCallback
        self.snifferReadyCallback = snifferReadyCallback
        self.wrepWidget     = wrepWidget
        # Messages variables
        self.send_util = send_util

        # timer
        self.start_time  = time.time()

        # Message handlers:
        self.targetMem = PerfectWispMemory(send_util= self.send_util,ID4hex= self.ID, filename= filename, hexlines = hexlines)
        if hexlines == None:
            try:
                hexlines = open(filename, "r").readlines()
            except Exception as e:
                raise NameError("What do you want? No hexlines and no valid file!")
        self.stork = Stork(   self.send_util,
                                ID4hex= self.ID,
                                hexlines= hexlines,
                                blockWritesPerAccessSpec = self.MEMLINE_PARALLEL,
                                constant_throttle = self.constant_throttle,
                                TstartValue = self.TstartValue)
        if(self.bios_and_boot):
            self.goBoot = Messenger(self.send_util,ID4hex= self.ID,
                                    message= "b007", epctailnot ='b105', readThis = 'b007')
        else:
            self.goBoot = None

        if(self.mode == Wisp.MODE_IAMSNIFFER or self.bios_and_boot):
            # goBios wordt ook gebruikt om terug te keren van sniffer mode
            self.goBios = Messenger(self.send_util,ID4hex= self.ID,
                                    message= "b105", epctail ='b105', readThis = 'b105')
        else:
            self.goBios = None

        if(self.mode == Wisp.MODE_IAMSNIFFER):
            self.goSniff= Messenger(self.send_util,ID4hex= self.ID,
                                    message= "ea41",epctail ='ea4e', readThis = 'ea41')
        else:
            self.goSniff = None

        if(self.compressed_data):
            self.goDecompress = Messenger(self.send_util,ID4hex= self.ID,
                                    message= "decd", readThis = 'decd')
        else:
            self.goDecompress = None

        # defining which handler to use in which state
        self.unit = dict({      self.STATE_GOTOBIOS:     self.goBios,
                                self.STATE_PROGRAMMING:  self.stork,
                                self.STATE_GOTOBOOT:     self.goBoot,
                                #self.STATE_FINISHED:         # don't handle messages in this mode
                                self.STATE_GOTOSNIF:     self.goSniff,
                                #self.STATE_SNIFFING      # don't handle messages in this mode
                                self.STATE_STOPSNIFFING: self.goBios,
                                #self.STATE_WAIT4SNIFFERS # don't handle messages in this mode
                                #self.STATE_TRANSFORMING  # don't handle messages in this mode
                                self.STATE_MEMCHECK:     self.targetMem,
                                self.STATE_DECOMPRESS:   self.goDecompress,})
        # (:widget:)
        self.wrepWidget.addWisp(self)
        # set start state
        self.setState(Wisp.STATE_WAITING)  # state of the wisp

        # giving the user some feedback:
        logger.info(self.ID +": * File to load:    %20s *"% self.filename)
        if(self.mode == Wisp.MODE_IWILLBESNIFFED):
            logger.info(self.ID +": * I WILL BE SNIFFED                 *")
        elif(self.mode == Wisp.MODE_IAMSNIFFER):
            logger.info(self.ID +": * I AM A SNIFFER                    *")
        logger.info(self.ID +": *****************************************")

    # this function will be called at an unexpected end of python execution,
    # when user cancels reprogramming, you might want to flush some final statistic here
    def stop(self):
        self.send_util.deleteMyAccessSpec()
        self.stork.stop()
        self.targetMem.stop()


    @staticmethod
    def globalInitParamater(throttleStartValue, constant_throttle, memlines_para, bios_and_boot, destroy_windows_after_Xsec_when_finished = None):
        # start sending messages with this payload size in words
        if throttleStartValue:
            Wisp.TstartValue = throttleStartValue
        # set the number of blockwrite opspecs per handshake:
        if memlines_para:
            if(memlines_para>7):
                raise NameError(self.ID +": Number of memlines can not be more than 7!")
            Wisp.MEMLINE_PARALLEL = memlines_para
        # don"t throttle up or down if this is set
        if(constant_throttle):
            Wisp.constant_throttle = constant_throttle # this will be the throttle value

        Wisp.bios_and_boot = bios_and_boot
        Wisp.destroy_windows_after_Xsec_when_finished = destroy_windows_after_Xsec_when_finished

    # acknowledge a message. How to acknowledge is embedded in the checkdata itself
    def ack(self,checkdata):
        self.send_util.stopTimerSuccesCheck() # stop the resend mechanism
        ret = self.check_data[checkdata]["ack"]() # call the ack function of this
        del self.check_data[checkdata] # one acknowledge per message is enough
        return ret

    def start(self):
        self.nextState()

    # This is the core function of the wisp class.
    # How to handle the message depends on the state
    def handleMessage(self, opspecs, epc):
        if(self.state in self.unit):
            self.unit[self.state].handleMessage(opspecs = opspecs, epc = epc)

    def getStates(self):
        ret = []
        ret.append(Wisp.STATE_WAITING)
        if(self.bios_and_boot):
            ret.append(Wisp.STATE_GOTOBIOS)

        if(self.mode == Wisp.MODE_IWILLBESNIFFED):
            ret.append(Wisp.STATE_WAIT4SNIFFERS)
        elif(self.mode == Wisp.MODE_IAMSNIFFER):
            ret.append(Wisp.STATE_GOTOSNIF)
            ret.append(Wisp.STATE_SNIFFING)
            ret.append(Wisp.STATE_STOPSNIFFING)
            ret.append(Wisp.STATE_MEMCHECK)
        elif(self.mode == Wisp.MODE_IWASASNIFFER):
            ret.append(Wisp.STATE_MEMCHECK)
        elif(self.mode == Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS):
            ret.append(Wisp.STATE_WAIT4SNIFFERS)
            ret.append(Wisp.STATE_MEMCHECK)

        ret.append(Wisp.STATE_PROGRAMMING)
        ret.append(Wisp.STATE_MEMCHECK)
        if(self.compressed_data):
            ret.append(Wisp.STATE_DECOMPRESS)

        if(self.bios_and_boot):
            ret.append(Wisp.STATE_GOTOBOOT)
        ret.append(Wisp.STATE_FINISHED)
        return ret

    # defining what the next state is if a state is finished
    def nextState(self,**extra_parameters):
        logger.info(self.ID +": Wisp was in state: "+ self.STATE[self.state] + " and is going to the next state --- Time elapsed: %.3f secs"% (time.time() - self.start_time))
        if(self.state == Wisp.STATE_WAITING):
                if self.bios_and_boot:
                    self.setState(Wisp.STATE_GOTOBIOS)
                    self.goBios.start(finished_callback = self.nextState)
                else:
                    # jump to the result of gotobios
                    self.state = Wisp.STATE_GOTOBIOS
                    self.nextState()

        elif(self.state == Wisp.STATE_GOTOBIOS):
                # if the wisp is in the bios look at the sniffer mode to see which state next to do
                if(self.mode == Wisp.MODE_SIMPLE): # don"t care about sniffers, NORMAL programming a single wisp
                    self.setState(Wisp.STATE_PROGRAMMING)
                    self.stork.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)

                elif(self.mode == Wisp.MODE_IWASASNIFFER): # don't care anymore about sniffers, check mem
                    self.setState(Wisp.STATE_MEMCHECK)
                    self.targetMem.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)

                elif(self.mode in ( Wisp.MODE_IWILLBESNIFFED,
                                    Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS)): # wait for sniffers as soon as you are in bios
                    self.setState(Wisp.STATE_WAIT4SNIFFERS)
                    self.snifferReadyCallback(self)

                elif(self.mode == Wisp.MODE_IAMSNIFFER): # this is a sniffer, so go to snif mode when you are in bios
                    self.setState(Wisp.STATE_GOTOSNIF)
                    self.goSniff.start(finished_callback = self.nextState)

        elif(self.state == Wisp.STATE_GOTOSNIF):
                self.setState(Wisp.STATE_SNIFFING)
                self.snifferReadyCallback(self)

        elif(self.state == Wisp.STATE_WAIT4SNIFFERS):
                if(self.mode == Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS):
                    self.setState(Wisp.STATE_MEMCHECK)
                    self.targetMem.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)
                else:
                    self.setState(Wisp.STATE_PROGRAMMING)
                    self.stork.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)

        elif(self.state == Wisp.STATE_SNIFFING):
                self.setState(Wisp.STATE_STOPSNIFFING)
                self.mode = Wisp.MODE_IWASASNIFFER
                self.goBios.start(finished_callback = self.nextState)

        elif(self.state == Wisp.STATE_PROGRAMMING ):
                if(extra_parameters['success']== True):
                    self.setState(Wisp.STATE_MEMCHECK)
                    self.targetMem.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)
                else:
                    self.iAmFinished()
        elif(self.state == Wisp.STATE_STOPSNIFFING ):
                self.setState(Wisp.STATE_MEMCHECK)
                self.targetMem.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)

        elif(self.state == Wisp.STATE_MEMCHECK):
                if(extra_parameters['all_memory_is_good'] == True):
                    if(self.compressed_data):
                        self.setState(Wisp.STATE_DECOMPRESS)
                        self.goDecompress.start(finished_callback = self.nextState)
                    if self.bios_and_boot:
                        self.setState(Wisp.STATE_GOTOBOOT)
                        self.goBoot.start(finished_callback = self.nextState)
                    else:
                        self.iAmFinished()
                else:
                    # MEMORY IS NOT GOOD, so do some stuff to send the missing parts
                    # get all data that is not good yet
                    hexlines = self.targetMem.getLongHexLinesFromBadCRCs()
                    # prepare mem checks for after the programming stage
                    self.targetMem.defineMemChecksFromHexlines(hexlines)

                    # collect how many words the original stork has
                    old_nr_of_words = self.stork.getNrOfWords()

                    # make a new stork
                    self.stork.stop()
                    self.stork = Stork(   send_util   = self.send_util,
                                            ID4hex      = self.ID,
                                            hexlines    = hexlines,
                                            blockWritesPerAccessSpec = self.MEMLINE_PARALLEL,
                                            constant_throttle        = self.constant_throttle)
                    self.unit[self.STATE_PROGRAMMING] = self.stork # update the message call list with the new stork

                    logger.info(self.ID +": * Reduced nr of words by memcheck: %4i *"% (old_nr_of_words - self.stork.getNrOfWords()))
                    logger.info(self.ID +": *****************************************")

                    self.setState(Wisp.STATE_PROGRAMMING)
                    # start stork
                    self.stork.start(finished_callback = self.nextState, destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished)

        elif(self.state == Wisp.STATE_GOTOBOOT):
                self.iAmFinished()

    def setState(self, state):
        self.state = state
        logger.info(self.ID +": Wisp is now in state: "+ self.STATE[self.state])

        #show in the widget
        self.wrepWidget.setState(self.ID, state, time.time()-self.start_time)

    def iAmFinished(self):
        self.setState(Wisp.STATE_FINISHED)
        self.send_util.deleteMyAccessSpec() # delete my own accessSpec from the reader
        logger.info(self.ID + ": " +self.wrepWidget.toString(self.ID))
        # notify stork that this wisp is finished
        self.finishedCallback(self)
