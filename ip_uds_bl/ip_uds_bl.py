import can_tp
import SRecord

print_switch = 0x3

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

"""
Download S-Record file and optionally execute
"""
def UDS_Download(s19filename, Execute=False):
    uds_header = [0x36]
    if Execute == True:
        uds_header.append(0x80)
    else:
        uds_header.append(0x00)

    s19file = open(s19filename)
    lines = s19file.readlines();
    s19file.close()
    sr = SRecord.SRecord()
    sr.readrecords(lines)
    if print_switch & 0x1 <> 0:
        sr.print_chunks()

    cantp = can_tp.CanTp()
    data = sr.get_data()
    for i in range(len(data)):
        address = data[i][0]
        bytes = data[i][1]
        cantp.Init()
        cantp.AppendData(uds_header)
        cantp.AppendData(long_to_bytes(address))
        cantp.AppendData(bytes)
        can_data_bytes = cantp.EncodeFrame()
        while len(can_data_bytes) > 0:
            can_xmit(can_data_bytes)
            #Wait(STmin)
            can_data_bytes = cantp.EncodeFrame()

def UDS_RequestForDownload():
    uds_header = [0x34]
    cantp = can_tp.CanTp()
    cantp.AppendData(uds_header)
    can_data_bytes = cantp.EncodeFrame()
    can_xmit(can_data_bytes)

#UDS_RequestForDownload()
UDS_Download(r'C:\p\hgprojects\TC27XAppBuild\app\bin\AurixApp.s19')

raw_input('Press any key to continue ...')