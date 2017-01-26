This program is used to compress hexdecimal file. It uses Huffman algorithm to 
generate the optimal binary code. Using the optimal code a compressed hex file 
is generated. 
Once the compressed file is generated, a python script will be called. The 
python script formats the compressed hex file as an intel hex formatted file. 

The C program "compress" expect and input hex file called "dump.hex" in the 
dataFiles folder. A bash script which is found in the bin folder is used to 
invoke the c program and the python script. the output file is generated in the
ouput folder. 

In case of compressing an Intel hex file, the user can use a python script in 
the python folder called "rm_intel_format_newlines.py" to remove the addresses 
and other intel-format related hex digits. The script will produce a dump.hex 
file in the dataFiles folder. 

In case of compressing an intel formatted firmware, the user must manually 
transfer the the first line of the original hex file and the last lines for 
the interrupts. These lines   are transferred uncompressed. 