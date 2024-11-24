import pgp
import sys
import bencode


def get_keys_and_subkeys_secrets(data):
    dac = data
    out = {}
    while len(dac) > 0:
        packet = pgp.extract_packet(dac)
        dac = dac[packet['length']:]
        if packet['type'] not in (pgp.SECKEY, pgp.SECSUBKEY):
            continue
        tipo = ''
        if packet['type'] == pgp.SECKEY:
            tipo = 'chiave segreta'
        if packet['type'] == pgp.SECSUBKEY:
            tipo = 'sottochiave segreta'
        segreto = pgp.extract_secret(packet['body'])
        fpr = pgp.fingerprint_priv(packet['body'])
        out[fpr] = [packet['type'], segreto, segreto[0]]
    return out

key = sys.argv[1]

with open(key, 'rb') as f:
    cont = f.read()
sys.stdout.buffer.write(bencode.bencode(get_keys_and_subkeys_secrets(cont)))
