#  Copyright (c) 2016,                                                                              #
# Author(s): Henko Aantjes,                                                                         #                 
# Date: 28/07/2016                                                                                  #

# most important files:
inventory.py --- check which wisps are in the view of the antenna
WControl.py --- main control script to do almost everything you dream of (concerning wisp communication)
WModules.py --- contains the common core modules that you should use for any pc-wisp communication

# other important files
WRam.py --- contains a class which is the virtual wisp memory
WStork.py --- send a lot of data to a wisp
WRepper.py --- reprogram a wisp, see info in file
WWisp.py --- main class that is used by wrepper.py
WWidgets.py --- contains all GUIs
WControlModules.py --- contains some example wisp control modules which build on top of the modules in WModules.py


# other files
access.py --- kind of inventory but with extra feature of doing 1 bunch of commands
llrp.py --- sllurp library handles user-to-sllurp communication
llrp_proto.py --- sllurp library handles tcp/llrp-to-sllurp communication

# other other files
Don't look at them, they are old or needed for llrp(_proto).py
