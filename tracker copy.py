from socket import *
import _thread
import os
import math
import random
from time import sleep

port = 12000
socket = socket(AF_INET, SOCK_STREAM)
socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
socket.bind(('', port))
socket.listen(1)
print("PROXY is listening at port " + str(port) + ".")

#File name
FILE_NAME = ""
#Number of chunks to be shared per peer (updated in chunkFile())
numChunkShare = 0
extraChunks = 0
#Number of total chunks to be expected (updated in chunkFile())
numExpectedChunks = 0
chunksInNetwork = []

def chunkFile():
    global numChunkShare
    global extraChunks
    global numExpectedChunks
    global chunksInNetwork
    global extraChunks
    #Get size of file to calculate number of chunks
    fileSize = os.path.getsize(FILE_NAME)
    #Number of expected chunks given file size ( used for distributing somewhat equal amounts of chunks among peers)
    numExpectedChunks = math.ceil(fileSize / 10000)

    print(str(fileSize) + " bytes")
    print("Expected number of chunks " + str(numExpectedChunks))

    fileChunkArr = []

    #Read and break file into chunks
    with open(FILE_NAME, "rb") as f:
        #Make directory
        if not os.path.isdir("file1"):
            os.mkdir("file1")

        for i in range(numExpectedChunks):
            #Read 10kb from file at a time
            chunkContent = f.readlines(10000)
            #Create and write to chunk file
            chunk = open("file1/chunk" + str(i), "wb+")
            chunk.writelines(chunkContent)
            fileChunkArr.append(chunkContent)

    #Estimate number of chunks each peer gets
    numChunkShare = int(numExpectedChunks / 4)
    extraChunks = int(numExpectedChunks % 4)

    print('Number of Chunks to share to each peer: ' + str(numChunkShare))
    print('Remaining chunks to share: ' + str(extraChunks))
    print('Total chunks: ' + str(len(fileChunkArr)))
    #Create list of chunks (assembled in no-particular order)
    chunksInNetwork = os.listdir("file1")
    random.shuffle(chunksInNetwork)

def getChunkNos():
    chunkList = []
    for i in range(numChunkShare):
        chunkList.append(random.randrange(numExpectedChunks))
    return chunkList

#Distribute chunks to called thread
def distributeChunks(c, addr):
    global extraChunks
    # chunkList = getChunkNos() Still need???

    thisNumChunkShare = numChunkShare
    if extraChunks > 0:
        thisNumChunkShare += 1
        extraChunks -= 1

    #Send filename and number of chunks being sent to single peer
    c.send(f'{FILE_NAME} {thisNumChunkShare} {numExpectedChunks}'.encode())

    sleep(1)

    #List of chunk file names, pick one at random
    #Choose numChunkShare amount of random packets to send to thread
    for i in range(thisNumChunkShare):
        #Get chunk file name
        chunkFile = chunksInNetwork.pop()
        chunkSize = os.path.getsize("file1/" + chunkFile)
        #Send file name and size in bytes
        print(f'{chunkFile} {chunkSize}')
        c.send(f'{chunkFile} {chunkSize}'.encode())

        while True:
            if c.recv(1024) == b'ACK':
                #Open chunk file's content
                chunk = open('file1/' + chunkFile, "rb")
                print("Sending " + chunkFile)
                #Send chunk content
                c.sendall(chunk.read())
                break
            #Waiting for acknowledging
            print("Waiting...")


    #Exit loop once all chunks are sent
    print("File sent")

    c.close()

FILE_NAME = input("Enter file name to send: ")
chunkFile()
while True:
    connection, address = socket.accept()

    _thread.start_new_thread(distributeChunks,(connection, address))

    print("Established connection with " + str(address[0]) + " at port # " + str(address[1]) + "!")
