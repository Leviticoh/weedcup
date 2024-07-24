#from os import path
#from sys import argv
from sys import stderr
from sys import stdin
from sys import stdout
#import subprocess
import struct
#from crc32c import crc32c
#from bencode import bencode
import base64
import errorCorrection

def unpack_block(block):
    b = base64.b64decode(block)
    return {
        "blob": b[:-2],
        "count": struct.unpack("B", b[-2:-1])[0],
        "index": struct.unpack("B", b[-1:])[0]
        }

counts = {}
blocks = {}
b_len = 0

while r := stdin.readline():
    block = unpack_block(r)
    if block["count"] not in counts:
        counts[block["count"]] = 0
    counts[block["count"]] += 1
    blocks[block["index"]] = block["blob"]
    if len(block["blob"]) > b_len:
        b_len = len(block["blob"])

votes = 0
count = 0
for c in counts:
    if counts[c] > votes:
        votes = counts[c]
        count = c

sorted_blocks = [None]*count*2
for i in blocks:
    if i < (count*2):
        sorted_blocks[i] = blocks[i]

rs_codes = []

for i in range(b_len):
    code = []
    for b in sorted_blocks:
        if b != None:
            if len(b) > i:
                code.append(b[i])
        else:
            code.append(None)
    rs_codes.append(code)

#pieces = map(errorCorrection.rs_decode_double, rs_codes)

pieces = []
for i,c in enumerate(rs_codes):
    pieces.append(errorCorrection.rs_decode_double(c))
    print(f"{i+1}/{b_len}", file=stderr)

data = []
for i in range(len(pieces[0])):
    for p in pieces:
        if len(p) > i:
            data.append(p[i])


stdout.buffer.write(bytes(data))
