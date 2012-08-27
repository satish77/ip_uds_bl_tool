import unittest;

class NewCanTp:
    def NewCanTp(self):
        self.Init()

    def Init(self):
        self.data_out = []
        self.data_in  = []
        self.seq_ctr  = 0
        self.first_frame_rcvd = False
        self.first_frame_sent = False
        
    def DecodeFrame(self, data_bytes):
        process_data = False
        frame_type = data_bytes[0] >> 4
        if frame_type == 0: # single frame
            self.data_in_dl = data_bytes[0] & 0xF
            self.data_in.extend(data_bytes[1:self.data_in_dl+1])
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


class CanTp:
    def CanTp(self, OnNewdata):
        self.seq_ctr  = 0
        self.data_out = []
        self.data_in  = []
        self.OnNewData = OnNewData
        self.first_frame_rcvd = 0
        
    def OnRx(self, data_bytes):
        frame_type = data_bytes[0] >> 4
        if fame_type == 0: # single frame
            self.data_in.dl = data_bytes[0] & 0xF
            self.data_in.extend(data_bytes[1:])
        elif frame_type == 1: # first frame
            if frame_type == 1:
                self.data_in.dl = ((data_bytes[0] & 0xF) << 8) | data_bytes[1]    
            self.data_in.extend(data_bytes[2:])
            self.first_frame_rcvd = 1    
        elif frame_type == 2 and self.first_frame_rcvd == 1: # consecutive frame
            seq_ctr = data_bytes[0] >> 4
            if seq_ctr <> exp_seq_ctr:
                first_frame_rcvd = 0
            else:
                for i in range(2, 8): 
                    self.data_in.extend(data_bytes[i])
            if(len(data_in) >= data_in.dl):
                self.OnNewData(self.data_in)
        elif frame_type == 3: # flow control frame
            self.data_out.BS = data_bytes[1]
            self.data_out.STMin = data_bytes[2]
        else:
            pass

    def OnTx(self):
        # TODO: Check if previous xmt successful
        data_bytes = []
        if len(self.data_out) > 0:
            self.seq_ctr = (self.seq_ctr + 1) % 16
            data_bytes[0] = (2 << 4) | self.seq_ctr
            data_bytes.extend(self.data_out[:7])
            self.data_out.pop(7)
        #if len(self.data_out) > 0:
        #    StartTimer(self.data_out.STmin)       
        return(data_bytes)

    def TxData(self, data):
        #Initialize timer for STmin
        self.data_out = data
        data_bytes = []
        if len(self.data_out) <= 7:
            # single frame
            data_bytes[0] = len(self.data_out)
            data_bytes.extend(self.data_out)
            self.data_out = []
        else:
            # first frame
            data_bytes[0] = (1 << 4) | (len(self.data_out) >> 8)
            data_bytes[1] = len(self.data_out) & 0xFF
            data_bytes.extend(self.data_out[:6])
            self.data_out.pop(6)
            self.seq_ctr = 0
        #can.xmt(data_bytes)
        #StartTimer(self.data_out.STmin, OnTx)
        return(data_bytes)

class TestSuite(unittest.TestCase):
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

raw_input('Press any key to continue ...')