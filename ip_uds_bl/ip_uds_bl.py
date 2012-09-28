import SRecord
import can_if
import can_tp
import uds
import myutils
import System.Timers

#timer_expired = False

class MainClass:
    def __init__(self, load_n_go_addr, uds):
        self.states = { 'IDLE'              : 0, 
                        'START'             : 1, 
                        'UDS_TRANSFER_DATA' : 2, 
                        'UDS_TRANSFER_EXIT' : 3, 
                        'FLASH_PROGRAM'     : 4,  
                        'NEXT'              : 5 }
        self.state = self.states['IDLE']
        self.uds = uds
        self.flash_cmds = { 'ERASE':1, 'FLASH':2 }
        self.s19_cmds = { 'PROGRAM':1, 'DOWNLOAD':2 }
        self.load_n_go_addr = load_n_go_addr
        self.uds.receive_sink = self

    def on_rcv_data(self):
        if self.state <> self.states['IDLE']:
            self.Task()

    def DownloadS19(self, s19filename):
        """ Download S-Record file and optionally execute """
        s19file = open(s19filename)
        lines = s19file.readlines();
        s19file.close()
        self.sr = SRecord.SRecord()
        self.sr.readrecords(lines)
        if myutils.debug_switch & 0x1 <> 0:
            self.sr.print_chunks()
        data = self.sr.get_data()
        self.srec_idx = 0
        self.state = self.states['START']
        self.s19_cmd = self.s19_cmds['DOWNLOAD']
        self.Task()

    def ProgramS19(self, s19filename, target_address):
        s19file = open(s19filename)
        lines = s19file.readlines();
        s19file.close()
        self.sr = SRecord.SRecord()
        self.sr.readrecords(lines)
        if myutils.debug_switch & 0x1 <> 0:
            self.sr.print_chunks()
        data = self.sr.get_data()
        self.srec_idx = 0
        self.state = self.states['START']
        self.target_address = target_address
        self.s19_cmd = self.s19_cmds['PROGRAM']
        self.Task()

    def Task(self):
        assert self.state in self.states.values()
        assert self.s19_cmd in self.s19_cmds.values()

        if self.state == self.states['START']:
            data = self.sr.get_data()
            uds_data = []
            first_address = data[self.srec_idx][0]
            next_address  = data[self.srec_idx][0]
            # data size is limited to 1024 bytes eventhough 4095 is the protocol limit.
            # if the address of srecord is contiguous, then append it.
            while (self.srec_idx < len(data)) and (data[self.srec_idx][0] == next_address) and len(uds_data) < 1024:
                uds_data.extend(data[self.srec_idx][1])
                next_address = data[self.srec_idx][0] + len(data[self.srec_idx][1])
                self.srec_idx = self.srec_idx + 1
            if self.s19_cmd == self.s19_cmds['DOWNLOAD']:
                self.target_address = first_address
            self.uds.RequestDownload(self.target_address, uds_data)
            self.state = self.states['UDS_TRANSFER_DATA']            
        elif self.state == self.states['UDS_TRANSFER_DATA']:
            self.uds.TransferData()
            state = self.states['UDS_TRANSFER_EXIT']
        elif self.state == self.states['UDS_TRANSFER_EXIT']:
            self.uds.TransferExit()            
            if self.s19_cmd == self.s19_cmds['PROGRAM']:
                self.state = self.states['FLASH_PROGRAM']
            else:
                self.state = self.states['NEXT']
        elif self.state == self.states['FLASH_PROGRAM']:
            self.uds.RoutineControl(1, uds.routines['FLASHPROGRAM'])
            self.state = self.states['NEXT']
        elif self.state == self.states['NEXT']:
            data = self.sr.get_data()
            if self.srec_idx >= len(data):
                self.state = self.states['IDLE']
            else:
                self.target_address += len(uds_data)
            if (myutils.debug_switch & 0x8000) == 0x8000: # stop on first transfer
                self.state = self.states['IDLE']            

    def EraseFlashBock(self, block_idx, num_blocks):
        self.uds.RoutineControl(1, uds.routines['FLASHERASE'], block_idx, num_blocks) 

    def TransferSomeData(self, target_address, data):
        self.uds.RequestDownload(target_address, len(data))
        self.uds.TransferData(data)
        self.uds.RequestTransferExit()
    
"""
Steps:-
1. Download SBL
2. Execute LoadNgo(SBL) for erasing flash blocks.
3. Execute LoadNgo(SBL) after downloading each s19 block(contiguous records).

Fixed addresses:- 
1. Command Buffer 
2. LoadNGo routine
3. Code Buffer
"""

#command_buf_addr = 0xA0000000 # Data Scratchpad RAM (DSPR)
load_n_go_addr   = 0xB0000000 # Data Scratchpad RAM
code_buf_addr    = 0x70000000 # Program Scratchpad RAM (PSPR) in CPU0

#uds = UDS()
#uds.TransferAndGo(0x90000000, [])
#uds.RequestForDownload()

canif = can_if.CanIf()
cantp = can_tp.CanTp(canif)
uds   = uds.UDS(cantp)
#canif.event_sink = cantp.DecodeFrame;
#cantp.OnRxData(uds.
mc = MainClass(load_n_go_addr, uds)
mc.DownloadS19(r'C:\p\hgprojects\TC27XSBL\app\bin\AurixSBL.s19')
#mc.ProgramS19(r'C:\p\hgprojects\TC27XAppBuild\app\bin\AurixApp.s19', code_buf_addr)

#mc.TransferSomeData(code_buf_addr, [1, 2, 3, 4, 5, 6, 7, 8, 9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10, 0x11 ])

#for i in range(2):
#    if mc.state == mc.states['IDLE']:
#        break
#    else:
#        mc.Task()

try:
    while (mc.state <> mc.states['IDLE'] and (uds.timedout == False)):
        pass
    
    if uds.timedout == True:
        print "UDS timedout..."

finally:
    canif.rx_thread_active = False

#raw_input('Press any key to continue ...')
