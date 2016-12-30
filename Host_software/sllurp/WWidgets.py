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
import random
import numpy as np
import matplotlib.pyplot as plt
from Tkinter import *
from WModules import h2i, i2h
import tkFont
logger              = logging.getLogger()

# this file contains all tkinter widgets

 ######  ########  #######  ########  ##    ## 
##    ##    ##    ##     ## ##     ## ##   ##  
##          ##    ##     ## ##     ## ##  ##   
 ######     ##    ##     ## ########  #####    
      ##    ##    ##     ## ##   ##   ##  ##   
##    ##    ##    ##     ## ##    ##  ##   ##  
 ######     ##     #######  ##     ## ##    ## 

class StorkWidget(object):
    """docstring for StorkWidget"""

    def __init__(self, stork, title = "",destroy_callback = None):
        super(StorkWidget, self).__init__()
        self.setStorkTarget([(len(x)-12)/4 for x in stork.lines])
        self.destroy_callback = destroy_callback
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.destroyedByUser) # this is instead of destroying the window!
        # self.root.focus()
        self.root.title(stork.ID+ ": " + title)
        text_w = min(max(self.plot_y_target), 220)
        text_h = sum(len([y for y in self.plot_y_target if y>i*150]) for i in range(10))+4
        self.txt = Text(self.root,width= text_w,height= text_h)
        self.txt.pack()
        for x in range(len(self.plot_y_target)):
            self.txt.insert(INSERT,"0"*self.plot_y_target[x]+"\n")

    def setStorkTarget(self, line_heigths):
        self.plot_y_target = line_heigths
        self.plot_y_out = np.zeros(len(line_heigths))
        self.plot_y_out_acked = np.zeros(len(line_heigths))

    def ack(self,linenumber,msg_size):
        begin = "%i.%i"%(linenumber+1,self.plot_y_out_acked[linenumber])
        eind = "%i.%i"%(linenumber+1,self.plot_y_out[linenumber])
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"1"*msg_size)
            self.txt.tag_add("ack", begin, eind)
            self.txt.tag_config("ack", background="black", foreground="white")
        self.plot_y_out_acked[linenumber] +=msg_size

    def setTry(self,linenumber,msg_size):
        begin = "%i.%i"%(linenumber+1,self.plot_y_out_acked[linenumber])
        eind = "%i.%i"%(linenumber+1,self.plot_y_out_acked[linenumber]+msg_size)
        end_of_line = "%i.%i"%(linenumber+1,self.plot_y_target[linenumber])
        if(self.txt):
            self.txt.delete(begin,end_of_line)
            self.txt.insert(begin,"0"*(self.plot_y_target[linenumber]-
                        self.plot_y_out_acked[linenumber]-msg_size))
            self.txt.insert(begin,"X"*msg_size)
            self.txt.tag_add("try", begin, eind)
            self.txt.tag_config("try", background="yellow", foreground="grey")
        self.plot_y_out[linenumber] = self.plot_y_out_acked[linenumber]
        self.plot_y_out[linenumber] +=msg_size

    def destroy(self):
        try:
            self.txt = None
            self.root.destroy()
        except Exception as e:
            pass

    def destroyedByUser(self):
        self.txt = None
        self.destroy()
        if(self.destroy_callback):
            self.destroy_callback()

##     ## ######## ##     ##     ######  ##     ## ########  ######  ##    ##
###   ### ##       ###   ###    ##    ## ##     ## ##       ##    ## ##   ##
#### #### ##       #### ####    ##       ##     ## ##       ##       ##  ##
## ### ## ######   ## ### ##    ##       ######### ######   ##       #####
##     ## ##       ##     ##    ##       ##     ## ##       ##       ##  ##
##     ## ##       ##     ##    ##    ## ##     ## ##       ##    ## ##   ##
##     ## ######## ##     ##     ######  ##     ## ########  ######  ##    ##

class MemCheckWidget(object):
    """docstring for MemCheckWidget"""

    def __init__(self, wispRam, title = "", destroy_callback = None):
        super(MemCheckWidget, self).__init__()
        memchecks = wispRam.memChecks
        self.setMemCheckTarget([memchecks[x]["length"] for x in sorted(memchecks)])
        self.addresses = [h2i(x) for x in sorted(memchecks)]
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.destroyedByUser)
        self.destroy_callback = destroy_callback
        # self.root.focus()
        self.root.title(wispRam.ID+ ": " + title)
        self.root.geometry('+%d-%d' % ( 20, 20))
        text_w = min(max(self.plot_y_target), 250)+5
        text_h = sum(len([y for y in self.plot_y_target if y>i*220]) for i in range(10))+2
        self.txt = Text(self.root,width= text_w,height= text_h)
        self.txt.pack(fill= BOTH, expand = True)
        for x in range(len(self.plot_y_target)):
            self.txt.insert(INSERT,i2h(self.addresses[x])+" " +"?"*self.plot_y_target[x]+"\n")

    def setMemCheckTarget(self, line_widths):
        self.plot_y_target = line_widths

    def getLineNumber(self, address):
        for a in range(len(self.addresses))[::-1]:
            if(address >= self.addresses[a]):
                return a
        else:
            raise NameError('Address' + i2h(address) + ' not found in {}'.format(' '.join([i2h(x) for x in self.addresses])))

    def getOffsetInWords(self, address):
        return (address - self.addresses[self.getLineNumber(address)])/2 + 5

    def ack(self,address,size_in_words):
        linenumber = self.getLineNumber(address)
        begin = "%i.%i"%(linenumber+1,self.getOffsetInWords(address))
        eind = "%i.%i"%(linenumber+1,self.getOffsetInWords(address) + size_in_words)
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"$"*size_in_words)
            tag = "ack{}".format(random.choice("abcdefghijklmnopqrstuvwxyz"))
            self.txt.tag_add(tag, begin, eind)
            self.txt.tag_config(tag, background="green", foreground="black")

    def nack(self,address,size_in_words):
        linenumber = self.getLineNumber(address)
        begin = "%i.%i"%(linenumber+1,self.getOffsetInWords(address))
        eind = "%i.%i"%(linenumber+1,self.getOffsetInWords(address) + size_in_words)
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"0"*size_in_words)
            tag = "nack{}".format(random.choice("abcdefghijklmnopqrstuvwxyz"))
            self.txt.tag_add(tag, begin, eind)
            self.txt.tag_config(tag, background="red", foreground="white")


    def chop(self,address,size_in_words):
        linenumber = self.getLineNumber(address)
        begin = "%i.%i"%(linenumber+1,self.getOffsetInWords(address))
        eind = "%i.%i"%(linenumber+1,self.getOffsetInWords(address) + size_in_words)
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"-"*size_in_words)
            tag = "chop{}".format(random.choice("abcdefghijklmnopqrstuvwxyz"))
            self.txt.tag_add(tag, begin, eind)
            self.txt.tag_config(tag, background="brown", foreground="white")

    def dontcare(self,address,size_in_words):
        linenumber = self.getLineNumber(address)
        begin = "%i.%i"%(linenumber+1,self.getOffsetInWords(address))
        eind = "%i.%i"%(linenumber+1,self.getOffsetInWords(address) + size_in_words)
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"F"*size_in_words)
            tag = "dontcare{}".format(random.choice("abcdefghijklmnopqrstuvwxyz"))
            self.txt.tag_add(tag, begin, eind)
            self.txt.tag_config(tag, background="black", foreground="white")

    def send(self,address,size_in_words):
        linenumber = self.getLineNumber(address)
        begin = "%i.%i"%(linenumber+1,self.getOffsetInWords(address))
        eind = "%i.%i"%(linenumber+1,self.getOffsetInWords(address) + size_in_words)
        if(self.txt):
            self.txt.delete(begin,eind)
            self.txt.insert(begin,"?"*size_in_words)
            tag = "sended{}".format(random.choice("abcdefghijklmnopqrstuvwxyz"))
            self.txt.tag_add(tag, begin, eind)
            self.txt.tag_config(tag, background="yellow", foreground="black")

    def destroy(self):
        try:
            self.root.destroy()
        except Exception as e:
            pass

    def destroyedByUser(self):
        self.txt = None
        if(self.destroy_callback):
            self.destroy_callback()
        self.destroy()

#### ##    ## ##     ## ######## ##    ## ########  #######  ########  ##    ##
 ##  ###   ## ##     ## ##       ###   ##    ##    ##     ## ##     ##  ##  ##
 ##  ####  ## ##     ## ##       ####  ##    ##    ##     ## ##     ##   ####
 ##  ## ## ## ##     ## ######   ## ## ##    ##    ##     ## ########     ##
 ##  ##  ####  ##   ##  ##       ##  ####    ##    ##     ## ##   ##      ##
 ##  ##   ###   ## ##   ##       ##   ###    ##    ##     ## ##    ##     ##
#### ##    ##    ###    ######## ##    ##    ##     #######  ##     ##    ##

class InventoryWidget(object):
    """docstring for InventoryWidget"""
    def __init__(self, root, text_w = 250, text_h = 20):
        super(InventoryWidget, self).__init__()
        self.taglist = dict()
        self.txt = Text(root,width= text_w,height= text_h)
        self.txt.pack(side=LEFT, fill=BOTH, expand=True)
        self.S = Scrollbar(root)
        self.S.pack(side=RIGHT, fill=Y)
        self.S.config(command=self.txt.yview)
        self.txt.config(yscrollcommand=self.S.set)
        self.updatetxt("no tags seen yet")

    def updatetxt(self, text):
        if(self.txt):
            self.txt.delete("1.0",END)
            self.txt.insert(INSERT,text)
            self.txt.update_idletasks()

    def showTagsInTextWidget(self, tags, EPCLength = 8):
        updatespeed = 0.2
        epcs_this_round = set()
        if len(tags):
            for tag in tags:
                epc = tag['EPC-96'][0:min(8,EPCLength)]
                epc += ('----' + tag['EPC-96'][5*4:6*4]) if EPCLength ==6*4 else ''
                if epc not in self.taglist:
                    self.taglist[epc] = tag['TagSeenCount'][0]
                self.taglist[epc] += tag['TagSeenCount'][0]*updatespeed - self.taglist[epc]*updatespeed
                epcs_this_round |= set({epc})

        for tagepc in epcs_this_round ^ set( self.taglist.keys() ):
            self.taglist[tagepc] *=1-updatespeed

        text = " Tag epc "+ ' '*max(EPCLength-8,0)+"|   visibility   \n"
        for tag in self.taglist:
            text += tag+ (" | %5.2f "%self.taglist[tag]) + 'x'*int(2*self.taglist[tag])+"\n"
        self.updatetxt(text)

    def getBestTag(self):
        for tag in self.taglist:
            if (self.taglist[tag] == max(self.taglist.values())):
                return tag
        else:
            return None

    def getGoodTags(self, threshold = 1.0):
        return set([tag[:4] for tag in self.taglist if self.taglist[tag]>threshold])

    def destroy(self):
        if(self.txt):
            self.txt.destroy()
            self.txt= None

##      ## ########  ######## ########
##  ##  ## ##     ## ##       ##     ##
##  ##  ## ##     ## ##       ##     ##
##  ##  ## ########  ######   ########
##  ##  ## ##   ##   ##       ##
##  ##  ## ##    ##  ##       ##
 ###  ###  ##     ## ######## ##

class WrepWidget(object):
    """docstring for WrepWidget"""
    PAST    = -1 # to say this state (button) has been active before
    FUTURE  =  0 # to say this state (button) has not been active before
    CURRENT =  1 # to say this state (button) is active now
    def __init__(self,wispstates_LOT, destroy_callback = None):
        super(WrepWidget, self).__init__()
        self.wispstates_LOT = wispstates_LOT
        self.destroy_callback = destroy_callback
        self.wwindow = Tk()
        self.wisprows = dict()
        self.wwindow.protocol("WM_DELETE_WINDOW", self.destroyedByUser) # do something if user closes the window
        self.wwindow.geometry('-%d+%d' % ( 20, 50))

    def addWisp(self,wisp):
        wisprow = Frame(self.wwindow)
        self.labelt = Label(wisprow, text=' WISP: ' + wisp.ID+ " ")
        self.labelt.pack(side=LEFT)
        wisprow.wispstatebuttons = []
        for state in wisp.getStates():
            txt = self.wispstates_LOT[state]
            wisprow.wispstatebuttons.append({'button' : Button(wisprow, text=txt), 'state': state, 'active': self.FUTURE,})
            wisprow.wispstatebuttons[-1]['button'].pack(side=LEFT)

        wisprow.pack(fill=X)
        self.wisprows[wisp.ID] = wisprow

    def setState(self, wispID, newState, time):
        if(self.wwindow):
            # reset old coloring
            for WSB in self.wisprows[wispID].wispstatebuttons:
                if WSB['active'] is self.CURRENT :
                    WSB['button'].configure(bg = 'forest green')
                    WSB['active'] = self.PAST
            # catch the current state
            # difficulty: states are not unique, so find out which of them is the next.
            # solution: pick the first 'clean' one (button without past activity) or the last one
            for WSB in self.wisprows[wispID].wispstatebuttons:
                if WSB['state'] is newState:
                    if WSB['active'] is self.PAST:
                        selected_button = WSB
                    else:
                        WSB['button'].configure(bg = 'red2')
                        b_text = WSB['button'].config('text')[-1]
                        WSB['button'].config(text=b_text+ "\n%2.3f"%(time))
                        WSB['active'] = self.CURRENT
                        break # don't check any next buttons anymore
            else: # if there was no break in the for loop, execute this
                selected_button['button'].configure(bg = 'red2')
                b_text = selected_button['button'].config('text')[-1]
                selected_button['button'].config(text=b_text+ "\n%2.3f"%(time))
                selected_button['active'] = self.CURRENT
            self.wwindow.update_idletasks()
            # self.wwindow.focus()

    # fetch the widget tekst for a specific wispID
    def toString(self, wispID):
        # get the buttons, join with '\n', but first flatten out the button txt ( = replace '\n' with ' ')
        # last step: wrap into brackets and attach 'WrepWidget '-txt
        return "WrepWidget [" +', '.join( [(' '.join(WSB['button'].config('text')[-1].split('\n'))) for WSB in self.wisprows[wispID].wispstatebuttons]) + "]"

    def destroy(self):
        try:
            self.wwindow.destroy()
        except Exception as e:
            pass

    def destroyedByUser(self):
        if(self.destroy_callback):
            self.destroy_callback()
        self.destroy()
        self.wwindow = None

         ######   #######  ##    ## ######## ########   #######  ##
       ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##
      ##       ##     ## ####  ##    ##    ##     ## ##     ## ##
     ##       ##     ## ## ## ##    ##    ########  ##     ## ##
    ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##
   ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##
   ######   #######  ##    ##    ##    ##     ##  #######  ########

class IOControlWidget(object):
    """docstring for IOControlWidget"""
    def __init__(self, buttonlist, optionlist, destroy_callback, terminal_callback, pause_callback, buttoncolors = {}):
        super(IOControlWidget, self).__init__()
        self.destroy_callback = destroy_callback
        self.terminal_callback = terminal_callback
        self.pause_callback = pause_callback
        self.optionlist        = optionlist

        self.io = Tk()
        self.io.protocol("WM_DELETE_WINDOW", self.destroy) # do something if user closes the window
        # self.io.focus()
        self.io.title("hahahaha :D")
        self.IOF = tkFont.nametofont("TkFixedFont")

        # setup a list of buttons
        self.buttoncollumn = Frame(self.io)
        self.buttons = {key:Button(self.buttoncollumn, text=key[2:], command=buttonlist[key],font=self.IOF) for key in sorted(buttonlist)}
        [self.buttons[b].pack(fill = X) for b in sorted(self.buttons.keys())]
        [self.buttons[key].config(bg = buttoncolors[key][0],fg = buttoncolors[key][1]) for key in sorted(buttoncolors)]
        self.buttoncollumn.pack(side = LEFT,fill = X,padx = 10,pady = 10)

        # setup a list of options
        self.optioncollumn = Frame(self.io)
        self.selected_option = {key[2:]: StringVar() for key in sorted(optionlist)} # not using the first 2 characters of the key, for refering to the selected option
        [self.selected_option[key[2:]].set(optionlist[key][0]) for key in sorted(optionlist)] # not using the first 2 characters of the key, for refering to the selected option
        self.optionrows = {key:Frame(self.optioncollumn) for key in sorted(optionlist)}
        self.optionlabels = {key:Label(self.optionrows[key], text= key[2:],font=self.IOF) for key in sorted(optionlist)}
        self.options = {key:OptionMenu(self.optionrows[key],self.selected_option[key[2:]], *optionlist[key]) for key in sorted(optionlist)} # not using the first 2 characters of the key, for refering to the selected option
        [self.options[o].pack(side = RIGHT,fill = BOTH,padx = 20) for o in sorted(self.options)]
        [self.options[o].config( bg = "grey55") for o in sorted(self.options)]
        [o.pack(side = LEFT, fill = BOTH) for o in self.optionlabels.values()]
        [self.optionrows[key].pack(fill = X, padx = 5) for key in sorted(self.optionrows)]
        self.optioncollumn.pack(side = LEFT)

        self.terminalrow = Frame(self.io)
        self.terminal_label = Label(self.terminalrow, text= "WISPTERM",font=self.IOF, bg = "dim gray")
        self.terminal_label.pack(side = LEFT,padx = 5, pady = 5)
        self.terminal = Entry(self.terminalrow,width= 50)
        self.terminal.pack(fill = X,expand = True, padx = 5, pady = 5)
        self.terminal.bind('<Return>', self.terminalInput)
        self.terminal.bind('<KP_Enter>', self.terminalInput)
        self.terminalrow.pack(fill= BOTH)
        self.terminalrow.config(bg = "dim gray", padx = 5)

        self.txt = Text(self.io,width= 100, height = 10)
        self.S = Scrollbar(self.io)
        self.S.pack(side=RIGHT, fill=Y)
        self.S.config(command=self.txt.yview)
        self.txt.config(yscrollcommand=self.S.set)
        self.txt.pack(fill = BOTH,expand = True)
        self.updatetxt("Initializing")

        self.wispsrow = Frame(self.io)
        self.wispsselection = Frame(self.wispsrow)
        self.wisp_selection_label = Label(self.wispsselection, text= "Select Targets",bg = "dark green", fg = "white")
        self.wisp_selection_label.pack(fill = BOTH, expand = True)
        self.wisplist = Listbox(self.wispsselection,selectmode=EXTENDED,height= 5)
        self.wisplist.config(width = 16)
        self.wisplist.pack(fill = Y, expand = True)
        self.setWispSelection(["0302"])
        self.pause_button = Button(self.wispsselection, text="PAUSE", command=self.pauseButtonPressed,font=self.IOF, fg = 'white',bg = "dark green")
        self.pause_button.pack(fill = X, padx = 3, pady = 3)
        self.wispsselection.pack(side = LEFT, fill = Y,pady = 5, padx = 5)

        self.tagWidget = InventoryWidget(self.wispsrow, 100, 12)
        self.wispsrow.pack(fill = BOTH)
        self.wispsrow.config(bg = "dark green")

    def pauseButtonPressed(self):
        if(self.pause_button.config('text')[-1] == "PAUSE"):
            self.pause_callback(pause = True)
            self.pause_button.config(text = "RESUME")
        else:
            self.pause_callback(resume = True)
            self.pause_button.config(text = "PAUSE")

    # add a new option to the option list
    def addAndSetOption(self, om_key, new_option):
        if om_key in self.options:
            if(new_option not in self.optionlist[om_key]):
                self.options[om_key]["menu"].add_command(label = new_option, command = lambda value=new_option:self.selected_option[om_key[2:]].set(value))
                self.optionlist[om_key].append(new_option)
            self.selected_option[om_key[2:]].set(new_option)
        else:
            self.showWarning("Unknown list to add the option to!")

    def updatetxt(self, text, mode = 'replace'):
        if(mode == 'replace'):
            self.txt.delete("1.0",END)
        self.txt.insert(INSERT,text)
        logger.info('IOTXT'+ mode+': ' + text)

    def showWarning(self, text, mode = 'replace'):
        if(mode == 'replace'):
            self.txt.delete("1.0",END)
        self.txt.insert(INSERT,text)
        self.txt.tag_add('warning', "1.0",INSERT)
        self.txt.tag_config('warning', background="red", foreground="white")
        logger.info('\033[1;31mIOTXT-WARNING: ' + text + '\033[1;0m')

    def deletetxt(self, nr_of_chars):
        for x in range(nr_of_chars):
            self.txt.delete(INSERT)

    def setWispSelection(self, selection):

        for item in selection:
            if(item not in self.wisplist.get(0,END)):
                self.wisplist.insert(0, item)
        for index in range(len(self.wisplist.get(0,END))):
            if(self.wisplist.get(index) in selection):
                self.wisplist.selection_set(index)
            else:
                self.wisplist.selection_clear(index)

    def getSelectedWispIDs(self):
        return [self.wisplist.get(int(x)) for x in self.wisplist.curselection()]

    def getSelected(self, key): # give the key without the [number/hex/char] and space (= without the first 2 characters)
        return self.selected_option[key].get()

    def terminalInput(self, key):
        if self.terminal_callback:
            userinput = self.terminal.get()
            if(userinput):
                if(userinput[-1:].lower() in {'x','q','c'}):
                    # clear terminal if user types something rubbish
                    self.terminal.delete(0, END)
                elif(userinput[-1:].lower() in {'\\',';'}):
                    # clear the terminal if user ends a command properly
                    self.terminal.delete(0, END)
                    # try to execute the command
                    self.terminal_callback(command = userinput[:-1])
                else:
                    # try to execute the command, don't clear the terminal
                    self.terminal_callback(command = userinput)

    def update(self):
        if(self.io):
            self.io.update()
            return True

    def destroy(self):
        self.tagWidget.destroy()
        self.io.destroy()
        self.io = None
        self.destroy_callback()
