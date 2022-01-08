# CS280p2

# This project consists of two files; tracker.py and peer.py. This code was designed by Caleb Sacks, Ezekiel Palmer, Grant Meyer, and Jonathan Hoff for CSCI 280
# at Clark University as a part of our Programming Assignment 2. The python files in this repository are my own personal copies of the original code we worked on.

# Tracker

# The tracker breaks up a specified file into chunks of size 10KB each. It then randomly distributes the chunks to each of the running peers when the peers connect
# to the tracker. The tracker must send each chunk but cannot send the same chunk more than once, and sends the same number of chunks to each peer randomly.

# Peer

# Each person runs the peer on their own device. They connect the peer to the tracker and recieve random chunks from a specified file. After every peer has recieved 
# their chunks, the peers then connect to their "neighbors." By connecting each peer, each peer then has an upload neighbor and a download neighbor to send chunks 
# to one and recieve chunks from the other. The peers send all the individual chunks between themselves until each peer has all the chunks of the file. Then
# the peers reassemble the file.
