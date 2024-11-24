import sys

def bencode(data):
    t = type(data)
    if t==type(""):
        return f"{len(data)}:{data}".encode()
    elif t==type(b""):
        return str(len(data)).encode() + b":" + data
    elif t==type(42):
        return f"i{data}e".encode()
    elif t==type([]):
        return b"l" + b"".join(map(bencode, data)) + b"e"
    elif t==type({}):
        a = [(k, v) for k, v in data.items()]
        a.sort(key=lambda x: x[0])
        return b"d" + b"".join([bencode(x[0])+bencode(x[1]) for x in a]) + b"e"
    else:
        print("[bencode/encode] wrong type provided", file=sys.stderr)
        return None

def _bdecode(blob: bytes) -> tuple:
    c = blob[:1]
    if c==b"i":
        parts=blob.partition(b"e")
        return (int(parts[0][1:]), parts[2])
    elif c==b"l":
        blob = blob[1:]
        ret = []
        while blob[:1] != b"e":
            r = _bdecode(blob)
            blob = r[1]
            ret.append(r[0])
        blob = blob[1:]
        return (ret, blob)
    elif c==b"d":
        blob = blob[1:]
        ret = {}
        while blob[:1] != b"e":
            r = _bdecode(blob)
            k = r[0]
            blob = r[1]
            r = _bdecode(blob)
            v = r[0]
            blob = r[1]
            ret[k] = v
        blob = blob[1:]
        return (ret, blob)
    elif c in b"0123456789":
        parts = blob.partition(b":")
        l = int(parts[0])
        ret = parts[2][:l]
        blob = parts[2][l:]
        return (ret, blob)
    else:
        return (None, None)

def bdecode(blob):
    return _bdecode(blob)[0]
