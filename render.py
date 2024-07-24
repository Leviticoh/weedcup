#from os import path
from sys import argv
from sys import stderr
import subprocess
import struct
from crc32c import crc32c
#from bencode import bencode
import base64
import errorCorrection

def mmToPoint(mm):
    return (mm*72)/25.4

def assemble_block(index, block_count, data):

    return bytes(base64.b64encode(data+struct.pack('B', block_count)+struct.pack('B', index)))

def drawtile(x,y,w,h, index, length, blob):
    out = "gsave\n"
    out += f"2 setlinewidth\n"
    out += f"{x} {y} {w} {h} rectstroke\n"
    out += f"{x+1} {y+1} translate\n"
    qr_content = assemble_block(index, length, blob)
    qr = subprocess.run(executable="/usr/bin/qrencode", args=["qrencode", "-lL", "-tEPS", "--inline", "--svg-path", "-s1"], capture_output=True, input=qr_content).stdout.decode()
    bbox = list(map(int,list(filter(lambda x: x.split()[0] == "%%BoundingBox:", qr.splitlines(False)))[0].split()[-4:]))
    scale = (h-2)/(bbox[3]-bbox[1])
    out += f"{scale} {scale} scale\n"
    out += qr
    out += "grestore\n"

    out += "gsave\n"
    out += "/Monospace 5 selectfont\n"

    for i, ch in enumerate([blob[n:n+8].hex(' ', 2).upper() for n in range(0,len(blob),8)]):
        out += f"{x+((bbox[2]-bbox[0])*scale)} {y-(7*i)+(h-14)} moveto\n"
        out += f"({ch}) show\n"

    out += f"{x+((bbox[2]-bbox[0])*scale)} {y+7} moveto\n"
    metadata = f"{index+1}/{length}"
    out += f"({metadata}) show\n"
    out += f"{x+((bbox[2]-bbox[0])*scale*1.35)-1} {y+7} moveto\n"
    metadata = "# " + struct.pack(">I", crc32c(struct.pack(">H", index) + blob)).hex().upper()
    out += f"({metadata}) show\n"
    out += "grestore\n"

    return out

A4 = (595, 842)

margins = {"left":   mmToPoint(5),
           "right":  mmToPoint(5),
           "top":    mmToPoint(5),
           "bottom": mmToPoint(5)}

data = []
data_len = 0

f = open(argv[1], 'rb')
while d := f.read(64):
    data_len += len(d)
    data.append(d)


blocks = []
checks = []

for i in range(len(data[0])):
    part = []
    for j in range(len(data)):
        if len(data[j]) > i:
            part.append(data[j][i])
    code = errorCorrection.rs_encode_double(bytes(part))
    print(f"{i+1}/64",file=stderr)
    blocks.append(code[0])
    checks.append(code[1])

blocks_qr = []
checks_qr = []
for i in range(len(blocks[0])):
    b = []
    for j in range(len(blocks)):
        if len(blocks[j]) > i:
            b.append(blocks[j][i])
    blocks_qr.append(bytes(b))

for i in range(len(checks[0])):
    b = []
    for j in range(len(checks)):
        if len(checks[j]) > i:
            b.append(checks[j][i])
    checks_qr.append(bytes(b))

w = (A4[0] - margins["left"] - margins["right"])/4
h = (A4[1] - margins["top"] - margins["bottom"])/10

x = x0 = margins["left"]
y = y0 = A4[1]-(margins["top"]+h)

doc_text = "%!PS\n" + \
f"<< /PageSize [{A4[0]} {A4[1]}] >> setpagedevice\n" + \
f"0 0 0 setcolor\n"

put = blocks_qr + checks_qr

for index,blob in enumerate(put):
    if (x+w)> A4[0]:
        x = x0
        y -= h
    if y < 0:
        y = y0
        doc_text += "\nshowpage\n"
    doc_text += drawtile(x, y, w, h, index, len(data), blob)
    x += w

doc_text += "\nshowpage\n"

print(doc_text)

