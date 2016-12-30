from __future__ import print_function
import argparse
import logging
import pprint
import time
from twisted.internet import reactor, defer
from sllurp.WWidgets import InventoryWidget
from Tkinter import *

import sllurp.llrp as llrp
from sllurp.llrp_proto import Modulation_Name2Type, DEFAULT_MODULATION, \
     Modulation_DefaultTari

numTags = 0
logger = logging.getLogger('sllurp')

args = None

def finish (_):
    # show the last statistics
    logger.info('total # of tags seen: {}'.format(numTags))
    if reactor.running:
        reactor.stop()

def politeShutdown (factory):
    return factory.politeShutdown()

def getCostumOpspecs(): # just some random operations that can be performed on the wisp

    writeSpecParam = {
        'OpSpecID': 1,
        'MB': 1,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WriteDataWordCount': 30,
        'WriteData': '\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc\xde\xad\xbe\xef\xaa\xaa\xbb\xbb\xcc\xcc', # XXX allow user-defined pattern
    }

    readSpecParam = {
        'OpSpecID': 2,
        'MB': 3,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WordCount': 9,
    }

    writeSpecParam2 = {
        'OpSpecID': 3,
        'MB': 3,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WriteDataWordCount': 32,
        'WriteData': '\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00\x11\x22\x33\x44', # XXX allow user-defined pattern
    }
    data = "003464500000000000000000000000000000000000000001000000010000000100000001000000010000000100000001000000010000000100000001"
    writeSpecParam3 = {
        'OpSpecID': 3,
        'MB': 1,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WriteDataWordCount': 31,
        'WriteData': ("1d"+calcChecksum(data)+data).decode("hex")
    }
    data = "203464500000000000000000000000000000000000000001000000010000000100000001000000010000000100000001000000010000000100000001"
    writeSpecParam4 = {
        'OpSpecID': 5,
        'MB': 3,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WriteDataWordCount': 31,
        'WriteData': ("1d"+calcChecksum(data)+data).decode("hex")
    }

    readSpecParam2 = {
        'OpSpecID': 4,
        'MB': 3,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WordCount': 9
    }
    return [writeSpecParam]

def calcChecksum(stork_message):
    checksum = 0
    for i in range(0, len(stork_message),2):
        checksum += int("0x"+ stork_message[i:i+2], 0)
    checksum = checksum % 256
    return "{:02x}".format(checksum)

def access (proto):
    return fac.nextAccessSpec(opSpecs = getCostumOpspecs(),
        accessSpec = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 1, 'OperationCountValue': 4,},})

def tagReportCallback (llrpMsg):
    """Function to run each time the reader reports seeing tags."""
    global numTags
    tags = llrpMsg.msgdict['RO_ACCESS_REPORT']['TagReportData']

    # show results
    if len(tags):
        for tag in tags:
            logger.info('saw tag(s): epc = %s #seen: %s'%(tag['EPC-96'],tag['TagSeenCount'][0]))
            logger.info('result {}'.format(tag['OpSpecResult']))

    else:
        logger.info('no tags seen')

    for tag in tags:
        numTags += tag['TagSeenCount'][0]

    # call a function from Wwidgets.py to show the tags in a seperate screen
    inventoryWidget.showTagsInTextWidget(tags)

def parse_args ():
    global args
    parser = argparse.ArgumentParser(description='Simple RFID Reader Inventory')
    parser.add_argument('host', help='hostname or IP address of RFID reader',  nargs='+')
    parser.add_argument('-p', '--port', default=llrp.LLRP_PORT, type=int,  help='port to connect to (default {})'.format(llrp.LLRP_PORT))
    parser.add_argument('-t', '--time', type=float,  help='number of seconds for which to inventory (default forever)')
    parser.add_argument('-d', '--debug', action='store_true',  help='show debugging output')
    parser.add_argument('-n', '--report-every-n-tags', default=1, type=int,   dest='every_n', metavar='N', help='issue a TagReport every N tags')
    parser.add_argument('-a', '--antennas', default='1', help='comma-separated list of antennas to enable (0=all; '\
                'default 1)')
    parser.add_argument('-X', '--tx-power', default=0, type=int, dest='tx_power', help='transmit power (default 0=max power)')
    mods = sorted(Modulation_Name2Type.keys())
    parser.add_argument('-M', '--modulation', default=DEFAULT_MODULATION,  choices=mods, help='modulation (default={})'.format(\
                DEFAULT_MODULATION))
    parser.add_argument('-T', '--tari', default=0, type=int,  help='Tari value (default 0=auto)')
    parser.add_argument('-s', '--session', default=2, type=int,  help='Gen2 session (default 2)')
    parser.add_argument('-P', '--tag-population', default=4, type=int,  dest='population', help="Tag Population value (default 4)")
    parser.add_argument('-l', '--logfile')
    parser.add_argument('-r', '--reconnect', action='store_true', default=False, help='reconnect on connection failure or loss')
    parser.add_argument('-m', '--message',nargs= '*',help='the message that you want to send')
    parser.add_argument('-mf', '--send_message_forever', action='store_true', default=False, help='Send the message forever, instead of just once')
    args = parser.parse_args()

# set logging parameters
def init_logging ():
    logLevel = (args.debug and logging.DEBUG or logging.INFO)
    logFormat = '%(asctime)s %(name)s: %(levelname)s: %(message)s'
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

    logger.log(logLevel, 'log level: {}'.format(logging.getLevelName(logLevel)))

# with this function you can send exactly 1 accessspec
def sendMessage(proto = ""):
    llrp_message = []
    opSpecID = 1
    for m in args.message:
        llrp_message.append({
            'OpSpecID': opSpecID,
            'MB': 3,
            'WordPtr': 0,
            'AccessPassword': 0,
            'WriteDataWordCount': len(m)/4,
            'WriteData': m.decode('hex'),
        })
        opSpecID+=1
    if(args.send_message_forever):
        fac.nextAccessSpec(opSpecs = llrp_message,
                accessSpec = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 0, 'OperationCountValue': 5,},})
    else:
        fac.nextAccessSpec(opSpecs = llrp_message,
                accessSpec = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 1, 'OperationCountValue': 2560,},})
def main ():
    global fac, inventoryWidget
    parse_args()
    init_logging()
    inventoryWidget =InventoryWidget(Tk()) # function from wWidget.py


    # special case default Tari values
    if args.modulation in Modulation_DefaultTari:
        t_suggested = Modulation_DefaultTari[args.modulation]
        if args.tari:
            logger.warn('recommended Tari for {} is {}'.format(args.modulation,
                        t_suggested))
        else:
            args.tari = t_suggested
            logger.info('selected recommended Tari of {} for {}'.format(args.tari,
                        args.modulation))

    enabled_antennas = map(lambda x: int(x.strip()), args.antennas.split(','))


    # d.callback will be called when all connections have terminated normally.
    # use d.addCallback(<callable>) to define end-of-program behavior.
    d = defer.Deferred()
    d.addCallback(finish)

    fac = llrp.LLRPClientFactory(onFinish=d,
            duration=args.time,
            report_every_n_tags=args.every_n,
            antennas=enabled_antennas,
            tx_power=args.tx_power,
            modulation=args.modulation,
            tari=args.tari,
            session=args.session,
            tag_population= int(32),
            start_inventory=True,
            disconnect_when_done=(args.time > 0),
            reconnect=args.reconnect,
            tag_content_selector={
                'EnableROSpecID': False,
                'EnableSpecIndex': False,
                'EnableInventoryParameterSpecID': False,
                'EnableAntennaID': True,
                'EnableChannelIndex': False,
                'EnablePeakRRSI': True,
                'EnableFirstSeenTimestamp': False,
                'EnableLastSeenTimestamp': True,
                'EnableTagSeenCount': True,
                'EnableAccessSpecID': False
            })

    # tagReportCallback will be called every time the reader sends a TagReport
    # message (i.e., when it has "seen" tags).
    fac.addTagReportCallback(tagReportCallback)

    # if the user defined a message for the wisp, then send this (block)write message
    if(args.message):
        fac.addStateCallback(llrp.LLRPClient.STATE_INVENTORYING, sendMessage)

    # listen to tcp (llrp) messages
    for host in args.host:
        reactor.connectTCP(host, args.port, fac, timeout=3)

    # catch ctrl-C and stop inventory before disconnecting
    reactor.addSystemEventTrigger('before', 'shutdown', politeShutdown, fac)

    reactor.run()

if __name__ == '__main__':
    main()
