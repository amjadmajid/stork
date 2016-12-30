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
from math import log, ceil
from twisted.internet import reactor
from WModules import h2i, i2h, OpSpecCreator
from WControlModules import wrapHexLines
from WWidgets import MemCheckWidget

# Simple usage:
# from wispRam import perfectWispMemory
# w = perfectWispMemory(filename = "../ihex/ccs1.hex", prepare_mem_checks = False)
# to get mem: w.getMem(address= 0x6400, length_in_words = 32)

# Memcheck with CRC usage:
# w = perfectWispMemory(send_util = AccessSpecFactory(....), ID4hex = '0303',filename = "../ihex/ccs1.hex")
# w.start(finished_callback = your_callback_function)
# when memory check is finished the callback will be call with parameter True if all memchecks are good or false if not, second parameter will be the object itself (module = self).

logger = logging.getLogger(__name__)


class PerfectWispMemory(object):
    """docstring for PerfectWispMemory"""

    MEMCHECKMAXSIZE = 256
    MEMCHECKMINSIZE = 8
    MINMEM = 0x1800
    MAXMEM = 0x10000
    sf = 8

    def __init__(self, send_util =None,ID4hex =None, filename = None, hexlines = None, prepare_mem_checks = True ):
        super(PerfectWispMemory, self).__init__()
        if(filename):
            self.memInit(open(filename, "r").readlines())
        elif(hexlines):
            self.memInit(hexlines)
        else:
            raise NameError('What do you want me to check?')
        if(prepare_mem_checks):
            self.ID = ID4hex
            self.send_util = send_util
            self.localizeMemBlocks()
            self.defineMemChecks()
        self.start_time = time.time()

    # initialize the wisp memory with memory lines from a hex file
    def memInit(self,memlines):
        self.memory = "FF"*(self.MAXMEM-self.MINMEM) # init with all "ff", all ones, just as untouched wisp memory
        # insert all known memory parts:
        for line in memlines:
            if(line[7:9] == "00"): # check if this line is a normal memory line (instead of: an end-of-file-line)
                # decompose hexline in parts
                am = self.convertAddr2myMem(h2i(line[3:7])) # address of memory
                dm = line[9:-3] # data of memory
                lm = len(dm) # lenght of data of memory

                memleft = self.memory[:am]
                memright = self.memory[am+lm:]
                self.memory = memleft+dm+memright
        #print self.memory

    # this function localizes the interesting (= non-empty) memory blocks in the perfect Wisp
    # this is used to determine which parts of the real wisp we need to check
    # WARNING: assume that all mem that is FFFFFFFFF etc is not important
    # this means that you can not do a memcheck on empty memory!
    def localizeMemBlocks(self):
        self.startAddresses=dict()
        lastAddress = -1 # start of the current memory block
        holecounter = 10 # length of the not interesting memory, which is used for hysteresis
        for w in range(self.MINMEM, self.MAXMEM,2):
            if(self.getMem(w,1)!="FFFF" or holecounter < 2): # check if this is interesting or if previous 2 blocks where interesting
                if(lastAddress == -1): # check if this is the first word of an interesting block
                    lastAddress = i2h(w)
                    self.startAddresses[lastAddress] = 1
                else:
                    self.startAddresses[lastAddress]+=1

                if(self.getMem(w,1)!="FFFF"):
                    holecounter = 0
                else:
                    holecounter+=1
            else:
                lastAddress = -1
                holecounter+=1
        for x in self.startAddresses:
            self.startAddresses[x] -=2 # reduce by 2 because that is the window of the stop condition

    # function that creates a list of crc of interesting memory parts
    def defineMemChecks(self,MLM = MEMCHECKMAXSIZE):
        memCheckAddresses = dict()
        # first chop very long data chuncks in smaller parts
        for addr in self.startAddresses:
            length =  self.startAddresses[addr]
            checkaddress = h2i(addr)
            while(length>0):
                if(length> MLM):
                    memCheckAddresses[i2h(checkaddress)] = MLM
                    checkaddress += 2* MLM # MLM is in words, address is in bytes
                else:
                    # do some math magic to ceil to the nearest factor of 2 (crc must be factor of 2)
                    memCheckAddresses[i2h(checkaddress)] = max(int(pow(2,ceil(log(length,2)))),16)
                length-=MLM
        self.mcas = memCheckAddresses
        logger.debug("{}".format(pprint.pformat(self.mcas)))
        # get a list of expected CRC results per small chunck of data
        self.memChecks = dict()
        self.memIsGood = dict()
        self.memIsBad  = dict()
        for mca in self.mcas:
            # check CRC of this block in 4 subparts
            self.memChecks[mca] = {"crcs": #"{:04x}{:04x}{:04x}{:04x}".format(self.getCRC(address = h2i(mca),                     nr_of_words = self.mcas[mca]/4),
                                            #                                self.getCRC(address = h2i(mca)+self.mcas[mca]/2   , nr_of_words = self.mcas[mca]/4),
                                                                            # self.getCRC(address = h2i(mca)+self.mcas[mca]/2 *2, nr_of_words = self.mcas[mca]/4),
                                                                            # self.getCRC(address = h2i(mca)+self.mcas[mca]/2 *3, nr_of_words = self.mcas[mca]/4) )
                                                                            self.crcString(address = h2i(mca),nr_of_words = self.mcas[mca]),
                                    "length": self.mcas[mca],}

    def crcString(self, address, nr_of_words):
        if(nr_of_words<self.MEMCHECKMINSIZE):
            raise NameError('crc too small')
        ret = '' # this will be our return string
        crcsize = max(nr_of_words/self.sf,self.MEMCHECKMINSIZE) # this is in words and must be MINSIZE or higher  # address is in bytes
        while(nr_of_words>0):
            ret += "{:04x}".format(self.getCRC(address =address,nr_of_words = crcsize))
            address+=crcsize*2
            nr_of_words-=crcsize
        return ret

    # get a part of the memory
    def getMem(self,address, length_in_words):
        lm=length_in_words*4 # length of mem is in hex characters, hex per word = 4
        am = self.convertAddr2myMem(address)
        if(address+length_in_words*2>self.MAXMEM):
            raise NameError("address range out of bounds")
        if(length_in_words<1):
            raise NameError("Nothing to give you! addr = {}, length = {}".format(address,length_in_words))
        return self.memory[am:am+lm]


    # feed it an real world integer address and get the perfectWispMemory address
    def convertAddr2myMem(self,address):
        if(address<self.MINMEM or address>self.MAXMEM):
            raise NameError("address "+hex(address)+" out of bounds")
        return (address-self.MINMEM)*2

    def getCRC(self,address, nr_of_words):
        crc = self.crcWords(0, self.getMem(address,nr_of_words))
        if(crc == self.crcWords(0, "FFFF"*nr_of_words) and self.getMem(address,nr_of_words) != "FFFF"*nr_of_words):
            logger.info("WARNING: crc of address " + i2h(address)+ " is equal to empty 'FFFF' mem crc of equal amount of words "+ str(nr_of_words))
        return crc

    # CRC16, poly = 0x1021
    # Input: crc=integer, data = string of 2 hexadecimal
    # Crc module in wisp is designed for old computer architectures, so MSB is in bit position 0
    # That is why we need to invert the data before feeding it in the software module
    def crcByte(self, crc, data):
        crc^=0xffff                                    # invert initial crc for the crc module
        data = h2i(data)                       # convert hex-string to integer
        x = (crc >> 8) ^ data                            # do some magic
        x ^= x >> 4                                       # do some magic
        crc = (crc << 8) ^ (x << 12) ^ (x << 5) ^ (x)  # do some magic
        return (crc & 0xffff)^0xFFFF                   # invert it back to leave the crc module

    # CRC16, poly = 0x1021
    # Input: seed=initial state (integer), data = crc input (string of 2*X hexadecimal)
    def crcWords(self, seed, data):
        result = seed
        while(len(data)):
            result = self.crcByte(result,data[0:2])
            data= data[2:]
        return result

    def start(self, finished_callback, destroy_windows_after_Xsec_when_finished = None):
        self.callback = finished_callback
        self.start_time = time.time()
        self.destroy_windows_after_Xsec_when_finished = destroy_windows_after_Xsec_when_finished
        self.memcheck_widget = MemCheckWidget(wispRam = self, destroy_callback = self.iAmCanceled)
        self.nextRound()


    def nextRound(self):
        counter = 0
        for addr in self.memChecks:
            this = self.memChecks[addr]
            resultpos = log(max(this["length"]/self.sf,self.MEMCHECKMINSIZE)  /2,2) # 16 should be 1 (if wisp receives 1 then it will translate to X blocks of 2<<1 =4),
                        # 32 should be 2 (if wisp receives 2 then it will translate to X blocks of 2<<2 =8), etc
            if(resultpos.is_integer()):
                resultpos = int(resultpos)
            else:
                raise NameError("trying to do a CRC with strange number "+str(this["length"])+ " = not 16*2^x for integer x > -1")
            checksum = i2h((h2i(addr[0:2])+h2i(addr[2:4]))%256,2) # calc checksum
            message = i2h(resultpos *32,2)+checksum + addr # *32 == shift by 5
            logger.info(self.ID + ": sending memcheck [" + message + "], expecting CRCs = " + this["crcs"])
            self.memcheck_widget.send(address = h2i(addr), size_in_words = this["length"])
            self.send_util.addOpspec(OpSpecCreator.getBlockWrite(message))
            nr_to_read = 1+min(self.sf,this["length"]/self.MEMCHECKMINSIZE)
            self.send_util.addOpspec(OpSpecCreator.getRead(mb = 3,address = 0,nr_of_words = nr_to_read))
            counter += 1
            if counter==4 :
                break

        if(len(self.send_util.opspecs)):
            self.send_util.sendOpspecs(OCV = 1, nack = self.timeout)
        else:
            logger.info(self.ID+": memcheck finished")
            logger.info(self.ID+": " + str(len(self.memIsGood))+ " good and "+ str(len(self.memIsBad))+" bad memblocks")

            self.iAmFinished()

    def timeout(self):
        logger.debug("\033[1;31mMEMCHECK TIMEOUT\033[1;0m")
        self.nextRound()

    def handleMessage(self, opspecs, epc):
        opspecs = {x:opspecs[x] for x in opspecs if (opspecs[x]["Result"] == 0) } # get all successive opspecresults
        opspecs = {x:opspecs[x] for x in opspecs if "ReadData" in opspecs[x] } # get all read opspecs

        nr_of_acks = 0
        for ops in opspecs.values():
            data = ops["ReadData"]
            if(self.checkCRC(addr = data[0:4],crcs= data[4:])):
                nr_of_acks += 1


        if(nr_of_acks>0):
            self.send_util.stopTimerSuccesCheck()
            self.nextRound()

        else:
            logger.debug(self.ID +": useless round: you should retry now")

    # this function checks the CRCs and
    def checkCRC(self, addr, crcs):
        if (addr in self.memChecks):
            this = self.memChecks[addr]
            logger.info("{} ?= {}".format(this["crcs"], crcs))
            crcsize_words = max(this["length"]/self.sf, self.MEMCHECKMINSIZE)
            addr_offset = 2 * crcsize_words # "*2" because addr is in bytes and the rest is in words, length/4 because we ack one/fourth of the total message
            for x in range(len(crcs)/4 -1,-1,-1):
                if (this["crcs"][x*4:x*4+4] == crcs[x*4:x*4+4]): # each CRC is 4 characters long
                    # good :) wisp has good data in this part
                    self.memcheck_widget.ack(h2i(addr) + x*addr_offset, crcsize_words)
                    self.memIsGood[i2h( h2i(addr) + x*addr_offset)] = crcsize_words # store the good stuff
                    logger.debug(i2h( h2i(addr) + x*addr_offset) + " = good")
                else:
                    # do something with a bad crc:
                    self.badCRC(address = h2i(addr) + addr_offset*x,
                                length = crcsize_words)

            if(addr in self.memIsBad or addr in self.memIsGood):
                del self.memChecks[addr]
            return True
        return False

    def badCRC(self, address, length):
        # bad :( wisp has bad data in this quarterpart
        # if the data chunck was large, try CRC over smaller data chuncks:
        if(not self.addChoppedMemCheck(address, length )):
            # data chunck was already small:
            # check if target memory was actually interesting:
            if(not all(x == "F" for x in self.getMem(address, length))):
                self.memcheck_widget.nack(address, length)
                self.memIsBad[i2h(address )] = length # store the bad stuff
                logger.debug(i2h(address) + " = bad, must be reprogrammed, too small to chop")
            else:
                self.memcheck_widget.dontcare(address, length)
                logger.debug(i2h(address) + " = bad, don't care, only 'F'")
                self.memIsGood[i2h( address )] = length # store the don't care stuff as good
                # because this part is not important, the target only contains F"s
        else:
            self.memcheck_widget.chop(address, length)
            logger.debug(i2h(address) + " = bad, chopped to check in smaller chunks")

    # If a CRC of a large chunck of data was wrong then chop it in 4 pieces and check those seperate
    def addChoppedMemCheck(self,addr,length):
        logger.debug(i2h(addr) + " = bad -> chopping (trying;)")
        if( length <= self.MEMCHECKMINSIZE*self.sf): # if previous message was already tiny, don"t add a new smaller CRCcheck
            return False

        self.memChecks[i2h(addr)] = {
                                "crcs": self.crcString(address = addr,nr_of_words = length),
                                "length": length,
                                }
        return True

    def getLongHexLinesFromBadCRCs(self):
        lines = []
        addresses = self.memIsBad.keys()
        addresses.sort() # sort the lines such that they are in increasing order, such that hexlinewrapping is possible
                         # [warning:] sort function does sorting based upon characters, fortunately hex is also sorted as 0123456789ABCDEFabcdef

        for addr in addresses:
            mem = self.getMem(address = h2i(addr), length_in_words = self.memIsBad[addr])
            lines.append(":"+i2h(len(mem)/2,2)+addr +"00" + mem + "FF\n")
            logger.debug(self.ID + ": hexline made from bad CRCcheck: "+i2h(len(mem)/2,2)+" "+addr +"[00]" + mem + "[FF]")
        lines.append(":00000001FF\n") # add the end of file line
        return wrapHexLines(lines)

    def defineMemChecksFromHexlines(self,lines,MLM = MEMCHECKMAXSIZE):
        memCheckAddresses = dict()
        # first chop very long data chuncks in smaller parts
        for line in lines:
            length =  len(line[9:-3])/4 # in words
            checkaddress = h2i(line[3:7])
            while(length>0):
                if(length> MLM):
                    memCheckAddresses[i2h(checkaddress)] = MLM
                    checkaddress += 2* MLM # MLM is in words, address is in bytes
                else:
                    # do some math magic to ceil to the nearest factor of 2 (crc must be factor of 2)
                    memCheckAddresses[i2h(checkaddress)] = max(int(pow(2,ceil(log(length,2)))),16)
                length-=MLM
        self.mcas = memCheckAddresses
        logger.debug("new memchecks based upon hexlines: {}".format(pprint.pformat(self.mcas)))
        # get a list of expected CRC results per small chunck of data
        self.memChecks = dict()
        # do not redefine self.memIsGood = dict()
        # do redefine the memIsBad
        self.memIsBad  = dict()
        for mca in self.mcas:
            # check CRC of this block in 4 subparts
            self.memChecks[mca] = {"crcs":   self.crcString(address = h2i(mca),nr_of_words = self.mcas[mca]),
                                   "length": self.mcas[mca],}
    def stop(self):
        self.send_util.stopTimerSuccesCheck()
        try:
            self.memcheck_widget.destroy()
        except Exception as e:
            pass


    def iAmFinished(self):
        self.send_util.stopTimerSuccesCheck()
        self.memcheck_widget.root.update_idletasks()
        if(self.destroy_windows_after_Xsec_when_finished):
            reactor.callLater(self.destroy_windows_after_Xsec_when_finished, self.memcheck_widget.destroy )
        self.callback(all_memory_is_good = (len(self.memIsBad) == 0 and len(self.memChecks)==0),
                    module = self, time = time.time()-self.start_time)

    def iAmCanceled(self):
        self.send_util.stopTimerSuccesCheck()
        if(len(self.memChecks)):
            self.callback(all_memory_is_good = 'canceled',module = self)

