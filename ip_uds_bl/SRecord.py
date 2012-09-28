#!/usr/bin/env python
# Copyright 2011 Satish Krosuru <satish77@gmail.com>

from struct import *
from array import *
import sys
import time
import myutils
import operator

g_prg_rqst = 0

class SRecord:
    def __init__(self, init=0xff, checkcs=True):
        self.udata  = []
        self.data   = []
        self.tail   = {}
        self.offset = 0
        self.size   = 0
        self.start  = None
        self.comm   = []
        self.init   = init
        self.check  = checkcs

    def get_data(self):
        return self.udata

    def readrecord(self, line):
        """Read a line and give an S-Record address, data and checksum"""
        type = line[:2]
        data = [int(line[i:i + 2], 16) for i in range(2, len(line), 2)]
        cs   = (reduce(operator.add, data) + 1) & 0xff
        if type in ('S1', 'S9'):
            adr = (data[1] << 8) + data[2]
            fd  = 3
        elif type in ('S2', 'S8'):
            adr = (data[1] << 16) + (data[2] << 8) + data[3]
            fd  = 4
        elif type in ('S3', 'S7'):
            adr = (long(data[1]) << 24) + (data[2] << 16) + (data[3] << 8) + data[4]
            fd  = 5
        elif type == 'S0':      # Comment
            return 'C', 0, data[3:-1], cs
        else:
            raise ValueError, "Not a valid S-Record"
        if type > 'S6':         # Start Address
            type = 'S'
        else:                   # Data
            type = 'D'
        return type, adr, data[fd:-1], cs

    def readrecords(self, records):
        """A list (rows) of S-Records read."""
        recno = -1
        for line in records:
            recno += 1
            line = line.rstrip()
            type, adr, data, cs = self.readrecord(line)
            if cs and self.checkcs:
                raise ValueError, "Error in Record %d" % recno
            if type == 'D':
##                if recno < 10:
##                    print hex(adr) + "\t" + line
                self.udata.append((adr, data))
            elif type == 'S':
                #print "Starting address: " + hex(adr)
                self.start = adr
            else:
                self.comm.append("".join(map(chr, data)))
        if not self.udata:
            return
        self.udata.sort()
        #print self.udata[0]
        loadr = self.udata[0][0]
        hiadr = self.udata[-1][0] + len(self.udata[-1][1])
        size  = hiadr - loadr
        #print "loadr:" + str(hex(loadr)) + "\thiadr:" + str(hex(hiadr)) + "\tsize(KB):" + str(size/1024)

    def print_chunks(self):
        udata_len = len(self.udata)
        i = 0
        next_addr = 0
        chunk_size = 0
        chunk_addr = 0
        num_chunks = 0
        for i in range(0, udata_len):
            #if num_chunks < 10:
            #    print "Address:" + hex(self.udata[i][0]) + "\tLength:" + str(len(self.udata[i][1]))
            if self.udata[i][0] == next_addr:
                chunk_size += len(self.udata[i][1])
                next_addr += len(self.udata[i][1])
            else:
                if chunk_size > 0:
                    num_chunks = num_chunks + 1
                    #if num_chunks < 10:
                    print "Chunk address: 0x%08X" % chunk_addr + "\tSize(bytes): %8d" % chunk_size
                chunk_size = len(self.udata[i][1])
                chunk_addr = self.udata[i][0]
                next_addr = self.udata[i][0] + len(self.udata[i][1])
        if chunk_size > 0:
            num_chunks = num_chunks + 1
            print "Chunk address: 0x%08X" % chunk_addr + "\tSize(bytes): %8d" % chunk_size

    def send_to_target(self, addr, buf):
        global g_prg_rqst

##        if g_prg_rqst > 3:
##            return
        
        g_prg_rqst = g_prg_rqst + 1
        assert ((addr & 0x7) == 0)
        assert ((len(buf) & 0x7) == 0)
        if buf == []:
            print "Empty"
        else:
            a = ' '.join( [ "%02X" % x for x in buf ])
            #print "0x%08X" % addr, len(buf), map(hex, buf)
            #print "0x%08X" % addr, "%2X" % len(buf), a
            print "%5d" % g_prg_rqst, "%08X" % addr, "%2X" % len(buf)
        
        a = []
        a.append((addr >> 24) & 0xFF)
        a.append((addr >> 16) & 0xFF)
        a.append((addr >> 8) & 0xFF)
        a.append(addr & 0xFF)
        a.append((len(buf) >> 8) & 0xFF)
        a.append(len(buf) & 0xFF)
        a = a + buf
        print a
        #self.WriteArray("fprgBuff", a, len(a))
        #self.WriteVariable("fprgCSW", 0x8B)
        
    def download_to_target(self):
        global g_prg_rqst
        buf = []
        buf_max = 32
        buf_addr = 0
        g_prg_rqst = 0
        for i in range(len(self.udata)):
            sr_addr = self.udata[i][0]
            """ if buffer is empty then record s-record as start address of the buffer and next data address"""
            if buf == []:
                sr_addr_aligned = sr_addr & 0xFFFFFFF8
                buf_addr = next_data_addr = sr_addr_aligned
                """ pad for non-aligned addresses """
                for l in range(sr_addr_aligned, sr_addr):
                    buf.append(0xFF)
                    next_data_addr = next_data_addr + 1
            elif next_data_addr != sr_addr:
                buf_end_addr_aligned = (buf_addr + len(buf) + 7 - 1) & ~7
                if(sr_addr > buf_end_addr_aligned):
                    while (next_data_addr % 8) != 0:
                        buf.append(0xFF)
                        next_data_addr = next_data_addr + 1
                    self.send_to_target(buf_addr, buf)
                    buf = []
                    buf_addr = next_data_addr = sr_addr
                    assert (buf_addr & 0x7) == 0
                else:
                    while(next_data_addr < sr_addr):
                        buf.append(0xFF)
                        next_data_addr = next_data_addr + 1               

            if len(buf) >= buf_max:
                self.send_to_target(buf_addr, buf)
                buf_addr = next_data_addr
                assert (buf_addr & 0x7) == 0
                buf = []
                
            for j in range(len(self.udata[i][1])):
                data = self.udata[i][1][j]
                buf.append(data)
                next_data_addr = next_data_addr + 1
                if len(buf) >= buf_max:
                    self.send_to_target(buf_addr, buf)
                    buf_addr = next_data_addr
                    assert (buf_addr & 0x7) == 0
                    buf = []
        """ if buffer is not algined then pad it """
        while((len(buf) % 8) <> 0):
            buf.append(0xFF)
        self.send_to_target(buf_addr, buf)    

if __name__ == '__main__':
    pass
    #s19path = win32api.GetFullPathName(sys.argv[1])

    #print "s19 file " + s19path
    #if (len(win32api.FindFiles(s19path)) == 0):
    #    print "Please give correct s19 file."
    #    sys.exit(0)

    #start_time = time.time()
    #temp_time = time.localtime()
    #str_date = str(temp_time[1]) + ":"+ str(temp_time[2]) + ":" + str(temp_time[0])
    #str_time = str(temp_time[3]) + ":"+ str(temp_time[4]) + ":" + str(temp_time[5])
    #print "Start Date [MM:DD:YYYY] " + str_date
    #print "Start Time [HH:MM:SS]   " + str_time
    #fp = open(s19path, 'rb')
    #rcount = 0
    #data = fp.readlines()
    #s = SRecord()
    #s.readrecords(data)
    #fp.close()
    #end_time = time.time()
    #temp_time = time.localtime()    
    #str_time = str(temp_time[3]) + ":"+str(temp_time[4]) + ":" + str(temp_time[5])
    #print "End Time [HH:MM:SS]  " + str_time
    #s.print_chunks()
    #s.download_to_target()
    #time_taken = (time.time() - start_time)
    #print "Time Taken: " + str(time_taken) + ( "Seconds")

    #print "Finished ..."

