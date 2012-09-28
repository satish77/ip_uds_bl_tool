debug_switch = 0x8003

def debug_print(mask, msg):
    if debug_switch & mask != 0:
        print msg

def long_to_list(longdata):
    data =  [(longdata >> 24) & 0xFF]
    data += [(longdata >> 16) & 0xFF]
    data += [(longdata >>  8) & 0xFF]
    data += [(longdata >>  0) & 0xFF]        
    return(data)
