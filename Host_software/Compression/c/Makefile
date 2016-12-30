OBJS= huffmanAlgo.o charFreq.o cBinaryFile.o comprsdHex.o
CC=gcc
CFLAGS= -c
LFLAGS= -Wall

all: objs
	mv compress ../compress
	mv *.o ../objects/

objs: $(OBJS) 
	$(CC)  $(LFLAGS) $(OBJS) -o compress 

huffmanAlgo.o: huffmanAlgo.c  huffmanAlgo.h functions.h
	$(CC) $(CFLAGS)  huffmanAlgo.c  

charFreq.o: charFreq.c  huffmanAlgo.h
	$(CC) $(CFLAGS) charFreq.c 

cBinaryFile.o: cBinaryFile.c  huffmanAlgo.h
	$(CC) $(CFLAGS) cBinaryFile.c 

comprsdHex.o: comprsdHex.c  huffmanAlgo.h
	$(CC) $(CFLAGS) comprsdHex.c 


clean:
	-rm ../compress
	-rm ../objects/*.o 

clean_obj:
	-rm ../objects/*.o 

