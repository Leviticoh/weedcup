import sys
import bencode
import pgp

with open(sys.argv[1], 'rb') as f:
    private_data = f.read()
privates = bencode.bdecode(private_data)

with open(sys.argv[2], 'rb') as f:
    public = f.read()

while len(public) > 0:
    packet = pgp.extract_packet(public)
    if packet['type'] in (pgp.PUBKEY, pgp.PUBSUBKEY):
        fpr = pgp.fingerprint_pub(packet['body'])
        body = packet['body'] + privates[fpr][1]
        if packet['type'] == pgp.PUBKEY:
            outp = pgp.build_packet_v4(pgp.SECKEY, body)
        else:
            outp = pgp.build_packet_v4(pgp.SECSUBKEY, body)
        sys.stdout.buffer.write(outp)
    else:
        sys.stdout.buffer.write(public[:packet['length']])
    public = public[packet['length']:]

