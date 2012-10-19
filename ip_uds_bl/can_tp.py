import unittest
import myutils
import System.Timers
import threading


class CanTp(object):
    def __init__(self, canif):
        self.Init()
        self.event_sink = None
        canif.event_sink = self.on_receive
        self.canif = canif
        self.timedout = False

    def Init(self):
        self.data_out = []
        self.data_in  = []
        self.seq_ctr  = 0
        self.first_frame_rcvd = False
        self.first_frame_sent = False

    def AppendData(self, data):
        #a = ' '.join( [ "%02X" % x for x in data ])
        #print a
        self.data_out.extend(data)
        
    def DecodeFrame(self, data_bytes):
        process_data = False
        frame_type = data_bytes[0] >> 4
        if frame_type == 0: # single frame
            self.data_in_dl = data_bytes[0] & 0xF
            self.data_in.extend(data_bytes[1:self.data_in_dl+1])
            process_data = True
        elif frame_type == 1: # first frame
            if frame_type == 1:
                self.data_in_dl = ((data_bytes[0] & 0xF) << 8) | data_bytes[1]    
            self.data_in.extend(data_bytes[2:self.data_in_dl+2])
            self.first_frame_rcvd = 1  
            self.exp_seq_ctr = 1  
        elif frame_type == 2 and self.first_frame_rcvd == 1: # consecutive frame
            seq_ctr = data_bytes[0] & 0xF
            if seq_ctr <> self.exp_seq_ctr:
                self.first_frame_rcvd = 0
            else:
                self.data_in.extend(data_bytes[1:8])
            while(len(self.data_in) > self.data_in_dl):
                # delete any excess data appended
                self.data_in.pop()
                process_data = True
            self.exp_seq_ctr = (self.exp_seq_ctr + 1) % 16
        elif frame_type == 3: # flow control frame
            self.data_out_BS = data_bytes[1]
            self.data_out_STMin = data_bytes[2]
        else:
            pass                    
        return(process_data)

    """ TODO: Handle more than 4095 bytes of data """
    def EncodeFrame(self):
        data_bytes = []
        if len(self.data_out) > 0:
            if self.first_frame_sent == True:
                self.seq_ctr = (self.seq_ctr + 1) % 16
                data_bytes.append((2 << 4) | self.seq_ctr)
                data_bytes.extend(self.data_out[:7])
                self.data_out = self.data_out[7:]
            else:
                if len(self.data_out) <= 7:
                    # single frame
                    data_bytes.append(len(self.data_out))
                    data_bytes.extend(self.data_out)
                    self.data_out = []
                else:
                    # first frame
                    data_bytes.append((1 << 4) | (len(self.data_out) >> 8))
                    data_bytes.append(len(self.data_out) & 0xFF)
                    data_bytes.extend(self.data_out[:6])
                    self.data_out = self.data_out[6:]
                    self.seq_ctr = 0
                    self.first_frame_sent = True
        return(data_bytes)

    def xmit(self, list):
        if myutils.debug_switch & 0x2 <> 0:
            for item in list: print '%02X' % int(item),
            print
        self.data_out = list
        self.active = True
        self.Task()
        
    def on_receive(self):
        myutils.debug_print(myutils.program_trace, "CanTp::on_receive")
        if self.canif.received_data[0] <> 0x30:
            if self.DecodeFrame(self.canif.received_data) == True:
                if self.event_sink <> None:
                    self.event_sink()
        else:
            print 'Flow control frame received.'

    def Task(self):
        #myutils.debug_print(myutils.program_trace, "CanTp::Task")        
        if self.active == True:
            can_data_bytes = self.EncodeFrame()
            if len(can_data_bytes) > 0:
                self.canif.xmit(can_data_bytes)
                self.timedout = False
            #    Method 1: Not working
            #    self.t = System.Timers.Timer(0.100)
            #    self.t.Elapsed += self.on_timeout
            #    Method 2: Not working
            #    timer = Timer()
            #    timer.Interval = 6000
            #    timer.Tick += self.on_timeout
            #    timer.Start()
            #    timer_id = timer.set_timer(1000, self.on_timeout) 
                #self.t = threading.Timer(0.05, self.on_stmin_tout) # 50 ms
                self.t = threading.Timer(0.1, self.on_stmin_tout) # 100 ms
                self.t.start()
                #self.t.join()                
            else:
                self.active = False
        #print self.timedout, self.active
        return self.active

    def on_stmin_tout(self):
        self.t.cancel()
        self.Task()


class CanTpTestSuite(unittest.TestCase):
    def setUp(self):
        self.ct = NewCanTp()

    """Verify receive of single frame"""
    def test1(self):
        self.ct.Init()
        self.ct.DecodeFrame([0x5, 1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(self.ct.data_in, [1, 2, 3, 4, 5], 'Single frame test')
        
    """Verify receive of multiple frames"""
    def test2(self):
        self.ct.Init()
        self.ct.DecodeFrame([0x10, 0xF, 1, 2, 3, 4, 5, 6])
        self.ct.DecodeFrame([0x21, 7, 8, 9, 0xA, 0xB, 0xC, 0xD])
        self.ct.DecodeFrame([0x22, 0xE, 0xF, 1, 2, 3])
        self.assertEqual(self.ct.data_in, [1, 2, 3, 4, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF])

    """Verify transmit of single frame"""
    def test3(self):
        self.ct.Init()
        self.ct.data_out = [1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(self.ct.EncodeFrame(), [0x7, 1, 2, 3, 4, 5, 6, 7])

    """Verify transmit of multiple frames"""
    def test4(self):
        self.ct.Init()
        self.ct.data_out = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual(self.ct.EncodeFrame(), [0x10, 8, 1, 2, 3, 4, 5, 6])
        self.assertEqual(self.ct.EncodeFrame(), [0x21, 7, 8])    

if __name__ == '__main__':
    unittest.main(exit=False)




