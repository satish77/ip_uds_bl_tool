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


#class MainClass:
#    def UDS_DownloadS19(s19file, Execute=False):
#        # wait for ?
#        if UDS_state == 1:
#            s19file = open(s19filename)
#            lines = s19file.readlines();
#            s19file.close()
#            sr = SRecord.SRecord()
#            sr.readrecords(lines)
#            if print_switch & 0x1 <> 0:
#                sr.print_chunks()
#            cantp = can_tp.CanTp()
#            data = sr.get_data()
#            srec_idx = 0            
#            next_address = data[0][0]
#            UDS_state = UDS_state + 1
#        elif UDS_state == START:
#            cantp.Init()
#            uds_header = [0x36]
#            if Execute == True:
#                uds_header.append(0x80)
#            else:
#                uds_header.append(0x00)
#            cantp.AppendData(uds_header)
#            cantp.AppendData(long_to_bytes(address))
#        elif UDS_state == 2:
#            # if the address of srecord is contiguous, then append it.
#            if data[srec_idx][0] == next_address:
#                cantp.AppendData(bytes)
#                next_address = address + len(bytes)                
#            else:
#                UDS_state = UDS_state + 1
#            # Check for more S-Records
#            srec_idx = srec_idx + 1
#            if srec_idx >= len(data):
#               UDS_state = UDS_state + 1
#        elif UDS_state == 3:
#            # Encode CAN frames
#            can_data_bytes = cantp.EncodeFrame()            
#            if len(can_data_bytes) == 0:
#                #UDS_Execute(sbl+LoadNgo)
#                UDS_state = UDS_state - 1
#            else:
#                can_xmit(can_data_bytes)
#                #Wait(STmin)
#        elif UDS_state == 4:                
#            can_data_bytes = cantp.EncodeFrame()            
#            cantp.Init()
#        """TODO: Append at the max 4095 - header data"""
#        else:
#            pass

"""
Download S-Record file and optionally execute
"""
#def UDS_Download(s19filename, Execute=False):
#    s19file = open(s19filename)
#    lines = s19file.readlines();
#    s19file.close()
#    sr = SRecord.SRecord()
#    sr.readrecords(lines)
#    if print_switch & 0x1 <> 0:
#        sr.print_chunks()

#    cantp = can_tp.CanTp()
#    data = sr.get_data()
#    next_address = 0 # assumes that 0 will not be the first address
#    for i in range(len(data)):
#        address = data[i][0]
#        bytes = data[i][1]        
#        """ If not contiguous data, send it out """
#        if next_address <> address:
#            can_data_bytes = cantp.EncodeFrame()
#            first_time = True
#            while len(can_data_bytes) > 0:
#                if first_time:
#                    can_xmit(can_data_bytes)
#                    first_time = False
#                #Wait(STmin)
#                can_data_bytes = cantp.EncodeFrame()
#            #UDS_Execute(sbl+LoadNgo)
#            cantp.Init()
#            uds_header = [0x36]
#            if Execute == True:
#                uds_header.append(0x80)
#            else:
#                uds_header.append(0x00)
#            cantp.AppendData(uds_header)
#            cantp.AppendData(long_to_bytes(address))
#        """TODO: Append at the max 4095 - header data"""
#        cantp.AppendData(bytes)
#        next_address = address + len(bytes)
#    # TODO: XMT any data left


#UDS_RequestForDownload()
#UDS_Download(sbl+LoadNgo)
#UDS_Download(r'C:\p\hgprojects\TC27XAppBuild\app\bin\AurixApp.s19')
#UDS_Download(AddressOfLoadNgo, True)

uds = UDS()
uds.TransferAndGo(0x90000000, [])
uds.RequestForDownload()


raw_input('Press any key to continue ...')