import can_tp
import SRecord

print_switch = 0x3

def debug_print(mask, msg):
    if print_switch & mask != 0:
        print msg

def can_xmit(list):
    if print_switch & 0x2 <> 0:
        for item in list: print '%02X' % int(item),
        print

def long_to_bytes(longdata):
    data =  [(longdata >> 24) & 0xFF]
    data += [ (longdata >> 16) & 0xFF]
    data += [ (longdata >>  8) & 0xFF]
    data += [ (longdata >>  0) & 0xFF]        
    return(data)

UDS_state = 0

class UDS:
    def __init__(self):
        self.cantp = can_tp.CanTp()
        self.can_tx_rdy = True
        self.active = False

    def sm(self):
        debug_print(1, "sm")
        # TODO: set can_tx_rdy to True after STMIN and after sending previous message
        if self.can_tx_rdy and self.active == True:
            can_data_bytes = self.cantp.EncodeFrame()
            if len(can_data_bytes) > 0:
                can_xmit(can_data_bytes)
            else:
                self.active = False

    """ Transfers at the most 4095 bytes of data """
    def TransferAndGo(self, address, data, go=False):
        debug_print(1, "TransferAndGo")
        self.cantp.Init()
        uds_header = [0x36]
        if go == True:
            uds_header.append(0x80)
        else:
            uds_header.append(0x00)        
        self.cantp.AppendData(uds_header)
        self.cantp.AppendData(long_to_bytes(address))
        self.cantp.AppendData(data)
        self.active = True
        while self.active == True: self.sm()

    def RequestForDownload(self):
        debug_print(1, "RequestForDownload")
        uds_header = [0x34]
        self.cantp.Init()
        self.cantp.AppendData(uds_header)
        self.active = True
        while self.active == True: self.sm()


class MainClass:
    def __init__(self):
        self.states = { 'IDLE': 0, 'BUSY': 1 }
        self.state = self.states['IDLE']
        self.uds = UDS()

    """
    Download S-Record file and optionally execute
    """
    def DownloadS19(self, s19filename):
        s19file = open(s19filename)
        lines = s19file.readlines();
        s19file.close()
        self.sr = SRecord.SRecord()
        self.sr.readrecords(lines)
        if print_switch & 0x1 <> 0:
            self.sr.print_chunks()
        data = self.sr.get_data()
        self.srec_idx = 0
        self.state = self.states['BUSY']

    def Task(self):
        if self.state == self.states['BUSY']:
            data = self.sr.get_data()
            uds_data = []
            first_address = data[self.srec_idx][0]
            next_address  = data[self.srec_idx][0]
            # if the address of srecord is contiguous, then append it.
            while (self.srec_idx < len(data)) and (data[self.srec_idx][0] == next_address):
                uds_data.extend(data[self.srec_idx][1])
                next_address = data[self.srec_idx][0] + len(data[self.srec_idx][1])
                self.srec_idx = self.srec_idx + 1

            if self.srec_idx >= len(data):
                self.state = self.states['IDLE']
            self.uds.TransferAndGo(first_address, uds_data)


#uds = UDS()
#uds.TransferAndGo(0x90000000, [])
#uds.RequestForDownload()

mc = MainClass()
mc.DownloadS19(r'C:\p\hgprojects\TC27XAppBuild\app\bin\AurixApp.s19')

#for i in range(2):
#    if mc.state == mc.states['IDLE']:
#        break
#    else:
#        mc.Task()

while mc.state == mc.states['BUSY']: mc.Task()

raw_input('Press any key to continue ...')
