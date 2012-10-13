import sys
import System
import clr
clr.AddReferenceToFile("vxlapi_NET20.dll")
import vxlapi_NET20
clr.AddReferenceToFile("UnmanagedCode.dll")
import UnmanagedCode
import myutils


class CanIf:
    def __init__(self):
        self.cmd_id = 0x222
        self.rsp_id = 0x111
        self.timeout = 0
        self.rx_thread_active = True

        try:
            self.rxChannel = vxlapi_NET20.xlSingleChannelCAN_Port("py_canif", 0)
            self.txChannel = vxlapi_NET20.xlSingleChannelCAN_Port("py_canif", 0)
        
            if(self.txChannel.xlCheckPort() and self.rxChannel.xlCheckPort()):
                self.txChannel.xlPrintConfig();
                self.rxChannel.xlPrintConfig();
        
                self.rxChannel.xlResetAcceptanceFilter()
                self.rxChannel.xlCanAddAcceptanceRange(self.rsp_id, self.rsp_id)
        
                self.txChannel.xlActivate()
                self.rxChannel.xlActivate()
        
                self.rxThread = System.Threading.Thread(System.Threading.ThreadStart(self.rx_thread))
                self.rxThread.Start()      
                
                self.event_sink = None

        except:
            print "Exception occurred!!!"
            print sys.exc_info()[0], sys.exc_info()[1]
            #sys.exit(1)
    
    def xmit(self, list):
        if(len(list) > 0):
            data = 0
            for i in range(len(list)):
                data = (list[i] << (i*8)) | data
            print "%016X\n" % data
            self.txChannel.xlTransmit(self.cmd_id, len(list), data)

    def rx_thread(self):
        WaitResults = dict(
            WAIT_OBJECT_0   = 0x0,
            WAIT_ABANDONED  = 0x80,
            WAIT_TIMEOUT    = 0x102,
            INFINITE        = 0xFFFF,
            WAIT_FAILED     = 0xFFFFFFF)
            
        System.Threading.Thread.CurrentThread.Priority = System.Threading.ThreadPriority.Highest
        
        xld = vxlapi_NET20.XLDriver()
        print xld.XL_ResetClock(1)

        #raw_input("press any key..")
        
        """  three second timer - resolution is 10 us"""
        #xld.XL_SetTimerRate(0, 300000) 
        
        receivedEvent = vxlapi_NET20.XLClass.xl_event()
        xlStatus = vxlapi_NET20.XLClass.XLstatus.XL_SUCCESS
        
        while self.rx_thread_active:
            #waitResult = UnmanagedCode.Kernel32.WaitForSingleObject(self.rxChannel.eventHandle, WaitResults.get('INFINITE'))
            """ wait for the event for 10 ms """
            waitResult = UnmanagedCode.Kernel32.WaitForSingleObject(self.rxChannel.eventHandle, 10)
            if waitResult == WaitResults.get('WAIT_TIMEOUT'):
                self.timeout = 1
            else:
                self.timeout = 0
                xlStatus = self.rxChannel.xlReceive(receivedEvent)
                while xlStatus[0] != vxlapi_NET20.XLClass.XLstatus.XL_ERR_QUEUE_IS_EMPTY:
                #while xlStatus[0] == vxlapi_NET20.XLClass.XLstatus.XL_SUCCESS:                   
                    #print("received event")
                    #print xlStatus
                    #print int(vxlapi_NET20.XLClass.XLeventType.XL_RECEIVE_MSG)
                    if xlStatus[1].tag == 1:
                        #print 'XL_RECEIVE_MSG'
                        if (myutils.debug_switch & 0x1) == 0x1:
                            self.rxChannel.xlPrintRx(xlStatus[1])

                        # print the received message
                        #print 'id: 0x%02x' % xlStatus[1].tagData.can_Msg.id
                        #print 'dlc: ', xlStatus[1].tagData.can_Msg.dlc
                        #print 'data: ',                         
                        #for md in xlStatus[1].tagData.can_Msg.data:
                        #    print ' %02x' % md,
                        #print
                        #print 'flags: 0x%02x' % xlStatus[1].tagData.can_Msg.flags

                        if xlStatus[1].tagData.can_Msg.id == self.rsp_id:
                            self.rsp_received = 1

                            # convert from byte array to a string
                            self.received_data = []
                            for d in xlStatus[1].tagData.can_Msg.data:
                                self.received_data += [int(d)]

                            if self.received_data[0] <> 0xFF:
                                self.cmd_failed = 1
                            else:
                                self.cmd_failed = 0
                            
                            if self.event_sink <> None: 
                                self.event_sink()

                    elif xlStatus[1].tag == 4:
                        print 'XL_CHIP_STATE'
                    elif xlStatus[1].tag == 6:
                        print 'XL_TRANSCEIVER'
                    elif xlStatus[1].tag == 8:
                        print 'XL_TIMER'
                    elif xlStatus[1].tag == 10:
                        print 'XL_TRANSMIT_MSG'
                    elif xlStatus[1].tag == 11:
                        print 'XL_SYNC_PULSE'
                    elif xlStatus[1].tag == 15:
                        print 'XL_APPLICATION_NOTIFICATION'
                    else:
                        print "Unknown tag: " + str(xlStatus[1].tag)

                    #if xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_RECEIVE_MSG:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_RECEIVE_MSG'
                    #elif xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_CHIP_STATE:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_CHIP_STATE'
                    #elif xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_TRANSCEIVER:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_TRANSCEIVER'
                    #elif xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_TIMER:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_TIMER'
                    #elif xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_TRANSMIT_MSG:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_TRANSMIT_MSG'
                    #elif xlStatus[1].tag == vxlapi_NET20.XLClass.XLeventType.XL_SYNC_PULSE:
                    #    print 'vxlapi_NET20.XLClass.XLeventType.XL_SYNC_PULSE'

                    
                    xlStatus = self.rxChannel.xlReceive(receivedEvent)




