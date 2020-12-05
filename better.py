#!/usr/bin/env python3
#
# Author: K. Walsh <kwalsh@cs.holycross.edu>
# Modified by: Apurva, Margaret, Michael :)
# Date: 4 April 2017
# Modified: 4 Dec 2020
#
# Our updated version of the Stop-and-wait client. 
#
# What we've added: timeouts and retransmissions, reordering, sliding window
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

    # Window size
    N = 5

    # How often to recalculate RTT, making sure it is greater than the window size
    RTT_frequency = 300 + N 
    
    window_ack = []
    for i in range(N):
        window_ack.append(0)

    tStart = time.time()   # start counting here

    # sending the first N in the window
    for i in range (0, N):
        body = datasource.wait_for_data(i)
        
        # make a header, create a packet, and send it
        hdr = bytearray(struct.pack(">II", magic, i))
        pkt = hdr + body
        tSend = time.time()
        s.sendto(pkt, (host, port))
        if verbose >= 3 or (verbose >= 1 and i < 5 or i % 1000 == 0):
            print("Sent packet with seqno %d" % (i))

    # initial timeout
    timeout = 0.5
    # intial starting time for probe packet
    starting = time.time()

    while seqno < 180000-N:
        try:
            s.settimeout(timeout)
            (ack, reply_addr) = s.recvfrom(4000)
            #... message received in time, do something with the message ...

            # unpack integers from the ACK packet, then print some messages
            (magack, ackno) = struct.unpack(">II", ack)
            if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
                print("Got ack with seqno %d" % (ackno))

            # if this is an ack for a probe packet, calculate how long it took
            if ackno % RTT_frequency == 0 and ackno != 0:
                total_time = time.time() - starting
                timeout = (7/8)*timeout + (1/8)*total_time

            # write info about the packet and the ACK to the log file
            trace.write(seqno, tSend - start, ackno, 1)

            # whatever ack that we received, record it
            window_ack[ackno] = 1

            # if this ack was the bottom of our window, move window up so that the bottom
            # equals the lowest # ack we are waiting for
            while window_ack[seqno] == 1:
                # Send seqno + N
                body = datasource.wait_for_data(seqno+N)
                hdr = bytearray(struct.pack(">II", magic, seqno+N))
                pkt = hdr + body
                tSend = time.time()
                
                # If this is a probe packet, start the timer
                if (seqno+N) % RTT_frequency == 0 and seqno != 0:
                    starting = time.time()
                    
                s.sendto(pkt, (host, port))
                if verbose >= 3 or (verbose >= 1 and seqno+N < 5 or seqno+N % 1000 == 0):
                    print("Sent packet with seqno %d" % (seqno+N))
                # Shift up the end of the window
                window_ack.append(0)
                # Shift up beginning of window
                seqno += 1   

        except (socket.timeout, socket.error):
            #... no packets are ready to be received ...
            if window_ack[seqno] == 0:
                # get some example data to send
                body = datasource.wait_for_data(seqno)

                # if resending a probe packet, restart the timer
                if seqno % RTT_frequency == 0 and seqno != 0:
                    starting = time.time()
                
                # make a header, create a packet, and send it
                hdr = bytearray(struct.pack(">II", magic, seqno))
                pkt = hdr + body
                tSend = time.time()
                s.sendto(pkt, (host, port))
                if verbose >= 3 or (verbose >= 1 and seqno < 5 or seqno % 1000 == 0):
                    print("Sent packet with seqno %d" % (seqno))


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
