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


 ######  ########  #######  ########  ##    ##     ######   #######  ##    ## ######## ########   #######  ##       
##    ##    ##    ##     ## ##     ## ##   ##     ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##       
##          ##    ##     ## ##     ## ##  ##      ##       ##     ## ####  ##    ##    ##     ## ##     ## ##       
 ######     ##    ##     ## ########  #####       ##       ##     ## ## ## ##    ##    ########  ##     ## ##       
      ##    ##    ##     ## ##   ##   ##  ##      ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##       
##    ##    ##    ##     ## ##    ##  ##   ##     ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##       
 ######     ##     #######  ##     ## ##    ##     ######   #######  ##    ##    ##    ##     ##  #######  ######## 

# This Control Unit gathers all best functionalities that you as a wisp user would need.
# The easy to use GUI gives you high flexibility of reading from and writing to the wisp,
# going in or out of the bootloader, deleting data on the wisp, randomize the random table on the wisp
# or simply check the link quality
# and last but not least: You can reprogram the wisp
#          It uses: Stork - a robust downstream protocol for CRFIDs
#####################################################################################################

import argparse
import logging
import random
import time
from twisted.internet import reactor, task

from WModules import AccessSpecFactory as ASF
from WStork import Stork
from WRam import PerfectWispMemory
from WRepper import WRepper
from WModules import *
from WControlModules import *
from WWidgets import IOControlWidget

######################################################################################################
STATE_SHUTTINGDOWN     = -1
STATE_INITIALIZING     =  0
STATE_ACTIVE           =  1


# WISP Control global variables.
fac                 = None
active_modules       = []
GUI                  = None
random_hex_lines    = None
logger              = logging.getLogger("sllurp")
logpar              = ''
programmingState    = STATE_INITIALIZING
time_start          = time.time()

######################################################################################################

# Stop the twisted reactor at the end of the program. and show some statistics
def finish (_=''):
    for active_module in  active_modules:
        active_module.stop()
    if reactor.running:
        reactor.stop()

# shut down factory if reactor stops
def politeShutdown (factory):
    return factory.politeShutdown()

# this function will be called by sllurp at every reader report. reader report shows epc, write result, read result etc.
def tagReportCallback (llrpMsg):
    global programmingState

    tags = llrpMsg.msgdict["RO_ACCESS_REPORT"]["TagReportData"]
    if(not len(tags) and len(active_modules)): # check on empty report
        logger.debug("No tags seen")
        return

    # in some modes we don"t expect any reader-tag communication
    if(programmingState in {STATE_INITIALIZING, STATE_SHUTTINGDOWN,}):
        for tag in tags:
            logger.info("not expecting: saw tag(s): epc = %s #seen: %s"%(tag["EPC-96"],tag["TagSeenCount"][0]))
        if(programmingState == STATE_SHUTTINGDOWN):
            fac.politeShutdown()
            logger.info("Wisps finished: Shutting down")
        return

    #### Most important part of the function: handle the message(s) in the appropriate wisp
    for active_module in active_modules:
        for tag in tags:
            if(tag["EPC-96"][0:4] in [active_module.ID[i*4:i*4+4] for i in range(len(active_module.ID)/4)]):
                active_module.handleMessage(tag["OpSpecResult"],tag["EPC-96"])

    GUI.tagWidget.showTagsInTextWidget(tags, EPCLength=6*4) # show tags in widget
# if modules are finished, it will call this function.
def module_finished_callback(module, parameter = None):
    if(module in active_modules):
        active_modules.remove(module)
    if(parameter):
        for p in parameter:
            logger.info("{}".format(p))

# if you press Ctrl-C in the terminal or close the window, then this function makes sure everything closes cleanly
def kill_all():
    for active_module in active_modules:
        active_module.stop()
    fac.politeShutdown()
    logger.info("Wisp Control finished: Shutting down, time in seconds : " + str(time.time()- time_start))
    # this is all goodbey

# this function will be called (only once) after the very first reader round
def inventoryFinished(proto):
    global programmingState, time_start
    if(programmingState != STATE_ACTIVE):
        GUI.updatetxt("Connection established")
        programmingState = STATE_ACTIVE
        time_start = time.time()

    # reset reader just in case it has old values
    fac.deleteAllAccessSpecs()

# the main python function, here starts everything
def main ():
    global fac, logger, programmingState, GUI
    # initializations:
    argparser = argparse.ArgumentParser(description="Stork data transfer application for CRFID")
    argparser.add_argument("-f", "--filenames", nargs="+",type=str, help="the Intel Hexs file to transfer")
    argparser.add_argument("-addr_st", "--start_address",type=str, help="set start address")
    argparser.add_argument("-addr_end", "--end_address",type=str, help="set end address")
    argparser.add_argument("-repeat", "--repeat",type=str, help="set repeat")

    # argparser.add_argument("-C", "--mem_clear_start_and_end", nargs="+", default=None, type=str, help="give start and end address to clear the wisp", dest="clear_mem")
    # argparser.add_argument("-R", "--sendRandomData", default=0,nargs="+", type=int, help="give it a description", dest="randomHex")
    # argparser.add_argument("-A", "--a_number", default=None, type=int, help="give it a description", dest="input_A")
    # argparser.add_argument("-L", "--list", nargs="+",default ="a b", type=str, help="the wisps that needs to be programmed", dest="wisp_targets",required=True)
    args = parse_args(argparser)
    init_logging(args)
    fac = initFactory(args, inventoryFinished, tagReportCallback, finish)

    buttonlist = {  '1 Show Wisp List':   updateWispList,
                    '2 Goto Bios':        gotobios,
                    '3 Goto Sniff':       gotosniff,
                    '4 Goto Boot':        gotoboot,
                    '4 Refresh Random NRs':refreshRandomNumbers,
                    '5 Send File Data':   sendData,
                    '6 Decompress':       decompress,
                    '7 Read Data':        readData,
                    '8 MemCheck':         memCheck,
                    '9 Clear Data':       clear_mem,
                    'A Reprogram':        reprogram,
                    }
    buttoncolors = {'1 Show Wisp List':   ['dark green','white'],
                    '2 Goto Bios':        ['gold','black'],
                    '3 Goto Sniff':       ['medium sea green','white'],
                    '4 Goto Boot':        ['navy','white'],
                    '4 Refresh Random NRs':['indian red','black'],
                    '5 Send File Data':   ['maroon','white'],
                    '6 Decompress':       ['grey50','white'],
                    '7 Read Data':        ['purple4','white'],
                    '8 MemCheck':         ['steel blue','white'],
                    '9 Clear Data':       ['black','white'],
                    'A Reprogram':        ['deep sky blue','black'],
                    }

    optionlist = {  '1 BWPayload':    ['throttle']+[str(x)for x in range(1,11)]+[str(x)for x in range(12,31,2)],
                    '2 OpSpecsPerAS': ['default (4)'] + [str(x)for x in range(1,8)],
                    '3 File':         ['ihex/ccs1.hex','ihex/ccs2.hex', 'ihex/ccs3decom.hex','ihex/intelFormat.hex', 'random']+(args.filenames if args.filenames else []),
                    '4 Updata Only':  ['False', 'True'],
                    '5 Reprogramming Mode':['Broadcast','Sequential', 'Opportunistic'],
                    '6 BIOS and BOOT':['Disabled', 'Enabled'],
                    '7 Start Address':['0x1800', '0x1840', '0x4400','0x6400','0x8400'],
                    '8 End Address':  ['0x1880', '0x6400','0x7000','0x8400','0x9000','0xA400','0xC400','0xE400','0xFF00'],
                    '9 Destroy Windows':['>1 sec', '>5 sec', '>10 sec','>20 sec', 'never'],
                    'A Compression':  ['Disabled', 'Enabled'],
                    'B Repeat':     [str(x) for x in range(0,4)]+[str(x) for x in range(4,40,5)],
                    }

    GUI = IOControlWidget(buttonlist,optionlist,buttoncolors = buttoncolors, destroy_callback = kill_all, terminal_callback = terminalCommandParser, pause_callback = pause_reader)

    task.LoopingCall(GUI.update).start(.1) # call 'GUI.update' every .1 second to make the gui responsive
    updateGUIwithArgs(args)
    # init and start the reactor
    startReactor(fac, args)

    # the previous line is a blocking function, so
    # anything after it will only be executed after the reactor is terminated

def updateGUIwithArgs(args):
    if args.start_address:
        GUI.addAndSetOption('7 Start Address',args.start_address)
    if args.end_address:
        GUI.addAndSetOption('8 End Address', args.end_address)
    if args.repeat:
        GUI.addAndSetOption('B Repeat', args.repeat)

def pause_reader(resume = False, pause = False):
    if(resume):
        fac.resumeInventory()
    elif(pause):
        fac.pauseInventory()


def terminalCommandParser(command):
    global logpar
    cm = [c for c in command.split(' ') if c is not ''] # split command
    l = len(cm) #
    if l == 0:
        return
    if cm[0].lower() in {'read', 'r'} and l in {3,4}: # check on r[ead] + start/- + end/- [+ filename]
        if(cm[1] is not '-'):
            GUI.addAndSetOption('7 Start Address', cm[1])
        if(cm[2] is not '-'):
            GUI.addAndSetOption('8 End Address', cm[2])
        if(l == 4):
            readData({'save_to_file': cm[3],})
        else:
            readData()
    elif cm[0].lower() in {'write'[:i] for i in range(1,10)} and l == 2: # check on w[rite] + filename
        GUI.addAndSetOption('3 File', cm[1])
        sendData()
    elif cm[0].lower() in {'random'[:i] for i in range(2,10)} and l== 3:  # check on ran[dom] + start +end
        GUI.addAndSetOption('3 File', 'random')
        if(cm[1] is not '-'):
            GUI.addAndSetOption('7 Start Address', cm[1])
        if(cm[2] is not '-'):
            GUI.addAndSetOption('8 End Address', cm[2])

        sendData()
    elif cm[0].lower() in {'clear'[:i] for i in range(1,10)} and l == 3:  # check on c[lear] + start +end
        if(cm[1] is not '-'):
            GUI.addAndSetOption('7 Start Address', cm[1])
        if(cm[2] is not '-'):
            GUI.addAndSetOption('8 End Address', cm[2])
        clear_mem()

    elif cm[0].lower() in {'reprogram'[:i] for i in range(3,10)} and l == 2: # check on rep[rogram] + file/-
        if(cm[1] is not '-'):
            GUI.addAndSetOption('3 File', cm[1])

        sendData()
    elif cm[0].lower() in {'bios'[:i] for i in range(2,5)} : # check on bi[os] + [wisp0]+ [wisp1]+ ...
        if l>1:
            GUI.setWispSelection(cm[1:])
        gotobios()
    elif cm[0].lower() in {'boot'[:i] for i in range(2,5)} : # check on bo[ot] + [wisp0]+ [wisp1]+ ...
        if l>1:
            GUI.setWispSelection(cm[1:])
        gotoboot()
    elif cm[0].lower() in {'sniffers'[:i] for i in range(2,10)} : # check on bo[ot] + [wisp0]+ [wisp1]+ ...
        if l>1:
            GUI.setWispSelection(cm[1:])
        gotosniff()
    elif cm[0].lower() in {'sendthis'[:i] for i in range(2,10)}  and l > 1: # check on se[ndthis]+ message/n[owrite] + readthis/nr_of_words_to_read
        if cm[1] not in {'nowrite'[:i] for i in range(1,10)} and (len(cm[1])%4) == 0:
            message = cm[1]
        else:
            message = None
        if l>2:
            if(len(cm[2])%4)==0:
                readThis = cm[2]
                readAndReport_NrOfWords =None
            else:
                readThis = None
                readAndReport_NrOfWords =int(cm[2])

        send_this(message= message,readThis = readThis, readAndReport_NrOfWords = readAndReport_NrOfWords)
    elif cm[0].lower() in {'logpar'[:i] for i in range(2,10)} and l > 1 : # set a logging parameter
        logpar = ' '.join(cm[1:])
    elif cm[0].lower() in {'buttons'[:i] for i in range(1,10)} : # check on bu[ttons]
        show_button_info()
    elif cm[0].lower() in {'help'[:i] for i in range(1,10)} : # check on h[elp]
        show_button_info()
    else:
        GUI.showWarning("I don't understand your command! length = {}; command = {};\n".format(l,  ' + '.join(cm)))
        show_terminal_helper_text('add')


def show_terminal_helper_text(mode = 'replace'):
    GUI.updatetxt("\nYOU ARE NEW?\n\n" + \
        "Here are some terminal examples:\n\t" + \
        "h[elp]                                         Show this terminal help list\n\t" + \
        "bu[ttons]                                      Show Button info\n\t" + \
        "r[ead] <start addr>/- <end addr>/- [<file>]    Read from the wisp, '-' means 'take from GUI, print to file'\n\t" + \
        "w[rite] <filename>                             Write a file to the wisp(s) \n\t" + \
        "ra[ndom] <start addres>/- <endaddress>/-       Send NEW random data to the wisp(s) \n\t" + \
        "c[lear] <start addres>/- <endaddress>/-        Clear data on the wisp\n\t" + \
        "rep[rogram] <filename>/random                  Reprogram the wisp, with current GUI options, except given filename\n\t" + \
        "bi[os] [<wispID0> <wispID1> ..]                Send wisps to the bootloader\n\t" + \
        "bo[ot] [<wispID0> <wispID1> ..]                Send wisps to the application\n\t" + \
        "sn[iffers] [<wispID0> <wispID1> ..]            Send wisps in sniffer/eavesdrop mode\n\t" + \
        "se[ndthis] <message>/n[owrite] <expected readopspec result>/<expected number of words>\n\t" + \
        "                                               Send custom write command to wisps, plus define when you are satisfied, \n\t"+\
        "                                               with a specific result or with any data number of words\n"+\
        "lo[gpar] <text> [<moretext>]                   Add extra text (example: distance reader tag) \n"+\
        "                                               in the most important log lines\n"+\
        "type anything else to see this \n\n\t"
        "**Characters and variables between [brackets] are not necessary, you may type them\n\t" + \
        "**When there is a / you may choose on eof the two\n\t" + \
        "**Type always something instead of each <parameter>, no spaces allowed\n\t" + \
        "**Commands are not capital sensitive, parameters are.\n\t"
        , mode
    )
def show_button_info():
    GUI.updatetxt("\nYOU ARE NEW and want to know what the buttons do?\n\n\t" + \
            "Show Wisp List         Show and select the wisps that the reader can see\n\t"+ \
            "Goto Bios              Send all selected wisps the go-to-bios command\n\t"+ \
            "Goto Boot              Send all selected wisps the go-to-boot command\n\t"+ \
            "Refresh Random NRs     Refresh for all selected wisps their random number table\n\t"+ \
            "Send File Data         Send all selected wisps the file that is chosen or if file is\n\t"+\
            "                       'random' then use the 'start address' and 'end address' to generate new random words. \n\t"+\
            "                       The parameters 'BWpayload' and 'OpSpecsPerAS' will be fetched\n\t"+ \
            "Read Data              Read from all selected wisps the data defined by 'start address' to 'end address'\n\t"+ \
            "Clear Data             Clear from all selected wisps the data defined by 'start address' to 'end address'\n\t"+ \
            "MemCheck               Do for all selected wisps a memory check according the the selected file or \n\t"+\
            "                       according to the last sended random data (in this session, so don't close this window) if filename is 'random'\n\t"+ \
            "Reprogram              Reprogram all selected wisps with the file, this includes a memcheck after reprogramming. \n\t"+\
            "                       User may choose the do a memcheck before sending, by selecting update_only. \n\t"+\
            "                       User may reprogram with random data, but than the bios and boot should be disabled. \n\t"+\
            "                       Reprogramming uses the mode selected by variable 'reprogramming mode', here you can turn sniffing off \n\t" +\
            "Goto Sniff             Send all selected wisps the go-to-sniff command\n\t" +\
            ""
        )


#######################################################################################
# Below are all the function that are connected to the buttons of the gui and
# the finished_callbacks of the tasks that where started by pressing the button
#######################################################################################
def updateWispList():
    GUI.setWispSelection(GUI.tagWidget.getGoodTags(1))

def send_this(message= None,readThis = None, readAndReport_NrOfWords = None):
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('sending command['+(message if message else '-') +'] to wisps: ' +' and '.join(wisps) + ' and expecting a result ['+(readThis if readThis else '-')+'] or ' +(readAndReport_NrOfWords if readAndReport_NrOfWords else '-')+ ' words')
    for wispID in wisps:
        active_modules.append(
            Messenger(
                ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, message= message, readThis = readThis, readAndReport_NrOfWords = readAndReport_NrOfWords
                )
            )
        active_modules[-1].start(finished_callback = send_this_finished)

def send_this_finished(module, **args):
    GUI.updatetxt(module.ID + ' your message is delivered\n')
    if 'callback_parameter' in args:
        GUI.updatetxt(module.ID + ' your response is ' + args['callback_parameter'], 'add')

    module_finished_callback(module)

def gotobios():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('sending gotobios to wisps: ' +' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            Messenger(
                ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, message= "b105", readThis = 'b105'
                )
            )
        active_modules[-1].start(finished_callback = gotobios_finished)

def gotobios_finished(module, **parameters):
    GUI.updatetxt(module.ID + ' wisp is in bios')
    module_finished_callback(module)


def gotoboot():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('sending gotoboot to wisps: ' +' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            Messenger(
                ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, message= "b007", epctailnot ='b105', readThis = 'b007'
                )
            )
        active_modules[-1].start(finished_callback = gotoboot_finished)

def gotoboot_finished(module, **parameters):
    GUI.updatetxt('wisp is in boot')
    module_finished_callback(module)


def gotosniff():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('sending gotosniff to wisps: ' +' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            Messenger(
                ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, message= "ea41",epctail ='ea4e', readThis = 'ea41'
                )
            )
        active_modules[-1].start(finished_callback = gotosniff_finished)

def gotosniff_finished(module, **parameters):
    GUI.updatetxt(module.ID +' wisp is in sniff mode')
    module_finished_callback(module)


def refreshRandomNumbers():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('Reload Random numbers to the wisps: '+' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            WiRandom(ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID
                )
            )
        active_modules[-1].start(finished_callback = refreshRandomNumbers_finished)

def refreshRandomNumbers_finished(module):
    GUI.updatetxt(module.ID + ': Mem contains now new random numbers')
    module_finished_callback(module)


def sendData():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    filename= GUI.getSelected('File')
    wisps   = GUI.getSelectedWispIDs()
    if(len(wisps)==0):
        wisps = GUI.tagWidget.getGoodTags(.5)
    if len(wisps)==0:
        GUI.showWarning('NOOO! Where is WISP?')

    hexlines = get_hex_lines(old_random = False)
    if not hexlines:
        return
    BWPAS   = GUI.getSelected('OpSpecsPerAS')
    BWPAS   = 4 if BWPAS== 'default (4)' else int(BWPAS)
    CT      = GUI.getSelected('BWPayload')
    CT      = None if CT== 'throttle' else int(CT)
    DWAX    = GUI.getSelected('Destroy Windows')
    DWAX    = None if DWAX == 'never' else int(DWAX.split()[0][1:])

    GUI.updatetxt('Sending data from "'+filename+'" to wisps: '+' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            Stork( send_util = ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID,
                hexlines=hexlines,
                blockWritesPerAccessSpec = BWPAS,
                constant_throttle = CT, )
            )
        active_modules[-1].start(finished_callback = sendData_finished,destroy_windows_after_Xsec_when_finished = DWAX)

def sendData_finished(module, **parameters):
    if(parameters['success']):
        GUI.updatetxt(module.ID + ': Mem contains now your new data')
    else:
        GUI.showWarning(module.ID + ': Send data canceled')
    module_finished_callback(module)
    if('log' in parameters):
        logger.info(parameters['log']+ logpar)

    if(GUI.getSelected('Compression')== 'Enabled'):
        GUI.setWispSelection([module.ID])
        decompress()
    else:
        check_repeat_send_data()

def check_repeat_send_data():
    repeat = int(GUI.getSelected('Repeat'))
    if(repeat):
        GUI.addAndSetOption('B Repeat',str(repeat-1))
        if(repeat in {5,10,15,20,25,30,35,40} ):
            logger.info("Log stork next payload")
            BWPayload = GUI.getSelected('BWPayload')
            if(BWPayload == 'throttle'):
                BWPayload = 35
            else:
                BWPayload = int(BWPayload)
            GUI.addAndSetOption('1 BWPayload',str(max(1,BWPayload-5)))
        sendData()

def decompress():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    wisps   = GUI.getSelectedWispIDs()
    GUI.updatetxt('sending decompressing command to wisps: ' +' and '.join(wisps))
    for wispID in wisps:
        active_modules.append(
            Messenger(
                ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, message= "decd", readThis = 'decd'
                )
            )
        active_modules[-1].start(finished_callback = decompress_finished)


def decompress_finished(module=None, **parameters):
    GUI.updatetxt(module.ID + ": Decompression is finished")
    logger.info("Log stork decompression time {:.3f}".format(parameters["time"])+ ", "+ logpar)
    module_finished_callback(module)
    check_repeat_send_data()

def readData(return_metadata = None):
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    start = h2i(GUI.getSelected('Start Address'))
    end = h2i(GUI.getSelected('End Address'))
    wisps = GUI.getSelectedWispIDs()
    # safety checks
    if(not wisps):
        GUI.showWarning('Reading from ' + i2h(start)+ 'to ' +i2h(end) + ' to wisps: \n MAKE A SELECTION FIRST!')
        return
    if(end <= start):
        GUI.showWarning('End Address ('+i2h(start)+') is smaller than or equal to Start Address!('+ i2h(end)+ ')')
        return

    GUI.updatetxt('Reading from ' + i2h(start)+ ' to ' +i2h(end) + ' from the wisp(s): '+' and '.join(wisps))

    for wispID in wisps:
        active_modules.append(
            WiRead(ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, start_address = start, end_address = end, metadata = return_metadata
                )
            )
        active_modules[-1].start(finished_callback = readData_finished)


def readData_finished( data, module):
    GUI.updatetxt(module.ID + ': Mem contains this data:\n\t'+'\n\t'.join(data))
    module_finished_callback(module)
    start_address = module.start_address
    end_address = module.end_address
    wispID = module.ID

    hexlines = get_hex_lines()
    if not hexlines:
        return
    try:
        P = PerfectWispMemory(hexlines = hexlines, prepare_mem_checks= False)
        expected_data = P.getMem( address = start_address, length_in_words = (end_address - start_address)/2)
        GUI.updatetxt(module.ID + ': Mem expected this data:\n\t'+expected_data)
        count_good = countEqual(''.join(data).lower(),expected_data.lower())
        nr_of_words = len(expected_data)/4
        GUI.updatetxt('Log stork Mem is {:.3f} the same as the file ({}/{}){}'.format(
                        count_good*1.0/nr_of_words, count_good, nr_of_words, logpar
                        ))

        if module.metadata:
            try:
                filename = module.metadata['save_to_file']
            except Exception as e:
                GUI.showWarning('Metadata corrupt, not saved to file')
                return
                with open(filename, 'w') as f:
                    f.write('wisp '+wispID+'\naddress '+ i2h(start_address) + ' ' + i2h(end_address) + '\n')
                    f.write('readdata ' + ''.join(data) + '\n')
                    f.write('perfectdata ' + ''.join(expected_data) + '\n')
    except Exception as e:
        pass
# count the number of words that are equal in the 2 strings
def countEqual(str1,str2):
    return sum([str1[k:k+4]==str2[k:k+4] for k in range(0,min(len(str1),len(str2)),4)])

def clear_mem():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    start = h2i(GUI.getSelected('Start Address'))
    end = h2i(GUI.getSelected('End Address'))
    wisps = GUI.getSelectedWispIDs()
    # safety checks
    if(start <= 0x4400 and end >=0x6400):
        GUI.showWarning("NOOO!! Don't clear the bootloader section, that will wirelessly brick the tag!")
        return
    if(end <= start):
        GUI.showWarning('End Address ('+i2h(start)+') is smaller than or equal to Start Address!('+ i2h(end)+ ')')
        return
    if(start == 0x1800 and len(wisps)>1):
        GUI.showWarning("NOOO!! You don't want to delete the random numbers of multiple wisps at the same time!\nIf you do, they will talk like coffee-chickens")
        return

    GUI.updatetxt('Clearing memory from ' + i2h(start)+ 'to ' +i2h(end) + ' to wisps: '+' and '.join(wisps))
    for wispID in GUI.getSelectedWispIDs():
        active_modules.append(
            WiClear(ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex= wispID, start_address = start, end_address = end
                )
            )
        active_modules[-1].start(finished_callback = clear_mem_finished)

def clear_mem_finished(module):
    GUI.updatetxt(module.ID + ': Mem is cleared now')
    module_finished_callback(module)

def get_hex_lines(old_random = True):
    global random_hex_lines
    filename = GUI.getSelected('File')
    if filename == 'random':
        if  random_hex_lines and old_random:
            return random_hex_lines
        else:
            start   = h2i(GUI.getSelected('Start Address'))
            end     = h2i(GUI.getSelected('End Address'))
            if(end <= start):
                GUI.showWarning('End Address ('+i2h(start)+') is smaller than or equal to Start Address!('+ i2h(end)+ ')')
                return False
            random_hex_lines = getRandomHexLines(size = end-start, address = start)
            return random_hex_lines
    else:
        try:
            hexlines= open(filename, "r").readlines()
            return hexlines
        except Exception as e:
            GUI.showWarning("Can't open the file")
            return False

def memCheck():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return

    wisps    = GUI.getSelectedWispIDs()
    hexlines = get_hex_lines()
    if not hexlines:
        return
    DWAX    = GUI.getSelected('Destroy Windows')
    DWAX    = None if DWAX == 'never' else int(DWAX.split()[0][1:])
    GUI.updatetxt('Doing a memcheck to wisps: '+' and '.join(wisps))
    for wispID in GUI.getSelectedWispIDs():
        active_modules.append(
            PerfectWispMemory( send_util = ASF(wispID = wispID, accessSpecID = ASF.nextASID(), fac = fac),
                ID4hex   = wispID,
                hexlines = hexlines
                )
            )
        active_modules[-1].start(finished_callback = memCheck_finished, destroy_windows_after_Xsec_when_finished = DWAX)

def memCheck_finished( module, **parameters):
    if(parameters['all_memory_is_good'] == 'canceled'):
        GUI.showWarning(module.ID + ': Memcheck is canceled')
    elif(parameters['all_memory_is_good']):
        GUI.updatetxt(module.ID + ': Mem is checked now and is GOOD :D')
    else:
        GUI.showWarning(module.ID + ': Mem is checked now and is BAD :(')
    if('time' in parameters):
        logger.info("Log stork memCheck time {:.3f}".format(parameters['time']) + (", "+logpar if logpar else logpar))
    module_finished_callback(module)


def reprogram():
    if(programmingState is not STATE_ACTIVE):
        GUI.showWarning('NOOO! Connection is not active!')
        return
    filename= GUI.getSelected('File')
    wisps   = GUI.getSelectedWispIDs()
    nr_of_wisps = len(wisps)
    if(nr_of_wisps == 0):
        GUI.showWarning('Select a wisp first!')
        return
    bios_and_boot  = (GUI.getSelected('BIOS and BOOT') == 'Enabled')
    if(bios_and_boot and filename == 'random'):
        GUI.showWarning( "NOOO!! You don't want to boot into random data!")
        return
    hexlines= get_hex_lines()
    if not hexlines:
        return

    BWPAS   = GUI.getSelected('OpSpecsPerAS')
    BWPAS   = 4 if BWPAS== 'default (4)' else int(BWPAS)
    CT      = GUI.getSelected('BWPayload')
    CT      = None if CT== 'throttle' else int(CT)
    UO      = GUI.getSelected('Updata Only') == 'True'
    COMPR   = GUI.getSelected('Compression') == 'Enabled'
    M       = GUI.getSelected('Reprogramming Mode')
    M       = WRepper.MODE_ONEBYONE_AND_SNIFFING if M =='Broadcast' else \
              (WRepper.MODE_ONEBYONE if M == 'Sequential' else \
              WRepper.MODE_PARALEL)
    DWAX    = GUI.getSelected('Destroy Windows')
    DWAX    = None if DWAX == 'never' else int(DWAX.split()[0][1:])
    GUI.updatetxt('Reprogramming data from "'+filename+'" to wisps: '+' and '.join(wisps))
    active_modules.append(
        WRepper( [ASF(wispID = wisps[i],
                            accessSpecID = ASF.nextASID(),
                            fac = fac) for i in range(nr_of_wisps)] ,
                IDs4hex = wisps , hexlines = hexlines, update_only = UO, compressed_data = COMPR,
                constant_throttle = CT, memline_parallel = BWPAS,
                bios_and_boot = bios_and_boot, pro_mode = M, destroy_windows_after_Xsec_when_finished = DWAX)
    )
    active_modules[-1].start(finished_callback = reprogram_finished)

def reprogram_finished(module, **parameters):
    if(parameters['success']):
        ID = module.ID
        GUI.updatetxt(' '.join(ID[x:x+4] for x in range(0, len(ID),4)) + ': Wisp(s) is/are reprogrammed now')
    else:
        GUI.showWarning(module.ID + ': reprogramming canceled by you')
    module_finished_callback(module)

    repeat = int(GUI.getSelected('Repeat'))
    if(repeat):
        GUI.addAndSetOption('B Repeat',str(repeat-1))
        reprogram()


if __name__ == "__main__":
    main()
