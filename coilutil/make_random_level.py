import random,pdb
from admin import boxify
rows=[]
fill_percent=1
rowlen=30
numrows=rowlen
from split_utils import *
#~ pdb.set_trace()
for rownum in range(numrows):
    row=''
    for n in range(rowlen):
        #~ print n,','

        if random.randrange(100)<fill_percent:
            row+='1'
        else:
            row+='0'
    row=[int(c) for c in row]
    rows.append(row)
boxify(rows)

def fill_alleys(rows):
    bad=True
    while bad:
        bad=False
        for xx in range(rowlen):
            for yy in range(numrows):
                pos=(xx,yy)
                #~ print 'pos is:',pos
                if isopen(rows,pos):
                    nei=[o for o in orth(pos) if isopen(rows,o)]
                    if len(nei)<2:
                        print 'filling',pos
                        rows[yy][xx]=1
                        bad=True


def show(rows):
    for r in rows:
        print ''.join([str(c) for c in r])
show(rows)
fill_alleys(rows)
print ''
show(rows)

