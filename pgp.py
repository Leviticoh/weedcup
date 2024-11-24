import struct
import sys
import hashlib

PKESK = 1
SIG = 2
SKESK = 3
OPS = 4
SECKEY = 5
PUBKEY = 6
SECSUBKEY = 7
COMP = 8
SED = 9
MARKER = 10
LIT = 11
TRUST = 12
UID = 13
PUBSUBKEY = 14
UAT = 17
SEIPD = 18

def error_eof(function):
    print(f"ERROR: input ended unecpectedly in '{function}'", file=sys.stderr)
    exit(1)

def mpi_decode(mpi):
    (l,) = struct.unpack('>H', mpi[:2])
    bl = (l+7)//8
    data = mpi[2:]
    if len(data) < bl:
        error_eof("mpi_decode")
    value = 0
    for n, b in enumerate(data[:bl]):
        if n == 0:
            if l%8 != 0:
                for i in range(l%8,8):
                    if b & (1<<i):
                        return (0, 'invalid')
                if not (b & (1 << ((l%8) - 1))):
                    return (0, 'invalid')
            elif not (b & (1 << 7)):
                return (0, 'invalid')
        value <<= 8
        value |= b

    return (l, value)

def body_len_v6(data):
    if data[0] < 192:
        return (1, data[0])
    if data[0] >= 192 and data[0] < 224:
        if len(data) < 2:
            error_eof("body_len")
        return (2,((data[0]-192) << 8) + data[1] + 192)
    if data[0] == 255:
        if len(data) < 5:
            error_eof("body_len")
        (val,) = struct.unpack('>I', data[1:5])
        return (5,val)
    return (None, 1, 1 << (data[0] & 0x1F))

def extract_packet_v6(data):
    packet_type = data[0]
    type_id = packet_type & 0b00111111
    length = body_len_v6(data[1:])
    body = data[length[0]+1:length[1]+length[0]+1]
    return {"type": type_id, "length": length[1] + length[0] + 1, "body": body}

def extract_packet_v4(data):
    packet_type = data[0]
    type_id = (packet_type & 0b00111100) >> 2
    length_type = packet_type & 0b00000011
    if length_type == 0:
        body_length = data[1]
        header_length = 2
    elif length_type == 1:
        (body_length,) = struct.unpack(">H", data[1:3])
        header_length = 3
    elif length_type == 2:
        (body_length,) = struct.unpack(">I", data[1:5])
        header_length = 5
    else:
        print("ERROR: version 4 packets with indeterminate length are not supported", file=sys.stderr)
        exit(1)
    if len(data) < (header_length + body_length):
        error_eof("extract_packet_v4")
    body = data[header_length:header_length+body_length]
    return {"type": type_id, "length": header_length + body_length, "body": body}

def encode_len_v4(l):
    if l < 256:
        return (0,struct.pack('B', l))
    elif l < 2**16:
        return (1,struct.pack('>H', l))
    elif l < 2**32:
        return (2,struct.pack('>I', l))
    else:
        return None

def extract_packet(data):
    packet_type = data[0]
    if not (packet_type & (1 << 7)):
        return {"error": "invalid"}
    if not (packet_type & (1 << 6)):
        return extract_packet_v4(data)
    return extract_packet_v6(data)

def build_packet_v4(id, body):
    tid = id << 2
    l = encode_len_v4(len(body))
    packet_type = 0b10000000 | tid | l[0]
    return struct.pack('B', packet_type) + l[1] + body

def extract_secret(packet):
    if packet[0] != 4:
        print("only version 4 keys are supported", file=sys.stderr)
        exit(1)

    algorithm = packet[5]
    body = packet[6:]
    if algorithm == 1: # RSA
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
    elif algorithm == 16: # elgamal
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
    elif algorithm == 17: # DSA
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
    elif algorithm == 18: # ECDH
        cl = body[0]
        body=body[cl+1:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
        cl = body[0]
        body=body[cl+1:]
    elif algorithm == 19 or algorithm == 22: # ECDSA or EdDSA
        cl = body[0]
        body=body[cl+1:]
        (l,_) = mpi_decode(body)
        bl = ((l+7)//8) + 2
        body = body[bl:]
    else:
        print("bambina, cosa mi hai dato da pappare!", file=sys.stderr)
        exit(1)
    return body

def fingerprint_priv(packet):
    secret = extract_secret(packet)
    publen = len(packet) - len(secret)
    pub = packet[:publen]
    return fingerprint_pub(pub)

def fingerprint_pub(packet):
    l = struct.pack(">H", len(packet))
    h = hashlib.sha1()
    h.update(bytes.fromhex('99'))
    h.update(l)
    h.update(packet)
    return h.digest()


