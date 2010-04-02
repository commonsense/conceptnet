from csc.nl.mblem import get_mblem
from collections import defaultdict

stems = defaultdict(lambda: defaultdict(list))

enm = get_mblem('en')
for line in open('enable'):
    word = line.strip()
    leaves = enm.lookup(enm.permute(word))
    for leaf in leaves:
        stem, _, _ = leaf.apply(word)
        if '?' in stem: continue
        stems[leaf.pos, leaf.inflections][stem].append(leaf.add+'+'+leaf.delete)

for posinfl, map in stems.items():
    pos, infl = posinfl
    out = open('en_unlem/%s.%s.train' % (pos, infl), 'w')
    for stem, leaves in map.items():
        items = list(stem[::-1])
        items = items[:20]
        items += ['='] * (20-len(items))
        items.append('|'.join(leaves))
        print >> out, ','.join(items)
    out.close()
