#  Copyright (c) 2016,                                                                              #
# Author(s): Henko Aantjes,                                                                         #                 
# Date: 28/07/2016                                                                                  #
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

########  ######## ########  ########   #######   ######   ########     ###    ##     ## 
##     ## ##       ##     ## ##     ## ##     ## ##    ##  ##     ##   ## ##   ###   ### 
##     ## ##       ##     ## ##     ## ##     ## ##        ##     ##  ##   ##  #### #### 
########  ######   ########  ########  ##     ## ##   #### ########  ##     ## ## ### ## 
##   ##   ##       ##        ##   ##   ##     ## ##    ##  ##   ##   ######### ##     ## 
##    ##  ##       ##        ##    ##  ##     ## ##    ##  ##    ##  ##     ## ##     ## 
##     ## ######## ##        ##     ##  #######   ######   ##     ## ##     ## ##     ## 

# 	  simple minimalistic reprogramming file
#         It uses: Stork - a robust downstream protocol for CRFIDs
#####################################################################################################
#                                                                                                   #
# ## Stork has been tested and reportedly working on the following readers:                        #
#    - Impinj Speedway R420 (FCC)                                                                   #
#    - Impinj Speedway R1000                                                                        #
#                                                                                                   #
# ## Example usage:                                                                                 #
#   bin/stork -w <wisp id> -f <Intel Hex file> -M WISP5 <reader IP address>                        #
#                                                                                                   #
#  # Some extra options can be specied e.g. for setting the starting throttle index:                #
#   bin/stork -m <throttle index> -f <Intel Hex file> <reader IP address>                          #
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
######################################################################################################
STATE_SHUTTINGDOWN     = -1
STATE_INITIALIZING     =  0
STATE_ACTIVE           =  1
MODE_ONEBYONE          =  2
MODE_PARALEL           =  3
MODE_ONEBYONE_AND_SNIFFING =  4

# stork global variables.
fac                 = None
args                = None
tagReport           = 0
logger              = logging.getLogger("sllurp")
programmingState    = STATE_INITIALIZING
programmingMode     = MODE_ONEBYONE_AND_SNIFFING

# multiprogramming stork
wispTargets            = dict() # all wisps that need to be reprogrammed
activeWispTargets   = dict() # wisps that are now being reprogrammed

######################################################################################################

# Stop the twisted reactor at the end of the program. and show some statistics
def finish (_):
    for wisp in wispTargets.values():
        wisp.close()

    logger.info("Total number of tags seen:  %i"%tagReport)

    wispsProgrammed = 0
    for wisp in wispTargets.values():
        if(wisp.state == Wisp.STATE_BOOT):
            wispsProgrammed += 1
    logger.info("Number of wisps programmed: %i" % wispsProgrammed)

    wispsFailed = 0
    for wisp in wispTargets.values():
        if(wisp.state == Wisp.STATE_ABORTING):
            wispsFailed += 1
    logger.info("Number of wisps failed:     %i" % wispsFailed)

    if reactor.running:
        reactor.stop()

# shut down factory if reactor stops
def politeShutdown (factory):
    return factory.politeShutdown()

# this function will be called by sllurp at every reader report. reader report shows epc, write result, read result etc.
def tagReportCallback (llrpMsg):
    global tagReport, activeWispTargets, programmingState

    tags = llrpMsg.msgdict["RO_ACCESS_REPORT"]["TagReportData"]
    if(not len(tags)): # check on empty report
        logger.info("No tags seen")

    # in some modes we don"t expect any reader-tag communication
    if(programmingState in {STATE_INITIALIZING, STATE_SHUTTINGDOWN,}):
        for tag in tags:
            logger.info("not expecting: saw tag(s): epc = %s #seen: %s"%(tag["EPC-96"],tag["TagSeenCount"][0]))
        if(programmingState == STATE_SHUTTINGDOWN):
            fac.politeShutdown()
            logger.info("Wisps finished: Shutting down")
        return

    # some statistics
    for tag in tags:
        tagReport += tag["TagSeenCount"][0]

    #### Most important part of the function: handle the message(s) in the appropriate wisp
    for tag in tags:
        if(tag["EPC-96"][0:4] in activeWispTargets):
            logger.info(tag["EPC-96"])
            wispTargets[tag["EPC-96"][0:4]].handleMessage(tag)
        else:
            logger.info("wispID %s not in list"% tag["EPC-96"])

# if a wisp is finished, it will call this function.
def wispFinishedCallback(finishedWisp):
    global activeWispTargets,programmingState

    activeWispTargets.pop(finishedWisp.ID) # remove finished wisp from active list

    # check if there is another wisp that needs to start
    if(programmingMode == MODE_ONEBYONE): # normal mode
        fac.deleteAllAccessSpecs()
        for ID in wispTargets:
            if(wispTargets[ID].state == Wisp.STATE_WAITING):
                activeWispTargets[ID] = wispTargets[ID]
                wispTargets[ID].start()
                logger.info("\n\n******************************* Next wisp *******************************\n")
                return
    if(programmingMode == MODE_ONEBYONE_AND_SNIFFING): # sniffing mode
        fac.deleteAllAccessSpecs()
        for ID in wispTargets:
            # search a sniffing wisp and make it a communication wisp
            if(wispTargets[ID].state == Wisp.STATE_SNIFFING):
                logger.info("\n\n******************************* Next wisp (sniffer) *******************************\n")
                wispTargets[ID].nextState()
                return
    if(programmingMode == MODE_PARALEL):
        pass # nothing has to be started, so just look if everyone has finished

    # if there is still at least one active wisp: wait for it, so do nothing here
    if(len(activeWispTargets)):
        return

    # if no waiting wisp is found shut down
    fac.politeShutdown()
    programmingState = STATE_SHUTTINGDOWN
    logger.info("Wisps finished: Shutting down")

# if a sniffer is ready to sniff it will call this function.
def snifferReadyCallback(readyWisp):
    # check if other wisps are also ready
    for wisp in activeWispTargets:
        if(wispTargets[wisp].state not in {Wisp.STATE_SNIFFING, Wisp.STATE_WAIT4SNIFFERS,}):
            # there is at least 1 wisp not ready yet
            logger.info("waiting for wisp: "+wispTargets[wisp].ID)
            return
    # if we reach this point all sniffers are sniffing and the master wisp is waiting for the sniffers
    # which means: time to to start programming!
    # search the master wisp (communication wisp) and start it
    for wisp in activeWispTargets:
        if(wispTargets[wisp].mode in (Wisp.MODE_IWILLBESNIFFED,
                                             Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS) ): # only the communication wisp will be in this mode
            wispTargets[wisp].nextState()
            return

# handle user start input
def parse_args ():
    global args
    parser = argparse.ArgumentParser(description="Stork data transfer application for CRFID")
    parser.add_argument("host", help="IP address of RFID reader", nargs="*")
    parser.add_argument("-p", "--port", default=llrp.LLRP_PORT, type=int, help="port to connect to (default {})".format(llrp.LLRP_PORT))
    parser.add_argument("-t", "--time", default=10, type=float, help="number of seconds for which to inventory (default 10)")
    parser.add_argument("-d", "--debug", action="store_true", help="show debugging output")
    parser.add_argument("-n", "--report-every-n-tags", default=200, type=int, dest="every_n", metavar="N", help="issue a TagReport every N tags")
    parser.add_argument("-X", "--tx-power", default=0, type=int, dest="tx_power", help="Transmit power (default 0=max power)")
    parser.add_argument("-M", "--modulation", default="WISP5", help="modulation (default WISP5)")
    parser.add_argument("-T", "--tari", default=0, type=int, help="Tari value (default 0=auto)")
    parser.add_argument("-s", "--session", default=2, type=int, help="Gen2 session (default 2)")
    parser.add_argument("-P", "--tag-population", default=32, type=int, dest="population", help="Tag Population value (default 32)")
    parser.add_argument("-l", "--logfile")

    parser.add_argument("-f", "--filenames", nargs="+",type=str, help="the Intel Hexs file to transfer", dest="filenames", required=True)
    parser.add_argument("-m", "--throttle_start", default=None, type=int, help="start size of message payload in words according to set T")
    parser.add_argument("-w", "--wisp_targets", nargs="+",default ="all", type=str, help="the wisps that needs to be programmed", required=True)
    parser.add_argument("-c", "--constant_throttle", default = None, type=int, help="set the throttle constant")
    parser.add_argument("-u", "--thisisanupdate",action='store_true', default=False, help="Do a memory check first (takes some timeoverhead), then send missing pieces")
    parser.add_argument("-b", "--memline_parallel",default = None, type=int, help="set the number of parallel memlines i.e. number of blockwrites per opspec")
    args = parser.parse_args()

# here the logging format is set
def init_logging ():
    logLevel  = (args.debug and logging.DEBUG or logging.INFO)
    logFormat = "%(asctime)s:%(message)s"
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
    s6 ="\033[1;44m  * "*6+' \033[1;0m'+ '\033[1;31m'+'█'*sside+'\033[1;0m'+'\n'
    s5 = '\033[1;44m  '+ "\033[1;44m  * "*5+'   \033[1;0m'+ '█'*sside+'\n'
    logger.info('\n\n'+ (s6+s5)*4+s6+ ( '█'*(sside+25)+ '\n'+ '\033[1;31m'+'█'*(sside+25)+ '\033[1;0m'+'\n')*4)

# this function will be called (only once) after the very first reader round
def inventoryFinished(proto):
    global programmingState
    programmingState = STATE_ACTIVE

    # reset reader just in case it has old values
    fac.deleteAllAccessSpecs()

    # start sending the gotobios messages
    for wisp in activeWispTargets.values():
        wisp.start()

# function to initialize the Reader (Rospec)
def initFactory():
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
            tag_population=int(32),
            start_inventory=True,
            tx_power=args.tx_power,
            report_every_n_tags=args.every_n,
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

    # Start Stork transfer session. (set the callback to inventoryFinished)
    factory.addStateCallback(llrp.LLRPClient.STATE_INVENTORYING, inventoryFinished)

    return factory

# All initializations are done, so fire the engine!!
def startReactor (factory):

    # Add nack_counter to reader connect attempt.
    for host in args.host:
        reactor.connectTCP(host, args.port, factory, timeout=3)

    # Catch Ctrl-C and to politely shut down system.
    reactor.addSystemEventTrigger("before", "shutdown", politeShutdown, factory)

    # Start the sllurp reactor.
    reactor.run()

# the main python function, here starts everything
def main ():
    global fac, logger, args
    # initializations:
    parse_args()
    init_logging()
    # initialize the Reader
    fac = initFactory()
    wrepWidget = WrepWidget(Wisp.STATE)

    Wisp.globalInitParamater(
                        constant_throttle        = args.constant_throttle,
                        memlines_para            = args.memline_parallel,
                        wispFinishedCallback     = wispFinishedCallback,
                        snifferReadyCallback     = snifferReadyCallback,
                        throttleStartValue       = args.throttle_start,
                        fac                      = fac,
                        wrepWidget               = wrepWidget)

    nr_of_wisps     = len(args.wisp_targets)
    nr_of_filenames = len(args.filenames)
    if (nr_of_filenames == nr_of_wisps or nr_of_filenames == 1 ): # check if user input makes sense
        global wispTargets, activeWispTargets, programmingMode, programmingState
        # initialize all the wisps
        for i in range(len(args.wisp_targets)):
            filename = args.filenames[i if nr_of_filenames>1 else 0]

            if(programmingMode in {MODE_ONEBYONE,MODE_PARALEL,} or (len(args.wisp_targets)==1) or (nr_of_filenames>1)):
                # sniffing is not possible
                if(args.thisisanupdate):
                    # do a memcheck first, because most is old
                    mode = Wisp.MODE_UPDATE_ONLY
                else:
                    # reprogram completely
                    mode = Wisp.MODE_SIMPLE
            else:
                if (i==0):
                    # this is the most important wisp
                    if(args.thisisanupdate):
                        mode = Wisp.MODE_UPDATE_ONLY_JUST_LIKE_MY_SNIFFING_FRIENDS
                    else:
                        mode = Wisp.MODE_IWILLBESNIFFED
                else:
                    # this is a sniffing wisp
                    mode = Wisp.MODE_IAMSNIFFER

            wisp = Wisp(args.wisp_targets[i][2:],
                    filename,
                    accessSpecID = i+1,
                    mode = mode )

            wispTargets[wisp.ID] = wisp

        # give user a chance to change his/her mind
        while(True):
            var = raw_input("\nIs this what you want? [y/n]\n")
            if(var == "n"):
                return
            if(var == "y"):
                break

        # set some wisps in the active list
        if(programmingMode == MODE_ONEBYONE ):
            activeWispTargets[wispTargets.keys()[0]] = wispTargets.values()[0] # start with first wisp
        elif(programmingMode == MODE_PARALEL or programmingMode == MODE_ONEBYONE_AND_SNIFFING):
            for wisp in wispTargets:
                activeWispTargets[wisp] = wispTargets[wisp]
        logger.info("nr_of_wispatarget: "+  str(len(wispTargets)))

        # init and start the reactor
        startReactor(fac)

        # when everything is finished:
        raw_input("\nEnter to finish and close graph...\n")

    else :
        logger.error("len(wisps) != len(files)  -w = %s , -f = %s " % (args.wisp_targets,args.filenames))

if __name__ == "__main__":
    main()
