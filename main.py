T=set(((0,0),(1,0),(1,1),(2,0)))
L=set(((0,0),(1,0),(2,0),(3,0)))

O=set([(0,0)])
L2=set(((0,0),(1,0)))

def sub(a,b):
   return (a[0]-b[0],a[1]-b[1])

def ULzero(shape):
    #move upper left square to zero
    minx=min([sq[0] for sq in shape])
    miny=min([sq[1] for sq in shape])
    return set([(sq[0]-minx,sq[1]-miny) for sq in shape])

def rot(shape):
   #rot x==>y,  y==>-x
   return set([(sq[1],-1*sq[0]) for sq in shape])

def flip(shape):
    #flip
   return set([(-1*sq[0],sq[1]) for sq in shape])

def fliprot(shape):
    res=[]
    for nn in range(2):
        for mm in range(4):
            res.append(shape)
            shape=rot(shape)
        shape=flip(shape)

    res2=[]
    for rr in res:
        rr=ULzero(rr)
        if rr in res2:
            continue
        res2.append(rr)
    return res2

def test_add(aa,bb):
    res=set()
    for shape in (aa,bb,):
        for sq in shape:
            if sq in res:
                return False
            res.add(sq)
    return res

def neighbors(s):
    return ((s[0]-1,s[1]),(s[0]+1,s[1]),(s[0],s[1]+1),(s[0],s[1]-1))

def translate(shape, coord):
    return set([(sq[0]+coord[0],sq[1]+coord[1]) for sq in shape])

def isempty(sq,shape):
    return sq not in shape

#all additions of T+L:
def all_combinations(s1,s2):
    possibles=[]
    for fr in fliprot(s1):
        for sq in fr:
            for neighbor in neighbors(sq):
                if isempty(neighbor,fr):
                    for s2sq in s2:
                        news2=translate(s2,sub(neighbor,s2sq))
                        #this is L, translated so that the filled square of L overlaps the empty, "neighbor" square of sq
                        combo=test_add(news2,fr)
                        if combo:
                            combo=ULzero(combo)
                            possibles.append(combo)
                        else:
                            continue
    p2=[]
    for pos in possibles:
        if pos in p2:
            continue
        p2.append(pos)
    return p2

def get_canonicals(shapes):
    res=[]
    for sh in shapes:
        can=get_canonical(sh)
        if can in res:
            continue
        res.append(can)
    return res

def get_canonical(shape):
    bestval=0
    best=None
    for shape in fliprot(shape):
        val=canonical_value(shape)
        if not bestval or val>bestval:
            best=shape
            bestval=val
    return best

def canonical_value(shape):
    shape2=ULzero(shape)
    import md5
    val=md5.md5(str(sorted(shape2))).hexdigest()
    return val

def canonical_value2(shape):
    shape2=ULzero(shape)
    val=0
    ii=0
    for xx in range(10):
        for yy in range(10):
            ii+=1
            if (xx,yy) in shape2:
                val+=2**ii
    return val


def show(shape):
    print '***********************'
    maxx=max([sq[0] for sq in shape])
    maxy=max([sq[1] for sq in shape])
    for yy in range(maxy+1):
        for xx in range(maxx+1):
            sq=(xx,yy)
            if sq in shape:
                print 'X',
            else:
                print '_',
        print '\n',
    print '======='

TT=set(((0,0),(1,0),))
LL=set(((0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0)))

O=set((0,0))

#~ def get_ns(n):
    #~ if n==1:
        #~ return [O]
    #~ elif n==2:
        #~ return
    #~ parents=all_
    #~ get_ns(n-1)

def get_single_combination(TT,LL):
    possibles=all_combinations(TT,LL)
    canonical=get_canonicals(possibles)
    canonical.sort(key=lambda x:canonical_value(x))
    return canonical

canonical=get_single_combination(LL,LL)
for ii,shape in enumerate(canonical):
    print ii
    show(shape)

