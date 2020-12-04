#!/usr/bin/env python3
#
# Author: K. Walsh <kwalsh@cs.holycross.edu>
# Modified by: Apurva, Margaret, Michael :)
# Date: 4 April 2017
# Modified: 4 Dec 2020
#
# Our updated version of the Stop-and-wait client. 
#
# What we've added: timeouts and retransmissions
# 
# What we havent: The ACK numbers are also completely ignored, so if
# there packets get duplicated in the network, things will probably go haywire.
# No send window, sends one packet at a time
#
# Run the program like this:
#   python3 client_saw.py 1.2.3.4 6000
# This will send data to a UDP server at IP address 1.2.3.4 port 6000.

import socket
import sys
import time
import struct
import datasource
import trace

# setting verbose = 0 turns off most printing
# setting verbose = 1 turns on a little bit of printing
# setting verbose = 2 turns on a lot of printing
# setting verbose = 3 turns on all printing
verbose = 2

# setting tracefile = None disables writing a trace file for the client
# tracefile = None
tracefile = "client_saw_packets.csv"

magic = 0xBAADCAFE

def main(host, port):
    print("Sending UDP packets to %s:%d" % (host, port))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Makes a UDP socket!

    trace.init(tracefile,
            "Log of all packets sent and ACKs received by client", 
            "SeqNo", "TimeSent", "AckNo", "timeACKed")

    start = time.time()
    seqno = 0
    while seqno < 5000:
        # get some example data to send
        body = datasource.wait_for_data(seqno)

        # make a header, create a packet, and send it
        hdr = bytearray(struct.pack(">II", magic, seqno))
        pkt = hdr + body
        tSend = time.time()
        s.sendto(pkt, (host, port))
        if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
            print("Sent packet with seqno %d" % (seqno))

        # wait for an ACK and timeout after 0.5 seconds
        t = 0.5    # timeout t must be a positive number (in seconds)
        try:
            s.settimeout(t)
            (ack, addr) = s.recvfrom(4000)
            tRecv = time.time()
            #... message received in time, do something with the message ...

            # unpack integers from the ACK packet, then print some messages
            (magack, ackno) = struct.unpack(">II", ack)
            if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
                print("Got ack with seqno %d" % (ackno))

            # write info about the packet and the ACK to the log file
            trace.write(seqno, tSend - start, ackno, tRecv - start)
            seqno += 1 # increament seqno

        # timeout expired but no packet was received yet
        except (socket.timeout, socket.error):
            print("timeout expired but no packet received yet")

        

    end = time.time()
    elapsed = end - start
    print("Finished sending all packets!")
    print("Elapsed time: %0.4f s" % (elapsed))
    trace.close()


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("To send data to the server at 1.2.3.4 port 6000, try running:")
        print("   python3 %s 1.2.3.4 6000" % (sys.argv[0]))
        sys.exit(0)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
