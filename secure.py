import random

def pass_hash(f):
    a = 'kKm8MV6v1jJZzIiNnY4yTt0GgLlDdBbsSHh7cCXxf3FEeUu9Oo5WwaArRQ2qpP'
    b = ''
    c = 0
    d = 0
    e = 0
    for g in f:
        d = d + ord(g)
    while len(b) < 128:
        e = len(b) + len(f) + d + len(b)
        h = a[(c + a.find(f[c]) + d - c + e) % len(a)]
        b = b + h
        c = (c + 1) % len(f)

    return b

def salt():
    a = 'kKm8MV6v1jJZzIiNnY4yTt0GgLlDdBbsSHh7cCXxf3FEeUu9Oo5WwaArRQ2qpP'
    b = ''
    for c in range(5):
        b = b + a[random.randrange(len(a))]

    return b


