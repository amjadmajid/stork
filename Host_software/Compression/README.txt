This program is used to compress a hexdecimal file. It uses Huffman algorithm to 
generate the optimal binary code. Using the optimal code a compressed hex file 
is generated. 
Once the compressed file is generated, a python script will be called. The 
python script formats the compressed hex file as an intel hex formatted file. 

The C program "compress" expects and input hex file called "dump.hex" in the 
dataFiles folder. A bash script which is found in the bin folder is used to 
invoke the C program and the python script. the output file is generated in the
output folder. 

In case of compressing an Intel hex file, the user can use a python script in 
the python folder called "rm_intel_format_newlines.py" to remove the addresses 
and other intel-format related hex digits. The script will produce a dump.hex 
file in the dataFiles folder. 
