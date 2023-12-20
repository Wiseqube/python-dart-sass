
def read(readable):
    value = 0
    bits = 0
    
    while(True):
        buf = readable.read(1)
        byte = buf[0]
        value |= ((byte & 0x7f)) << bits
        bits += 7
        if byte < 0x80:
            break
    
    return value