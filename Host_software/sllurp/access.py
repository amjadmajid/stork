from __future__ import print_function
import argparse
import logging
import pprint
import time
from twisted.internet import reactor, defer

import sllurp.llrp as llrp
from sllurp.llrp_proto import Modulation_Name2Type, DEFAULT_MODULATION, \
     Modulation_DefaultTari

tagReport = 0
logger = logging.getLogger('sllurp')

args = None
fac = None
time_start = 0

def finish (_):
    logger.info('total # of tags seen: {}'.format(tagReport))
    logger.info('Time of this function in seconds: '+str(time.time()- time_start))
    if reactor.running:
        reactor.stop()

def getCostumOpspecs():

    writeSpecParam = {
        'OpSpecID': 1,
        'MB': 3,
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
        'OpSpecID': 3,
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

    return [writeSpecParam3,readSpecParam,writeSpecParam4,readSpecParam2]


def calcChecksum(stork_message):
    checksum = 0
    for i in range(0, len(stork_message),2):
        checksum += int("0x"+ stork_message[i:i+2], 0)
    checksum = checksum % 256
    return "{:02x}".format(checksum)

def access (proto):
    global time_start
    if args.read_words:
        readSpecParam = {
            'OpSpecID': 2,
            'MB': 1, # EPC=1, Usermem = 3
            'WordPtr': 0,
            'AccessPassword': 0,
            'WordCount': args.read_words
        }
        readSpecParam3 = {
            'OpSpecID': 4,
            'MB': 3,
            'WordPtr': 0,
            'AccessPassword': 0,
            'WordCount': args.read_words
        }
        readSpecParam8 = [{
        'OpSpecID': x+1,
        'MB': 3,
        'WordPtr': 0,
        'AccessPassword': 0,
        'WordCount': args.read_words
        } for x in range(6) ]

    if args.write_words:
        if args.write_words > 1:
            write_data = '\xde\xad'*args.write_words
            writeSpecParam = {
                'OpSpecID': 1,
                'MB': 3,
                'WordPtr': 0,
                'AccessPassword': 0,
                'WriteDataWordCount': args.write_words,
                'WriteData': write_data, # XXX allow user-defined pattern
            }
            writeSpecParam2 = {
                'OpSpecID': 3,
                'MB': 3,
                'WordPtr': 0,
                'AccessPassword': 0,
                'WriteDataWordCount': args.write_words,
                'WriteData': write_data, # XXX allow user-defined pattern
            }
        else:
            writeSpecParam = {
                'OpSpecID': 1,
                'MB': 3,
                'WordPtr': 0,
                'AccessPassword': 0,
                'WriteDataWordCount': args.write_words,
                'WriteData': '\xde\xad', # XXX allow user-defined pattern
            }
            writeSpecParam2 = {
                'OpSpecID': 3,
                'MB': 3,
                'WordPtr': 0,
                'AccessPassword': 0,
                'WriteDataWordCount': args.write_words,
                'WriteData': '\x00\x00', # XXX allow user-defined pattern
            }

    if(args.read_words and not args.write_words):
        time_start = time.time()
        return proto.startAccessSpec(None ,opSpecs = readSpecParam8, # OR you could do: [readSpecParam,readSpecParam2,readSpecParam3],
                accessSpecParams = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 0, 'OperationCountValue': 5,},})

    if(args.read_words and args.write_words):
        return proto.startAccessSpec(None ,opSpecs = [writeSpecParam,readSpecParam,writeSpecParam2,readSpecParam3],
                accessSpecParams = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 0, 'OperationCountValue': 5,},})
    if(args.write_words):
        return proto.startAccess(readWords=None,
            writeWords=[writeSpecParam],accessStopParam =  {'AccessSpecStopTriggerType': 0, 'OperationCountValue': 5,})
    return fac.nextAccessSpec(opSpecs = getCostumOpspecs(),
        accessSpec = {'ID':1, 'StopParam': {'AccessSpecStopTriggerType': 1, 'OperationCountValue': 1,},})

def politeShutdown (factory):
    return factory.politeShutdown()

def tagReportCallback (llrpMsg):
    """Function to run each time the reader reports seeing tags."""
    global tagReport
    tags = llrpMsg.msgdict['RO_ACCESS_REPORT']['TagReportData']
    if len(tags):
        # logger.info('saw tag(s): {}'.format(pprint.pformat(tags)))
        for tag in tags:
            for ops in tag["OpSpecResult"]:
                logger.info("Readdata = " + tag["OpSpecResult"][ops]["ReadData"])
        if("OpSpecResult" in tags[0]):
            for ops in tags[0]["OpSpecResult"].values():
                if(ops["ReadData"][-2:] == "ff"):
                    politeShutdown(fac)
    else:
        logger.info('no tags seen')
        return
    for tag in tags:
        tagReport += tag['TagSeenCount'][0]

def parse_args ():
    global args
    parser = argparse.ArgumentParser(description='Simple RFID Reader Inventory')
    parser.add_argument('host', help='hostname or IP address of RFID reader',
            nargs='*')
    parser.add_argument('-p', '--port', default=llrp.LLRP_PORT, type=int,
            help='port to connect to (default {})'.format(llrp.LLRP_PORT))
    parser.add_argument('-t', '--time', type=float,default=None,
            help='number of seconds for which to inventory and access (default inf.)')
    parser.add_argument('-d', '--debug', action='store_true',
            help='show debugging output')
    parser.add_argument('-a', '--antennas', default='1', help='comma-separated list of antennas to enable (0=all; '\
                'default 1)')
    parser.add_argument('-n', '--report-every-n-tags', default=1, type=int,
            dest='every_n', metavar='N', help='issue a TagReport every N tags')
    parser.add_argument('-X', '--tx-power', default=0, type=int,
            dest='tx_power', help='Transmit power (default 0=max power)')
    parser.add_argument('-M', '--modulation', default='WISP5', help='modulation (default WISP5)')
    parser.add_argument('-T', '--tari', default=0, type=int,
            help='Tari value (default 0=auto)')
    parser.add_argument('-s', '--session', default=2, type=int,
            help='Gen2 session (default 2)')
    parser.add_argument('-P', '--tag-population', default=4, type=int,
            dest='population', help="Tag Population value (default 4)")
    parser.add_argument('-c', '--reconnect', action='store_true',
            default=False, help='reconnect on connection failure or loss')

    # read or write
    #op = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('-r', '--read-words', type=int,
            help='Number of words to read from MB 0 WordPtr 0')
    parser.add_argument('-w', '--write-words', type=int,
            help='Number of words to write to MB 0 WordPtr 0')
    parser.add_argument('-l', '--logfile')

    args = parser.parse_args()

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

def main ():
    global fac,time_start
    parse_args()
    init_logging()

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

    # will be called when all connections have terminated normally
    onFinish = defer.Deferred()
    onFinish.addCallback(finish)

    enabled_antennas = map(lambda x: int(x.strip()), args.antennas.split(','))

    fac = llrp.LLRPClientFactory(onFinish=onFinish,
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

    # start tag access once inventorying
    fac.addStateCallback(llrp.LLRPClient.STATE_INVENTORYING, access)

    for host in args.host:
        reactor.connectTCP(host, args.port, fac, timeout=3)

    # catch ctrl-C and stop inventory before disconnecting
    reactor.addSystemEventTrigger('before', 'shutdown', politeShutdown, fac)
    reactor.run()

if __name__ == '__main__':
    main()
