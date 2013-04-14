import json
from collections import defaultdict
from pprint import pprint

import pycosat


with open('index.json') as fi:
    index = json.load(fi)

v = {} # map fn to variable number
w = {} # map variable number to fn
for i, fn in enumerate(index.iterkeys()):
    v[fn] = i + 1
    w[i + 1] = fn

groups = defaultdict(list) # map name to list of filenames
for fn, info in index.iteritems():
    groups[info['name']].append(fn)

clauses = []

for filenames in groups.itervalues():
    # ensure packages with the same name conflict
    for fn1 in filenames:
        v1 = v[fn1]
        for fn2 in filenames:
            v2 = v[fn2]
            if v1 < v2:
                clauses.append([-v1, -v2])

def itergroup(name):
    for fn in groups[name]:
        info = index[fn]
        assert info['name'] == name
        yield fn, info

for fn1, info1 in index.iteritems():
    for r in info1['requires']:
        clause = [-v[fn1]]

        parts = r.split()
        while len(parts) < 3:
            parts.append(None)
        name, version, build = parts
        assert name and name != info1['name']
        if build is None and name == 'nose':
            version = None

        if version is None:
            assert build is None
            for fn2, unused_info in itergroup(name):
                clause.append(v[fn2])

        elif name in ('python', 'numpy') and len(version) == 3:
            assert build is None
            for fn2, info2 in itergroup(name):
                if info2['version'].startswith(version):
                    clause.append(v[fn2])

        elif build is None:
            for fn2, info2 in itergroup(name):
                if info2['version'] == version:
                    clause.append(v[fn2])

        else:
            fn2 = '%s-%s-%s.tar.bz2' % tuple(parts)
            clause.append(v[fn2])

        assert len(clause) > 1
        clauses.append(clause)


#pprint([' V '.join(('-' if i<0 else '') + w[abs(i)] for i in clause)
#        for clause in clauses])

clauses.append(None)
for fn in index:
    clauses[-1] = [v[fn]]
    sol = pycosat.solve(clauses)
    if not isinstance(sol, list):
        print fn, sol
        if not fn.startswith('anaconda-'):
            pprint(index[fn])
    #pprint(sorted(w[i] for i in sol if i > 0))
