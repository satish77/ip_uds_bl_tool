class GM3110:
    def __init__(self):
        self.cantp = can_tp.CanTp()
        self.can_tx_rdy = True
        self.active = False

    def sm(self):
        debug_print(1, "UDS State Machine")
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
        self.cantp.AppendData(long_to_list(address))
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
