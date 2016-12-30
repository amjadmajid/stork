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

##      ## ########  ######## ########  ########  ######## ########  
##  ##  ## ##     ## ##       ##     ## ##     ## ##       ##     ## 
##  ##  ## ##     ## ##       ##     ## ##     ## ##       ##     ## 
##  ##  ## ########  ######   ########  ########  ######   ########  
##  ##  ## ##   ##   ##       ##        ##        ##       ##   ##   
##  ##  ## ##    ##  ##       ##        ##        ##       ##    ##  
 ###  ###  ##     ## ######## ##        ##        ######## ##     ## 
#
# Wireless REPProgrammER
# It uses: Stork - the fastest downstream protocol for CRFIDs
#####################################################################################################
#                                                                                                   #
# ## Stork has been tested and reportedly working on the following readers:                         #
#    - Impinj Speedway R420 (FCC)                                                                   #
#    - Impinj Speedway R1000                                                                        #
#                                                                                                   #
# ## Example usage:                                                                                 #
#   bin/stork -w <wisp id> -f <Intel Hex file> -M WISP5 <reader IP address>                         #
#                                                                                                   #
#  # Some extra options can be specied e.g. for setting the starting throttle index:                #
#   bin/stork -m <throttle index> -f <Intel Hex file> <reader IP address>                           #
#                                                                                                   #
#####################################################################################################

from __future__ import print_function
import argparse
import logging
import pprint
import time
import os
import sys
from twisted.internet import reactor, defer, task
import numpy as np
import matplotlib.pyplot as plt

import sllurp.llrp as llrp
from sllurp.llrp_proto import DEFAULT_MODULATION, Modulation_DefaultTari

from WWisp import Wisp
from WWidgets import WrepWidget

logger              = logging.getLogger("WRepper")


# Wireless REProgrammER
# This module can reprogram wisps in or excluding memcheck at the beginning and it will always do a memcheck at the end
# You could specify the stork parameters and en reprogramming mode (one by one, parallel or sniffing)

class WRepper(object):
    """docstring for WRepper"""

    MODE_ONEBYONE          =  2
    MODE_PARALEL           =  3
    MODE_ONEBYONE_AND_SNIFFING =  4

    def __init__(self, send_utils ,IDs4hex , filename = None, hexlines = None, compressed_data = False,
                    update_only = False, throttle_start = None, constant_throttle = None,
                    memline_parallel = None, bios_and_boot = True, pro_mode = None, destroy_windows_after_Xsec_when_finished =None):
        super(WRepper, self).__init__()

        self.ID = ''.join(IDs4hex)
        self.programmingMode     = pro_mode if pro_mode else self.MODE_ONEBYONE_AND_SNIFFING
        self.wispTargets         = dict() # all wisps that need to be reprogrammed
        self.activeWispTargets   = dict() # wisps that are now being reprogrammed
        self.destroy_windows_after_Xsec_when_finished = destroy_windows_after_Xsec_when_finished
        self.wrepWidget = WrepWidget(Wisp.STATE, destroy_callback = self.iAmCanceled)
        Wisp.globalInitParamater( constant_throttle  = constant_throttle,
                            memlines_para            = memline_parallel,
                            throttleStartValue       = throttle_start,
                            bios_and_boot            = bios_and_boot,
                            destroy_windows_after_Xsec_when_finished = self.destroy_windows_after_Xsec_when_finished
                            )


        nr_of_wisps     = len(IDs4hex)

        # initialize all the wisps
        for i in range(nr_of_wisps):

            if(self.programmingMode in {self.MODE_ONEBYONE,self.MODE_PARALEL,} or len(IDs4hex)==1 ):
                # sniffing is not possible
                if(update_only):
                    mode = Wisp.MODE_UPDATE_ONLY # do a memcheck first, because most is old
                else:
                    mode = Wisp.MODE_SIMPLE # reprogram completely
            else:
                if (i==0):
                    # this is the most important wisp
                    if(update_only):
                        # this important wisp needs an update only, but his friend wisps also, so this wisp needs to make sure his sniffing friends are ready
                        mode = Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS
                    else:
                        # this important wisp needs to make sure (needs to wait) his friends are readdy to sniff
                        mode = Wisp.MODE_IWILLBESNIFFED
                else:
                    # this is a sniffing wisp
                    mode = Wisp.MODE_IAMSNIFFER

            # add the wisp to the wisplist
            self.wispTargets[IDs4hex[i]] = Wisp(IDs4hex[i], filename = filename,hexlines = hexlines,
                    compressed_data = compressed_data,
                    send_util = send_utils[i], mode = mode,
                    wispFinishedCallback     = self.wispFinishedCallback,
                    snifferReadyCallback     = self.snifferReadyCallback,
                    wrepWidget               = self.wrepWidget
                     )


        # set some wisps in the active list
        if(self.programmingMode == self.MODE_ONEBYONE ):
            self.activeWispTargets[self.wispTargets.keys()[0]] = self.wispTargets.values()[0] # start with first wisp
        elif(self.programmingMode == self.MODE_PARALEL or self.programmingMode == self.MODE_ONEBYONE_AND_SNIFFING):
            for wisp in self.wispTargets:
                self.activeWispTargets[wisp] = self.wispTargets[wisp]

    # call this to start the process
    def start(self, finished_callback):
        self.finished_callback = finished_callback
        for wisp in self.activeWispTargets.values():
            wisp.start()

    # every time the reader sends a report, this message must be called with the reportresults
    def handleMessage(self, opspecs, epc):
        if(epc[0:4] in self.activeWispTargets):
            self.wispTargets[epc[0:4]].handleMessage(opspecs, epc)

    # if a wisp is finished, it will call this function.
    def wispFinishedCallback(self, finishedWisp):
        # remove finished wisp from active list
        self.activeWispTargets.pop(finishedWisp.ID)

        # check if there is another wisp that needs to start
        if(self.programmingMode == self.MODE_ONEBYONE): # normal mode
            for ID in self.wispTargets:
                if(self.wispTargets[ID].state == Wisp.STATE_WAITING):
                    self.activeWispTargets[ID] = self.wispTargets[ID]
                    self.activeWispTargets[ID].start()
                    logger.info("\n\n******************************* Next wisp *******************************\n")
                    return
        if(self.programmingMode == self.MODE_ONEBYONE_AND_SNIFFING): # sniffing mode
            for ID in self.wispTargets:
                # search a sniffing wisp and make it a communication wisp
                if(self.wispTargets[ID].state == Wisp.STATE_SNIFFING):
                    logger.info("\n\n******************************* Next wisp (sniffer) *******************************\n")
                    self.wispTargets[ID].nextState()
                    return
        if(self.programmingMode == self.MODE_PARALEL):
            pass # nothing has to be started, so just look if everyone has finished

        # if there is still at least one active wisp: wait for it, so do nothing here
        if(len(self.activeWispTargets)):
            return
        # all wisps are ready
        self.iAmFinished()

    # if a sniffer is ready to sniff it will call this function.
    def snifferReadyCallback(self, readyWisp):
        # check if other wisps are also ready
        for wisp in self.activeWispTargets:
            if(self.wispTargets[wisp].state not in {Wisp.STATE_SNIFFING, Wisp.STATE_WAIT4SNIFFERS,}):
                # there is at least 1 wisp not ready yet
                logger.info("Waiting for wisp: "+self.wispTargets[wisp].ID)
                return
        # if we reach this point all sniffers are sniffing and the master wisp is waiting for the sniffers
        # which means: time to to start programming!
        # search the master wisp (communication wisp) and start it
        for wisp in self.activeWispTargets:
            if(self.wispTargets[wisp].mode in (Wisp.MODE_IWILLBESNIFFED,
                                                 Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS) ): # only the communication wisp will be in this mode
                self.wispTargets[wisp].nextState()
                return

    # call this if you regret starting this module
    def stop(self):
        for wisp in self.wispTargets.values():
            wisp.stop()

    # This function will be called when a user closes a window
    def iAmCanceled (self):
        if(len(self.activeWispTargets)):
            self.stop()
            logger.info("Wisps canceled: callback")
            self.finished_callback(module = self, success = False)

    # execute this when reprogramming is completely finished for all wisps
    def iAmFinished (self):
        if(self.destroy_windows_after_Xsec_when_finished):
            reactor.callLater(self.destroy_windows_after_Xsec_when_finished, self.wrepWidget.destroy )
        logger.debug("Wisps finished: callback")
        self.finished_callback(module = self, success = True)
