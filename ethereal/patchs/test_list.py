#!/usr/bin/python

import time

def timeit(function):
    def capsule(*arg, **kw):
        start = time.time()
        try:
            return function(*arg, **kw)
        finally:
            global last_measure
            last_measure = time.time() - start
    return capsule

class Q:
    def __init__(self, i):
        self.m_name=i

    def name(self):
        return self.m_name

    def __repr__(self):
        return "Q(%s)" % self.m_name

class Q2:

    __slots__ = 'm_name'

    def __init__(self, i):
        self.__setstate__(i)

    def name(self):
        return self.m_name

    def __repr__(self):
        return "Q2(%s)" % repr(self.m_name)

    def __getstate__(self):
        return self.m_name

    def __setstate__(self, t):
        self.m_name = t

@timeit
def test(n, qs, function):
    for i in xrange(n):
        function(qs)

def list(dict):
    items = dict.values()
    nlist = [(x.name(), x) for x in items]
    nlist.sort()
    nlist = [val for (key, val) in nlist]
    #print nlist
    return nlist

def list2(dict):
    items = dict.values()
    items.sort(cmp=cmpQ)
    return items

def list3(dict):
    items = dict.values()
    items.sort(key=Q.name)
    return items

def list4(dict):
    items = dict.values()
    items.sort(key=Q2.name)
    return items

def cmpQ(x, y):
    return cmp(x.name(), y.name())

# Main
qs={}
for i in xrange(10000):
    qs[i]=Q(i)

n=100

for function in (list, list2, list3, list4):
    test(n, qs, function)
    print "%s => %f" % (function.__name__, last_measure)
