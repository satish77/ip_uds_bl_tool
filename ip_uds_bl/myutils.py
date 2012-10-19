# 0x0001 program Trace (function decorator ???)
# 0x0002 can_tp.xmit()
# 0x8000 Stop on first transfer
# 0x4000 CAN Messages
# 0x2000 UDS Timeout Disable
debug_switch = 0
program_trace = 0x0001
can_msg_trace = 0x4000

def debug_print(mask, msg):
    if debug_switch & mask != 0:
        print msg

def long_to_list(longdata):
    data =  [(longdata >> 24) & 0xFF]
    data += [(longdata >> 16) & 0xFF]
    data += [(longdata >>  8) & 0xFF]
    data += [(longdata >>  0) & 0xFF]        
    return(data)
