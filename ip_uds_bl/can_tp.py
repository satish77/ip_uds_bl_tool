import unittest;

class CanTp(object):
    def __init__(self):
        self.Init()

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




