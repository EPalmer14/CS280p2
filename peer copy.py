import os
from os import error
import shutil
from socket import AF_INET, SOCK_STREAM, socket
import sys
import threading
from time import sleep
from typing import ByteString


NETWORK_RECEIVE_SIZE = 1024000


ip = 'http://localhost'
port = 12001
chunks_dir = 'peer_file'

quitting = False
# Known when chunks are received from the tracker
dwonload_socket = None

FileName = ""

def load_chunk_info():
    if not os.path.exists('chunks.txt'):
        return -1, []

    lines = None
    with open('chunks.txt', 'r') as f:
        lines = f.readlines()

    name = lines[0]
    total_chunk_count = int(lines[1])
    chunks_received = lines[2:]
    return total_chunk_count, chunks_received

total_chunk_count, chunks_received = load_chunk_info()


def save_chunk_info():
    with open('chunks.txt', 'w+') as f:
        lines = [FileName, str(total_chunk_count)] + chunks_received
        f.write('\n'.join(lines))


def assemble_file():
    global FileName
    global total_chunk_count

    if os.path.exists(FileName):
        os.remove(FileName)

    AssembledFile = open(f'{FileName}', 'ab+')
    i = 0
    while i < total_chunk_count:
        chunk = open(chunks_dir + '/chunk' + str(i), 'rb')
        AssembledFile.write(chunk.read())
        i += 1
    return

def send_chunk(connection, chunk_name):
    """Sends a file to the given connection
    Args:
        path (str): Path to the file
    """

    full_path = os.path.join(chunks_dir, chunk_name)
    #Send chunk size
    connection.send(f'{os.path.getsize(full_path)}'.encode())
    # sleep(1)

    if connection.recv(1024) == b'ACK':
        print("Ack received")
        with open(full_path, 'rb') as f:
            connection.sendall(f.read())
            print('Sent {}\n'.format(chunk_name))


def handle_connection(connection):
    while connection.fileno() > -1:
        #Receive chunk name
        chunk_name = connection.recv(NETWORK_RECEIVE_SIZE).decode()
        if chunk_name == '':
            break

        if chunk_name not in chunks_received:
            print(f'Requested chunk ({chunk_name}) missing, retrieving it from download neighbor')
            request_chunk_from_peer(download_socket, chunk_name)
            # chunks_received.append(data)
        #Otherwise, send chunk
        send_chunk(connection, chunk_name)


def accept_connections():
    listen_socket = socket(AF_INET, SOCK_STREAM)
    listen_socket.bind(('', port))
    listen_socket.listen(1)
    print('Listening at {}:{}\n'.format(ip, port))

    while True:
        # Wait for a new connection.
        connection, address = listen_socket.accept()
        print('Received connection ({})\n'.format(address))
        handle_connection(connection)

def request_chunk_from_peer(PeerSocket, chunk_name):
    #Send chunk name to peer
    PeerSocket.send(chunk_name.encode())
    #Receive chunk file size
    ChunkSize = int(PeerSocket.recv(NETWORK_RECEIVE_SIZE).decode())
    print(ChunkSize)
    #Send acknowledgement
    PeerSocket.send(b'ACK')

    SaveFile = open(os.path.join(chunks_dir, chunk_name), 'wb')

    #Receive chunkdata
    data = bytearray()
    while len(data) < ChunkSize:
        file = PeerSocket.recv(ChunkSize - len(data))
        if not file:
            return None
        data.extend(file)
        print('length of data: ')
        print('length of ChunkSize: ')
        print(len(data))
        print(ChunkSize)
    print('File received')

    SaveFile.write(data)

    chunks_received.append(chunk_name)

def request_chunks_from_peer(download_ip, download_port):
    global download_socket

    download_socket = socket(AF_INET, SOCK_STREAM)
    download_socket.connect((download_ip, download_port))

    input('Press Enter to continue...')

    all_chunk_names = [f'chunk{i}' for i in range(0, total_chunk_count)]
    missing_chunk_names = [name for name in all_chunk_names if name not in chunks_received]
    for name in missing_chunk_names:
        print("Requesting chunk: " + name)
        request_chunk_from_peer(download_socket, name)

def request_chunks_from_tracker(ip, port):
    global total_chunk_count
    global chunks_received
    global FileName

    IP = ip
    Port = port
    TrackerSocket = socket(AF_INET, SOCK_STREAM)
    TrackerSocket.connect((IP, Port))

    #Receive final file name and expected number of chunks
    FileInfo = TrackerSocket.recv(NETWORK_RECEIVE_SIZE).decode()
    #Parse received data
    data = FileInfo.split(" ")
    FileName = data[0]
    #Does this variable need to be global?
    received_chunk_count = int(data[1])
    total_chunk_count = int(data[2])
    print("Expecting: %s of chunks" % data[1])

    # Clear contents of directory and then make it
    if os.path.isdir(chunks_dir):
        shutil.rmtree(chunks_dir)

    os.mkdir(chunks_dir)

    #Open file to write chunk numbers to
    chunks_received = []
    i = 0
    #Continue to receive chunks until expected number is reached
    while i < received_chunk_count:
        # print("Waiting For Chunk: " + str(i))
        #Receive chunk file (name) and size
        FileChunk = TrackerSocket.recv(NETWORK_RECEIVE_SIZE).decode()
        chunkData = FileChunk.split(" ")
        chunkName = chunkData[0]
        chunkSize = int(chunkData[1])
        # print(FileChunk)
        print("Received: " + chunkName)
        #Write chunk to record
        chunks_received.append(chunkName)
        #Continue to send acknowledgements until chunk data is received
        while True:
            #Send chunk acknowledgement to receive data
            print("Sending ack")
            TrackerSocket.send(b'ACK')
            #Receive chunk file (data)

            # file = TrackerSocket.recv(NETWORK_RECEIVE_SIZE)

            data = bytearray()
            while len(data) < chunkSize:
                file = TrackerSocket.recv(chunkSize - len(data))
                if not file:
                    return None
                data.extend(file)
                print("packet data received")


            if file:
                print("Chunk data received")
                #Create chunk file
                Chunk = open(f'{chunks_dir}/{chunkName}', 'wb+')
                #Write data to file
                Chunk.write(data)
                break
            # sleep(1)
        i += 1

    #assemble_file()
    return total_chunk_count, chunks_received

def accept_commands():
    global quitting

    try:
        # Command loop
        while not quitting:
            command = input('Enter command: ')
            # TODO
            command = command.split(' ')

            if command[0] == 'connect':
                _, IP, Port, flag = command
                if flag == 'p':
                    request_chunks_from_peer(IP, int(Port))

                if flag == 't':
                    request_chunks_from_tracker(IP, int(Port))

            elif command[0] == 'assemble':
                assemble_file()

            else:
                print('Incorrect command')

    except KeyboardInterrupt:
        save_chunk_info()
        quitting = True


def main():
    try:
        threading.Thread(target=accept_connections).start()
        sleep(1)
        accept_commands()
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
