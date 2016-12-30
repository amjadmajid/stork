from __future__ import print_function
import argparse
import logging
import pprint
import time,re

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt


logger   = logging.getLogger()
args = None
p = dict()

def checkrange(x,mini,maxi):
    x = float(x)
    if x < mini:
        raise argparse.ArgumentTypeError("Minimum tari is 6.25us")
    if x > maxi:
        raise argparse.ArgumentTypeError("Maximum tari is 25us")
    return x

def tari(x):
    return checkrange(x,6.25,25)

def rtcal(x):
    return checkrange(x,2.5,3)

def trcal(x):
    return checkrange(x,1.1,3)

def t5(x):
    return checkrange(x,0,20000)

def parse_args ():
    global args
    parser = argparse.ArgumentParser(description='Analitical model of EPC GEN 2 standard')
    parser.add_argument('-N', '--nr_of_Tags', default=1, type=int, help='number of tags')
    parser.add_argument('-t', '--tari', default=None, type=tari, help='Tari value in microseconds (defaultR1000 = 7.14)')
    parser.add_argument('-T?', '--commandTimeQuestion', default=None, help='calculate the time of this command')
    parser.add_argument('--rtcal_mult', default=2.75, type=rtcal, help='trcal multiplier, rtcal=X*tari (2.5<X<3) (default = 2.75)')
    parser.add_argument('--trcal_mult', default=2, type=trcal, help='trcal multiplier, trcal=X*rtcal (1.1<X<3) (default = 2.0)')
    parser.add_argument('--delayed_reply', default=0, type=t5, help='Delayed reply, response time of tag to blockwrite, default = minimum')
    parser.add_argument('-I', '--impinj', action='store_true', help='use Impinj Blockjeswrite')
    parser.add_argument('-g', '--highspeed', action='store_true', help='Show maximum speed')
    parser.add_argument('-s', '--slowspeed', action='store_true', help='Show worstcase speed')
    parser.add_argument('-d', '--debug', action='store_true', help='show debugging output')
    parser.add_argument('-l', '--logfile')

    args = parser.parse_args()


def init_logging ():
    logLevel  = (args.debug and logging.DEBUG or logging.INFO)
    logFormat = '%(message)s' #%(asctime)s:
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

    logger.log(logLevel, 'Analytical Model\nlog level: {}'.format(logging.getLevelName(logLevel)))

def parameters(p,nr_of_Tags = 1, tari = 7.140, c_0 = 1.75, highspeed = None, slowspeed = None,
slow_reply = None,trcal_mult = 2, delimeter = 12.5, t1 = None, t2 = None, t4 = None, t5 = None):
    p['nr_of_Tags'] = nr_of_Tags
    p['times'] = dict()
    t = p['times']
    ## Tari
    t['tari_min'] = 6.25 # us
    t['tari_max'] = 25 # us
    t['tari'] = tari # us default for R1000
    if(highspeed):
        t['tari'] = t['tari_min']
    elif(slowspeed):
        t['tari'] = t['tari_max']

    ## Symbols
    t['symbol_0'] = t['tari']
    t['symbol_1_min'] = 1.5*t['tari']
    t['symbol_1_max'] = 2.0*t['tari']
    t['symbol_1'] = c_0*t['tari']
    if(highspeed):
        t['symbol_1'] = t['symbol_1_min']
    elif(slowspeed):
        t['symbol_1'] = t['symbol_1_max']
    t['symbol_mean'] = (t['symbol_0']+t['symbol_1'])/2
    t['symbol_X'] = t['symbol_mean']

    ## Calibration
    t['rtcal'] = t['symbol_0']+ t['symbol_1']

    t['trcal_min'] = 1.1*t['rtcal']
    t['trcal_max'] = 3.0*t['rtcal']
    t['trcal'] = trcal_mult*t['rtcal']
    if(highspeed):
        t['trcal'] = t['trcal_min']
    elif(slowspeed):
        t['trcal'] = t['trcal_max']

    ## delimeter
    t['delimeter']=delimeter
    t['delimeter_min']= t['delimeter']*.95
    t['delimeter_max']= t['delimeter']*1.05
    if(highspeed):
        t['delimeter'] = t['delimeter_min']
    elif(slowspeed):
        t['delimeter'] = t['delimeter_max']

    t['preamble'] = t['delimeter']+t['symbol_0']+t['rtcal']+t['trcal']
    t['frame_sync'] = t['delimeter']+t['symbol_0']+t['rtcal']

    p['divide_ratio'] = 64/3
    t['fm0_symbol'] = t['trcal']/p['divide_ratio']
    t['fm0_preamble'] = 6*t['fm0_symbol']
    t['fm0_ext_preamble'] = 12*t['fm0_symbol']+t['fm0_preamble']

    # time between messages: table 6.16 in Gen2_protocol_standard.pdf
    t['pri'] = t['fm0_symbol'] # table footnote 1
    FT = 0.15
    t['t1_min'] = max(t['rtcal'],10*t['pri'])*(1-FT)-2
    t['t1_max'] = max(t['rtcal'],10*t['pri'])*(1+FT)+2
    if t1:
        t['t1'] = t1
    else:
        t['t1'] = max(t['rtcal'],10*t['pri'])
    t['t2_min'] = 3*t['pri']
    t['t2_max'] = 20*t['pri']
    if t2:
        t['t2'] = t2
    else:
        t['t2'] = t['t2_min']
    t['t3'] = 0
    if t4:
        t['t4'] = t4
    else:
        t['t4'] = 2*t['rtcal']
    t['t3'] = max(0, t['t4']-t['t1']) # table footnote 5
    t['t5_min'] = t['t1_min']
    t['t5_max'] = 20000 *.02
    if t5:
        t['t5'] = t5
    else:
        t['t5'] = max(t['t5_min'],slow_reply)


    # messages
    p['all_message_keys'] ={'Q','QNR','QR','QRNR','A','RN','R','W','BW','BJW',}
    p['all_messages'] ={'Q':'Query','QNR':'Query No Resp.',
    'QR':'QueryRep','QRNR':'Q_Rep No Resp',
    'A':'Ack','RN':'req. Rand. No',
    'R':'Read','W':'Write',
    'BW':'BlockWrite','BJW':'BlockJesWrite',}
    MB = 'X1'

    p['Q'] = {'l' : 22,'s':'1000','msg':'100010000010X00XXXXXX',
    'reply':{'l':16,'msg':'X'*16,},
    }
    p['QNR'] = {'l' : 22,'s':'1000','msg':'100010000010X00XXXXXX',
    'reply':{'l':0,'msg':'',},
    }

    p['QR'] = {'l' : 4,'s':'00','msg':'00XX',
    'reply':{'l':16,'msg':'X'*16,},
    }

    p['QRNR'] = {'l' : 4,'s':'00','msg':'00XX',
    'reply':{'l':0,'msg':'',},
    }

    p['A'] = {'l' : 2+16,'s':'01','msg':'01'+'X'*16,
    'reply':{'l':16+6*16+16,'msg':'X'*128,},
    }
    p['RN'] = {'l' : 8+16+16,'s':'11000001','msg':'11000001'+'X'*32,
    'reply':{'l':32,'msg':'X'*32,},
    }

    def readReply(words):
        return {'l':1+words*16+16+16,'msg':'0'+'X'*16*words+'X'*(16+16),}
    p['R'] = {'l' : 8+2+8+8+16+16,'s':'11000010','msg':'11000010'+MB+'0'*8+'X'*(8+16+16),
    'reply':readReply,
    }

    delayed_reply = {'l':33,'msg':'0'+'X'*32,}
    p['W'] = {'l' : 8+2+8+16+16+16,'s':'11000011','msg':'11000011'+MB+'0'*8+'X'*(16+16+16),
    'reply':delayed_reply,
    }

    def blockwrite(words):
        return {'l' : 8+2+8+8+16*words+16+16,'s':'11000111','msg':'11000111'+MB+'0'*4+'X'*(4+8+16*words+16+16),
        'reply':delayed_reply,
        }
    p['BW'] = blockwrite

    p['BJW'] = {'l' : 8+2+8+8+16+16+16,'s':'11000111',
    'msg':'11000111'+'00'+'0'*4+'X'*4+'0'*7+'1'+'X'*(16+16+16),
    'reply':delayed_reply,
    }
    p['needs_time_T2_after']= {'Q','QR', 'A', 'RN',}
    p['needs_time_T4_after']= {'QNR','QRNR','R', 'W', 'BW', 'BJW',}
    p['needs_immediate_reply'] = {'Q','QR','A','RN','R',}
    p['needs_delayed_reply']={ 'W','BW','BJW',}
    p['no_reply'] = {'QNR','QRNR',}
    p['needs_preamble']={'Q',}
    p['needs_frame_sync']=  p['all_message_keys'] ^ p['needs_preamble']
    p['variable_reply_length'] = {'R',}
    p['variable_command_length'] = {'BW',}

def splitcmd(command_and_poss_number):
    global p

    command_and_poss_number = re.sub('[^A-Z0-9]','',command_and_poss_number)
    # extract a possible argument of the command
    CMDparts = re.split('(\d+)',command_and_poss_number)
    command = CMDparts[0]
    nr = CMDparts[1]if len(CMDparts)>1 else ''

    return {'cmd':command,'nr':nr,}

def expandcmd(cmd):
    global p
    spl = splitcmd(cmd)
    return p['all_messages'][spl['cmd']]+spl['nr']

# time of the Reader signal
def timeOfPIEMsg(msg,maxtime=0.5):
    global p
    time_min = 0
    time_max_addition = 0
    if(msg[0:4]== p['Q']['s']):
        time_min+=p['times']['preamble']
    else:
        time_min+=p['times']['frame_sync']

    while(len(msg)):
        symbol = msg[0]
        msg = msg[1:]
        if symbol in {'0','1'}:
            time_min+= p['times']['symbol_'+symbol]
        else:
            time_min+= p['times']['symbol_0']
            time_max_addition+= p['times']['symbol_1']-p['times']['symbol_0']

    return time_min+maxtime*time_max_addition

# time of backscatter message
def timeOfBackScatter(msg,TRext = None,maxtime = 0):
    global p
    time = 0
    # preamble
    if(TRext or maxtime==1): # is it an extended preamble?
        time+=p['times']['fm0_ext_preamble']
    else:
        time+=p['times']['fm0_preamble']

    # check if data is valid
    if(not all((x in {'0','1','X',}) for x in msg)):
        raise NameError('Message is not composed of known symbols (1,0,X)%s'%msg)
    # data bits
    time += len(msg)*p['times']['fm0_symbol']
    # dummy bit
    time += p['times']['fm0_symbol']
    return time

def timeOfCommand(command_X,maxtime=0.5, replytime=0):
    global p
    time = 0
    if (len(p) == 0):
        define_p()

    spl= splitcmd(command_X)
    command = spl['cmd']
    if(spl['nr']):
        nr_words = int(spl['nr'])

    if(command in p['variable_command_length']):
        commandparameter = p[command](nr_words)
    else:
        commandparameter = p[command]
    time+=timeOfPIEMsg(commandparameter['msg'],maxtime)

    if command in p['needs_immediate_reply']:
        time+=(1-replytime)*p['times']['t1_min']+replytime*p['times']['t1_max']
    elif command in p['needs_delayed_reply']:
        time+=p['times']['t5']
    elif(command in p['no_reply']):
        time+=0
    else:
        raise NameError('Command [%s] has no TIMEBETWEEN specified'%command)

    # reply time
    if(command in p['variable_reply_length'] ): # Is reply length variable?
        time += timeOfBackScatter(commandparameter['reply'](nr_words)['msg'])
    elif(commandparameter['reply']['l']):
        time += timeOfBackScatter(commandparameter['reply']['msg'])
    else:
        time+=0

    if command in p['needs_time_T2_after']:
        time+=(1-replytime)*p['times']['t2_min']+replytime*p['times']['t2_max']
    elif command in p['needs_time_T4_after']:
        time+=(1-replytime)*p['times']['t4']+ replytime*1000
    else:
        raise NameError('Command [%s] has no TIMEAFTER specified'%command)
    return time

def timesOfCommand(command_and_poss_number,maxtime=0.5, replytime=0):
    global p

    command_and_poss_number = re.sub('[^A-Z0-9]','',command_and_poss_number)
    # extract a possible argument of the command
    CMDparts = re.split('(\d+)',command_and_poss_number)
    command = CMDparts[0]
    nr_words = int(CMDparts[1])if len(CMDparts)>1 else None

    if(command in p['variable_command_length']):
        commandparameter = p[command](nr_words)
    else:
        commandparameter = p[command]
    time1=timeOfPIEMsg(commandparameter['msg'],maxtime)

    if command in p['needs_immediate_reply']:
        time2=(1-replytime)*p['times']['t1_min']+replytime*p['times']['t1_max']
    elif command in p['needs_delayed_reply']:
        time2=(1-replytime)*p['times']['t5_min']+replytime*p['times']['t5_max']
    elif(command in p['no_reply']):
        time2=0
    else:
        raise NameError('Command [%s] has no TIMEBETWEEN specified'%command)

    # reply time
    if(command in p['variable_reply_length'] ): # Is reply length variable?
        time3= timeOfBackScatter(commandparameter['reply'](nr_words)['msg'],maxtime)
    elif(commandparameter['reply']['l']):
        time3= timeOfBackScatter(commandparameter['reply']['msg'],maxtime)
    else:
        time3 = 0

    if command in p['needs_time_T2_after']:
        time4=(1-replytime)*p['times']['t2_min']+replytime*p['times']['t2_max']
    elif command in p['needs_time_T4_after']:
        time4=(1-replytime)*p['times']['t4']+ replytime*1000
    else:
        raise NameError('Command [%s] has no TIMEAFTER specified'%command)
    return [time1,time2,time3,time4]



def showFigure():
    #cmds = ['Q','QR','QNR','QRNR','A','RN','A','R1','R2','R4','R16','W','BW1','BW2','BW3','BW4','BW5','BW6','BW7','BJW']
    cmds = ['Q','QR','A','RN','A','R1','R16','BJW','BW16']

    times = [timesOfCommand(cmd,0) for cmd in cmds]
    ts = [sum(x) for x in times]
    logger.info("\nepcread 6words          Q+ack  = %5ius, QR+ack  =%5ius => %3ius/word\n" % (ts[0]+ts[2], ts[1]+ts[2], (ts[1]+ts[2])/6 ))
    for x in [1,2,3,4,8]:
        logger.info("epcread (6words+) 16w*%i Q+ack+R= %5ius, QR+ack+R=%5ius => %3ius/word" %
            (x,ts[0]+sum(ts[2:-1])+ts[-1]*x,sum(ts[1:-1])+ts[-1]*x , (sum(ts[1:-1])+ts[-1]*x) / (x*16) ))


    tRT = [x[0] for x in times]
    tT = [x[1] for x in times]
    tRTT = [x+y for (x,y) in zip(tRT,tT)]
    tTR = [x[2] for x in times]
    tRTTTR = [x+y+z for (x,y,z) in zip(tRT,tT,tTR)]
    tR = [x[3] for x in times]



        # showing all the times
    plt.figure()
    w = 0.3
    d = .02
    xpos = range(len(cmds))
    xcpos = [x-d-w/2 for x in range(len(cmds))]+ [x+d+w/2 for x in range(len(cmds))]
    plt.bar([x-w-d for x in xpos],tRT,width=w)
    plt.bar([x-w-d for x in xpos],tT,bottom=tRT,width=w,color='y')
    plt.bar([x-w-d for x in xpos],tTR,bottom=tRTT,width=w,color=[1,0,0,.9])
    plt.bar([x-w-d for x in xpos],tR,bottom=tRTTTR,width=w,color='g')

    times = [timesOfCommand(cmd,1) for cmd in cmds]
    tRT = [x[0] for x in times]
    tT = [x[1] for x in times]
    tRTT = [x+y for (x,y) in zip(tRT,tT)]
    tTR = [x[2] for x in times]
    tRTTTR = [x+y+z for (x,y,z) in zip(tRT,tT,tTR)]
    tR = [x[3] for x in times]
    plt.bar([x+d for x in xpos],tRT,color=[0,0,1],width=w)
    plt.bar([x+d for x in xpos],tT,bottom=tRT,width=w,color='y')
    plt.bar([x+d for x in xpos],tTR,bottom=tRTT,width=w,color=[1,0,0,0.9])
    plt.bar([x+d for x in xpos],tR,bottom=tRTTTR,width=w,color='g')

    plt.legend(['Reader=>Tag','Tag processing','Tag=>Reader','Reader processing'],loc=2)
    plt.xticks(rotation=90)
    plt.xticks(xcpos, [expandcmd(x)+' min' for x in cmds]+[expandcmd(x)+ ' max' for x in cmds])
    plt.ylabel('time [us]')
    plt.tight_layout()
    plt.axis((-1,len(xpos),0,5000))
    plt.show()
    plt.draw()

# define p at the max speed
def define_p():
    global p
    parameters(p,highspeed = False)

def main ():
    global fac, logger, p
    parse_args()
    init_logging()
    define_p()
    # parameters(p, nr_of_Tags = args.nr_of_Tags)
    #logger.debug(pprint.pprint(p))

    if(args.commandTimeQuestion):
        tmin = timeOfCommand(args.commandTimeQuestion,0)
        tmax = timeOfCommand(args.commandTimeQuestion,1)
        logger.info("Time of the command: %3.2f to %3.2f us"%(tmin,tmax))

    # showFigure()
    t_hc = sum([timeOfCommand(x,0.5) for x in (["Q","A","RN","A"])]) # handshake + command initialization
    t_hs = sum([timeOfCommand(x,0.5) for x in (["Q","A"])]) # handshake short
    t_empty = sum(timesOfCommand("QR")[1:2])
    t_collision = timeOfCommand("QR")
    t_BJW = timeOfCommand("BJW")
    t_BJW32_7 = 32*7*t_BJW
    t_W = timeOfCommand("W")
    t_R30_7 = timeOfCommand("R14")

    t_llrp = 1*1000
    t_aloha = 1500*0
    t_Stork_30_7 = t_hc+t_BJW32_7+t_R30_7+t_llrp+t_aloha
    t_Wisent_16_1 = (t_hc + t_BJW*18)*2 +t_llrp+t_aloha
    t_R2_1_1 = t_hc + t_W + t_llrp + t_aloha
    print ("BJW = "+str(t_BJW))
    print ("W = "+ str(t_W))
    print ("hc = "+str(t_hc))
    print ("hs = "+str(t_hs))
    print ("empty = "+ str(t_empty))
    print ("collision = "+ str(t_collision))
    print ("Read Stork = " + str(t_R30_7))
    print ("Stork time per word:  %3.2f %6.2f %3.2f"%(t_Stork_30_7/30.0/7, t_Stork_30_7, t_Stork_30_7/30.0/7*2500/1000000))
    print ('Wisent time per word: %3.2f %6.2f %3.2f'%(t_Wisent_16_1/16.0, t_Wisent_16_1, t_Wisent_16_1/16.0*2500/1000000))
    print ('R2 time per word:     %3.2f %6.2f %3.2f'%(t_R2_1_1, t_R2_1_1, t_R2_1_1*2500/1000000))
    print ('handshake =  ' + str(t_hc)+ 'us')


# how to use it without the main?
# from epcdownstream import *
# sum([timeOfCommand(x,0) for x in (["QR","A","RN","A"])]) get minimal time of handshake
# speed max due to EPC overhead: 32*8*2/sum([timeOfCommand(x,0.5) for x in (["QR","A","RN","A"]+ ["BW32" for k in range(8)])])*1000*1000
# speed max due to LLRP overhead: 32*8*2/sum([timeOfCommand(x,0.5) for x in (["QR","A","RN","A"]+ ["BW32" for k in range(8)])]+[20000])*1000*1000
# speed max due to current infrastructure: 32*8*2/sum([timeOfCommand(x,0.5) for x in (["Q","A","RN","A"]+ ["BJW" for k in range(32*8)])]+[20000])*1000*1000
#

if __name__ == '__main__':
    main()
