from sys import stderr

poly = 0b100011011



def addgf256(a, b):
    assert(a >= 0)
    assert(b >= 0)
    assert(a < 256)
    assert(b < 256)

    return a^b

def mulgf256_impl(a, b):
    assert(a >= 0)
    assert(b >= 0)
    assert(a < 256)
    assert(b < 256)

    acc = 0

    while b > 0:
        if b%2 == 1:
            acc ^= a
        a *= 2
        b //=2

    global poly
    tmp = (poly<<7)
    shift = 15

    while (acc & 0xff00) != 0:
        if ((acc >> shift) % 2) == 1:

            acc ^= tmp
        tmp >>= 1
        shift -= 1

    return acc

prods = [[mulgf256_impl(a,b) for a in range(256)] for b in range(256)]

def mulgf256(a, b):
    return prods[a][b]

def invert_gf256_impl(n):
    for i in range(256):
        if (mulgf256(n, i))==1:
            return i

inverses = [invert_gf256_impl(n) for n in range(1,256)]


def powgf256(a, b):
    assert(a >= 0)
    assert(b >= 0)
    assert(a < 256)
    assert(b < 256)

    acc = 1
    for _ in range(b):
        acc = mulgf256(acc, a)
    return acc

def invert_gf256(n):
    return inverses[n-1]


class mat_gf256:
    def __init__(self, M):
        self.mat = M

    def normalize_gf256(self, r):
        if self.mat[r][r] == 0:
            i = r
            while self.mat[i][r] == 0:
                i+=1
            for n, k in enumerate(self.mat[i]):
                self.mat[r] = addgf256(self.mat[r][n], k)
        factor = invert_gf256(self.mat[r][r])
        for i in range(len(self.mat[r])):
            self.mat[r][i] = mulgf256(self.mat[r][i], factor)

    def invert_mat_gf256(self):
        n_righe = len(self.mat)
        for i in range(n_righe):
            self.mat[i] += ([0]*i)
            self.mat[i].append(1)
            self.mat[i] += ([0]*(n_righe - 1 - i))

        for i in range(n_righe):
            self.normalize_gf256(i)
            for j in range(i+1, n_righe):
                factor = self.mat[j][i]
                for k, v in enumerate(self.mat[i]):
                    self.mat[j][k] = addgf256(self.mat[j][k], mulgf256(v, factor))

        for i in range(n_righe):
            for j in range(i):
                factor = self.mat[j][i]
                for k, v in enumerate(self.mat[i]):
                    self.mat[j][k] = addgf256(self.mat[j][k], mulgf256(v, factor))

        for i in range(n_righe):
            self.mat[i] = self.mat[i][n_righe:]

    def transpose(self):
        tmp = self.mat
        self.mat = []
        for i in range(len(tmp[0])):
            self.mat.append([])
            for r in tmp:
                self.mat[i].append(r[i])


def mul_mat_gf256(a, b):
    assert(len(a.mat[0])==len(b.mat))
    acc = []
    for i in range(len(a.mat)):
        acc.append([])
        for j in range(len(b.mat[0])):
            q = 0
            for k in range(len(b.mat)):
                q = addgf256(q, mulgf256(a.mat[i][k], b.mat[k][j]))
            acc[i].append(q)
    return mat_gf256(acc)


def gen_x_mat_gf256(lr,lc):
    r = []
    for i in range(lr):
        p = []
        for n in range(lc):
            p.append(powgf256(i, n))
        r.append(p)
    return mat_gf256(r)


def rs_encode_double(data):
    l = len(data)
    n = l*2
    assert(n <= 255)

    Y = mat_gf256([list(data)])
    Y.transpose()

    X = gen_x_mat_gf256(l, l)
    X.invert_mat_gf256()


    func = mul_mat_gf256(X, Y)

    X = gen_x_mat_gf256(n, l)
    enc = mul_mat_gf256(X, func)

    enc.transpose()

    out = enc.mat[0]
    return [bytes(out[:l]), bytes(out[l:])]

def rs_decode_double(rs_code):
    n = len(rs_code)
    qq = rs_code.copy()
    assert(n <= 255)
    l = n//2

    X = gen_x_mat_gf256(n, l)
    X.mat = [v for k, v in enumerate(X.mat) if rs_code[k] != None]

    rs_code = [ v for v in rs_code if v != None]
    rs_code = mat_gf256([rs_code])
    rs_code.transpose()

    if len(X.mat) >= l:
        X.mat = X.mat[:l]
    else:
        print(f"can't recover, too many errors, try making at least {l-len(X.mat)} of these pieces available", file=stderr)
        for i, v in enumerate(qq):
            if v==None:
                print(f"{i+1}/{l}", file=stderr)
        exit(1)

    X.invert_mat_gf256()

    first_codes = mat_gf256(rs_code.mat[:l])

    func = mul_mat_gf256(X, first_codes)

    X = gen_x_mat_gf256(l, l)
    dat = mul_mat_gf256(X, func)

    dat.transpose()

    return bytes(dat.mat[0])






