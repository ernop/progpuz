import random,pprint,os,time,copy,sys,traceback
import admin,config

def simple_getopen(rows):
    """just get the open positions in some rows, relative to UL == 0,0"""
    res=set([])
    x,y=len(rows[0]),len(rows)
    for yy in range(y):
        for xx in range(x):
            if rows[yy][xx]==0:
                res.add((xx,yy))
    return res

def floodfill_with_blocks(rows, start, blocks):
    """floodfill from start in rows, and also considering sqs in blocks to be filled."""
    newrows=[r[:] for r in rows]
    row_set_many(newrows, blocks)
    res=floodfill(newrows, start)
    return res

def flow_in_set(spots,start):
    """spots is a set of pos, floodfill within it from start."""
    tocheck=[]
    if start in spots:
        tocheck=set([start])
    res=set()
    while tocheck:
        th=tocheck.pop()
        res.add(th)
        for nei in orth(th):
            if nei in res:
                continue
            if nei in spots:
                tocheck.add(nei)
    return res

def flow_to_gates(rows,pos,envelop=False):
    """from pos, move 2x2 squares around step by step covering things.
    these are the room squares. return these, and call the adjacent squares the gates.

    later addition, not totally fixed: if there are two adjacent gates, add them and then remake stuff, until it settles.
    """
    sqs=set()
    tocheck=set([pos])
    checked=set()
    sqs.add(pos)
    while tocheck:
        this=tocheck.pop()
        if this in checked:
            continue
        checked.add(this)
        more=row2roomsqs(rows,this)
        if more:
            sqs.update(more)
            sqs.add(this)
            tocheck.update(more)
    gatesqs=set()
    changed=1
    while changed:
        changed=0
        for sq in sqs:
            gatesqs.update(set([nei for nei in orth(sq) if isopen(rows,nei) and nei not in sqs]))
        nears=0
        toadd=set()
        for gsq in gatesqs:
            parents=[n for n in orth(gsq) if n in sqs]
            if len(parents)>1:
                toadd.add(gsq)
        if toadd:
            changed=1
        for gsq in toadd:
            gatesqs.remove(gsq)
            sqs.add(gsq)
    changed=1
    while changed:
        changed=0
        for g in gatesqs:
            for g2 in gatesqs:
                if dist(g,g2)==1:
                    sqs.add(g)
                    sqs.add(g2)
                    more=row2roomsqs(rows,g)
                    sqs.update(more)
                    more=row2roomsqs(rows,g2)
                    sqs.update(more)
                    changed=1
        gatesqs=set()
        for sq in sqs:
            gatesqs.update([nei for nei in orth(sq) if isopen(rows,nei) and nei not in sqs])
    gates=set()
    for gatesq in gatesqs:
        outsqs=[n for n in orth(gatesq) if isopen(rows,n) and n not in sqs]
        gates.add((gatesq ,len(outsqs)))
    if envelop:
        sqs,gates=fix_enveloped(rows,sqs,gates)
    #in the unlucky event that two gates are adjacent, fix it up.
    return sqs,gates

def flow_to_req_gates(rows,pos,envelop=False):
    """floodfill, but don't pass through a tunnel.  just go to the first tunnel sq: that is, sq which has exactly two dvs
    envelop bit controls whether internal tunnels should be included too.
    """
    sqs=set()
    tunnelsqs=set()
    tocheck=set([pos])
    done=set()
    maxx=len(rows[0])-1
    maxy=len(rows)-1
    while tocheck:
        this=tocheck.pop()
        done.add(this)
        if isreqtunnel(rows,this):
            tunnelsqs.add(this)
            continue
        sqs.add(this)
        for pos in orth(this):
            if pos[0]<0 or pos[1]<0 or pos[0]>maxx or pos[1]>maxy:
                continue
            if pos in done:
                continue

            if isopen(rows,pos):
                tocheck.add(pos)
            else:
                done.add(this)
    gates=set()
    for t in tunnelsqs:
        outsqs=[n for n in orth(t) if isopen(rows,n) and n not in sqs]
        ns=len(outsqs)
        if ns==0:
            #it's an alley.
            ns=1
        gates.add((t,ns))
    if envelop:
        sqs,gates=fix_enveloped(rows,sqs,gates)
    return sqs,gates


def floodfill(rows,pos):
    """get plain old floodfills.

    this is used when splitting rooms into subrooms; get floodfills, then using the old known gates, mark those.  otherwise it's a pain.......

    also you don't have to rely on rows being actually filled in; include a set of 'excluded' squares which will be considered filled in already.

    also, if you include 'realrows', it will not flood past squares filled in realrows either.  so it will flood the OR of rows and realrows.
    that is used in make_subrooms so you dont have to modify the rows of a subroom - modify room rows on the top level,then
    take a subroom with its original squares and figure out what's leftover of it, given the state of the board rows.
    """
    sqs=set()
    tocheck=set([pos])
    done=set()
    while tocheck:
        this=tocheck.pop()
        done.add(this)
        sqs.add(this)
        for pos in orth(this):
            if pos in done:
                continue
            if isopen(rows,pos):
                tocheck.add(pos)
            else:
                done.add(this)
    return sqs



def split_on_parazones(rm):
    parasqs=rm2parasqs(rm)
    parazones=parasqs2parazones(parasqs)
    #check if these parazones can be used to split the room.
    subs=[]
    return subs

def fix_enveloped(rows,sqs,gates):
    """for a given set of sqs & gates in some rows, there are sometimes isolated internal reqtunnels.  this finds them and adds them.
    return sqs,gates, with the finished gates removed.
    this should really also just include rooms too.  makes more sense."""
    done=set()
    internals=set()
    removed_gates=set()
    for g in gates:
        gatesq=g[0]
        tunsqs,tunends=get_tunnelsqs_ends(rows,gatesq)
        external=False
        #~ print 'dealing with:',g,'tunends:',tunends
        if len(tunends)<2:
            external=True
        else:
            for tunend in tunends:
                if tunend not in sqs:
                    external=True
                    break
        if not external:
            removed_gates.add(g)
            for s in tunsqs:
                sqs.add(s)
    for g in removed_gates:
        gates.remove(g)
    return sqs,gates


def row2roomsqs(rows,pos):
    roomsqs=set()
    r=(pos[0]+1,pos[1])
    ro=isopen(rows,r)
    l=(pos[0]-1,pos[1])
    lo=isopen(rows,l)

    if ro or lo:
        u=(pos[0],pos[1]-1)
        uo=isopen(rows,u)
        d=(pos[0],pos[1]+1)
        do=isopen(rows,d)
    if ro:
        if uo:
            ur=(pos[0]+1,pos[1]-1)
            if isopen(rows,ur):
                roomsqs.update([u,r,ur])
        if do:
            dr=(pos[0]+1,pos[1]+1)
            if isopen(rows,dr):
                roomsqs.update([d,r,dr])
    if lo:
        if uo:
            ul=(pos[0]-1,pos[1]-1)
            if isopen(rows,ul):
                roomsqs.update([u,l,ul])
        if do:
            dl=(pos[0]-1,pos[1]+1)
            if isopen(rows,dl):
                roomsqs.update([d,l,dl])
    return roomsqs

def row_set_many(newrows, many):
    for pos in many:
        newrows[pos[1]][pos[0]]=1

def getopendvs(rows,pos):
    return [n for n in [0,1,2,3] if isopen(rows,add(pos,n))]

def isopen(rows,pos):
    return not rows[pos[1]][pos[0]]

def pos_in_rooms(pos,rooms):
    for rm in rooms:
        if pos in rm.orig_sqs:
            return True
    return False




def all_permutations(seq):
    """permutate a sequence and return a list of the permutations"""
    if not seq:
        return [seq] # is an empty sequence
    else:
        temp = []
        for k in range(len(seq)):
            part = seq[:k] + seq[k+1:]
            for m in all_permutations(part):
                temp.append(seq[k:k+1] + m)
    return temp

def isalley(board,pos):
    """only check orig open squares"""
    #pass#assert board.isopen(pos)
#~     assert (type(pos) is tuple),type(pos)
    #~ pdb.set_trace()
    return (board.isopen(pos) and len(board.getopendv_loc(pos))<=1)

def getorigalley(board):
    origalleys=[]
    for loc in innerboard(board.config):
        if board.isopen(loc) and isalley(board,loc):
            origalleys.append(loc)
    return origalleys

def dist_safe(a,b):
    if a is None or b is None: return None
    return dist(a,b)

def offset(a,offset_amount):
    if a==():
        return ()
    if type(a)==tuple and type(a[0])!=tuple:
        return (a[0]-offset_amount[0],a[1]-offset_amount[1])
    res=[offset(n,offset_amount) for n in a]
    return res

def dist(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def orth(pos):
    "4 orth sqs around pos"
    return [(pos[0]+1,pos[1]),(pos[0],pos[1]+1),(pos[0]-1,pos[1]),(pos[0],pos[1]-1)]
    #~ return (add(pos,n) for n in [0,1,2,3])

def makevec(loc,target):
    """ what's the vector from loc to target?  aka arcpos a2b"""
    res=(target[0]-loc[0],target[1]-loc[1])
    if res==(1,0):return 0
    elif res==(0,1):return 1
    elif res==(-1,0):return 2
    return 3
def find_pos_in_dict_to_list(pos, forced_paths):
    for k,v in forced_paths.items():
        if pos in v:
            return k
    import ipdb;ipdb.set_trace();print 'ipdb!'
def makevec2(a,b):
    if a=='IN':
        return a
    if b=='OUT':
        return b
    return makevec(a,b)

def add(loc,dv):
    dv=dv%4
    if dv==0:
        return (loc[0]+1,loc[1])
    if dv==1:
        return (loc[0],loc[1]+1)
    if dv==2:
        return (loc[0]-1,loc[1])
    else:
        return (loc[0],loc[1]-1)


def oob(config,pos):
    return pos[0]<0 or pos[1]<0 or pos[0]>config.maxx or pos[1]>config.maxy


def getsq():
    if random.choice([0,1,2])==2:
        return 1
    return 0
    #~ return random.choice([0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1])

def fullboard(config):
    for yy in range(config.maxy+1):
        for xx in range(config.maxx+1):
            yield (xx,yy)

def innerboard(config):
    for yy in range(1,config.maxy):
        for xx in range(1,config.maxx):
            yield (xx,yy)

def corners(config):
    for yy in [0,config.maxy+1]:
        for xx in [0,config.maxx+1]:
            yield (xx,yy)

def edges(config):
    okys=[0,config.maxy]
    okxs=[0,config.maxx]
    for yy in range(0,config.maxy+1):
        for xx in range(0,config.maxx+1):
            if yy in okys or xx in okxs:
                yield (xx,yy)

def tooclose_lists(a,b,mind):
        for e in a:
            for f in b:
                if dist(e,f)<mind:
                    return True
        return False

def get_allneighbors(config):
    #~ print 'getall'
    allneighbors={}
    for pos in innerboard(config):
        allneighbors[pos]=[]
        allneighbors[pos].extend([(pos[0]+1,pos[1]+n) for n in [-1,0,1]])
        allneighbors[pos].extend([(pos[0],pos[1]+n) for n in [-1,1]])
        allneighbors[pos].extend([(pos[0]-1,pos[1]+n) for n in [-1,0,1]])
    for pos in edges(config):
        allneighbors[pos]=[]
        allneighbors[pos].extend([(pos[0]+1,pos[1]+n) for n in [-1,0,1]])
        allneighbors[pos].extend([(pos[0],pos[1]+n) for n in [-1,1]])
        allneighbors[pos].extend([(pos[0]-1,pos[1]+n) for n in [-1,0,1]])
        allneighbors[pos]=[p for p in allneighbors[pos] if not oob(config,p)]
    return allneighbors

def mkglob(allneighbors,board,now):
    return glob(allneighbors,board,now,set())

def glob_list(allneighbors,board,now,found):
    print 'glob_LIST?'
    found.append(now)
    for pos in allneighbors[now]:
        if board.isopen(pos):continue
        if pos in found:continue
        found.extend(glob(allneighbors,board,pos,found))
    return found

def newglob(allneighbors,board,now,found):
    if now in found:
        return found
    found.add(now)
    for pos in allneighbors[now]:
        if board.isopen(pos):continue
        if pos in found:continue
        found.update(glob(allneighbors,board,pos,found))
    return found


def glob(allneighbors,board,now,found):
    st=time.time()
    """get plain old floodfills.

    this is used when splitting rooms into subrooms; get floodfills, then using the old known gates, mark those.  otherwise it's a pain.......
    """
    if now in found:

        res=found
    else:
        tocheck=set([now])
        maxx=len(board.rows[0])-1
        maxy=len(board.rows)-1
        while tocheck:
            this=tocheck.pop()
            found.add(this)
            for pos in allneighbors[this]:
                if pos in found:
                    continue
                if board.isopen(pos):
                    continue
                tocheck.add(pos)
        res=found
    #~ print 'newglob: %0.3f'%(time.time()-st)
    #~ assert og==found
    return res


def glob_diff(allneighbors,board,now,orig_glob):
    st=time.time()
    """
    instead of returning the new glob, just return the diff.  this should make it a lot easier to
    create extra_glob
    """
    new=set()
    if now in orig_glob:
        pass
    else:
        tocheck=set([now])
        maxx=len(board.rows[0])-1
        maxy=len(board.rows)-1
        while tocheck:
            this=tocheck.pop()
            new.add(this)
            for pos in allneighbors[this]:
                if pos in orig_glob:
                    continue
                if pos in new:
                    continue
                if board.isopen(pos):
                    continue
                tocheck.add(pos)
    #~ print 'newglob: %0.3f'%(time.time()-st)
    #~ assert og==found
    return new

def mkborders(config):
    """all orthogonal connected squares"""
    borders={}
    for pos in fullboard(config):
        if pos[0]==0 or pos[0]==config.maxx or pos[1]==0 or pos[1]==config.maxy:
            these=[add(pos,n) for n in [0,1,2,3] if not oob(config,add(pos,n))]
        else:
            these=[add(pos,n) for n in [0,1,2,3]]
        borders[pos]=these
    return borders



def isreqtunnel(rows,pos):
    """a reqtunnel is a spot with only two dvs, which must be traversed to connect
    the two neighbors.
    this is what really seems like a "tunnel".  triple intersections are not reqtunnels!
    """

    if not isopen(rows,pos):
        return False
    opendvs=getopendvs(rows,pos)
    if not opendvs:
        return True
    if len(opendvs)==1:
        return True
    if len(opendvs)>2:
        return False
    d1,d2=[add(pos,opendvs[0]), add(pos, opendvs[1])]
    if d1[0]==d2[0] or d1[1]==d2[1]:
        #opposite sides.
        return True
    #now it's a corner.
    oppsq=(d1[0]+(d2[0]-pos[0]),d1[1]+(d2[1]-pos[1]))
    if isopen(rows,oppsq):
        return False
    return True

def isdeeptunnel(rows,pos):
    """the naive way here won't work; tunnel != has exactly two dvs.  it should have two dvs, and the 4th sq
    of that meeting point can't be open! (otherwise it's just a corner!) deeptunnel is the inner part of a reqtunnel..
    but they also show up in corners of rooms."""
    dvs=[n for n in [0,1,2,3] if not oob(config, add(pos,n)) and isopen(rows,add(pos,n))]
    if len(dvs)==2:
        neighbors=[add(pos,d) for d in dvs]
        for nei in neighbors:
            neidvs=getopendvs(rows,nei)
            if len(neidvs)>2:
                return False
        return True
    else:
        return False

def get_tunnelsqs(rows,pos,seen=None):
    tun=set()
    if isreqtunnel(rows,pos):
        dvs=getopendvs(rows, pos)
        for dv in dvs:
            sqs,ends=get_tunnel_end_dv(rows,pos,dv)
            tun.update(sqs)
        tun.add(pos)
    return tun

def get_tunnelsqs_ends(rows,pos):
    tun=set()
    ends=set()
    if isreqtunnel(rows,pos):
        dvs=getopendvs(rows,pos)
        for dv in dvs:
            dvsqs,dvend=get_tunnel_end_dv(rows,pos,dv)
            if dvend:
                ends.add(dvend)
            tun.update(dvsqs)
        tun.add(pos)
    #~ print 'got tunnel at',pos,'had:',len(tun),tun,'had ends',ends
    return tun,ends



def get_tunnel_end_dv(rows,pos,dv):
    """given a pos and a dv, returns tunnel sqs, and end (end == first nontunnel sq).  not including initial square.  end is () if ends in alley"""
    tun=set()
    next=add(pos,dv)
    dvs=getopendvs(rows,next)
    while len(dvs)<=2:
        tun.add(next)
        dvs.remove((dv+2)%4)
        if not dvs:
            return tun,()
        dv=dvs.pop()
        next=add(next,dv)
        if next in tun:
            break
        dvs=[n for n in [0,1,2,3] if isopen(rows,add(next,n))]
    return tun,next

def divide_rows_into_rooms(rows,method,levelnum=None):
    st=time.time()
    donesqs=set()
    tunnelsqs=set()
    reqtunnelsqs=set()
    rooms=[]
    from simpleroom import mkroom
    maxx=len(rows[0])
    maxy=len(rows)
    for xx in range(maxx):
        for yy in range(maxy):
            pos=(xx,yy)
            #~ if pos==(10,3):
                #~ pdb.set_trace()
            if pos in donesqs:
                continue
            if not isopen(rows,pos):
                continue
            if isdeeptunnel(rows,pos):
                donesqs.add(pos)
                continue
            if isreqtunnel(rows,pos):
                reqtunnelsqs.add(pos)
                continue

            rm=mkroom(rows,pos,method=method,levelnum=levelnum)

            if not rm:
                tunnelsqs.add(pos)
                continue
            for lp in rm.sqs:
                donesqs.add(rm.local2global(lp))
            rm.mystart=None
            rm.timelimit=None
            rooms.append(rm)
            #~ rm.initrows()
    #~ print 'made %d %s in %0.4f'%(len(rooms),method,(time.time()-st))
    return rooms


def gsq2indv(rm,gatesq):
    for indv in range(4):
        nei=add(gatesq,indv)
        if nei in rm.orig_allsqs:
            return indv
    return None

perms={}

def perms_of_range_generator(rg):
    if len(rg) <=1:
        yield rg
    else:
        for perm in perms_of_range_generator(rg[1:]):
            for i in range(len(perm)+1):
                yield perm[:i] + rg[0:1] + perm[i:]

def all_permutations_of_range(rg, top=None):
    """permutate a sequence and return a list of the permutations"""
    if top:
        print 'ST',rg
    #~ print 'st',
    global perms
    if str(rg) in perms:
        #~ print 'cached',rg
        return [r[:] for r in perms[str(rg)]]
    #~ print 'new',rg
    if not rg:
        return [rg] # is an empty sequence
    else:
        temp = []
        for k in range(len(rg)):
            part = rg[:k] + rg[k+1:]
            for m in all_permutations_of_range(part):
                temp.append(rg[k:k+1] + m)
    #~ print '...end'
    perms[str(rg)]=temp
    if top:
        print 'END'
    return temp

def permutations_with_repeats(dct, level=None):
    """for a dict like {'a':2, 'b':1} ==> ((a,a,b),(a,b,a),(b,a,a))
    something like permutations with repeats.
    """
    if not level:
        level=1
    #~ print  level,'permutations_with_repeats',dct
    res=()
    if len(dct)==1:
        newdct=dct.copy()
        k,v=newdct.popitem()
        res=((k,)*v)
        #~ print res
        return (res,)
    for k,v in dct.items():
        #~ print 'looping k',k,'res is:',res
        if v>1:
            newdct=dct.copy()
            newdct[k]=newdct[k]-1
            res=res+key_before(k,permutations_with_repeats(newdct,level+1))
        elif v==1:
            newdct=dct.copy()
            newdct.pop(k)
            res=res+key_before(k,permutations_with_repeats(newdct,level+1))
        elif v==0:
            newdct=dct.copy()
            newdct.pop(k)
            res=res+permutations_with_repeats(newdct,level+1)
    return res

def key_before(k, res):
    newres=tuple([tuple((k,)+tuple(r)) for r in res])
    return newres

def all_permutations_of_sol_choices(dct):
    """return a new list of dicts dct with the lists replaced by one choice.
    so for {'a':[1,2], 'b':[1]} it'd return
    [{'a':1, 'b':1}, {'a':1,'b':2}]
    returns all the ways to choose one item from the incoming dicts.
    """
    counts={}
    for k,v in dct.items():
        counts[k]=len(v)
    keys=sorted(dct.keys())
    sollists=[dct[k] for k in keys]
    depths = make_depths(sollists)
    res=[]
    for ii,depth in enumerate(depths):
        rd={}
        for kk, d in enumerate(depth):
            rd[keys[kk]]=d
        res.append(rd)
    return res

def make_depths(lst):
    """receive a list of lists of choices.  return all possible choice combinations."""
    res=[]
    if len(lst)==1:
        #like [[1,2,3]] --> [[1],[2],[3],]
        return [[l] for l in lst[0]]
    newlst=list(lst)
    bb=newlst.pop(0)
    for ch in bb:
        res.extend(key_before(ch, make_depths(newlst)))
    return res

def getparasqs(board):
    """#for a given sq; sq is a parasq if:
    #   1. sq is empty
    #the vpath or hpath is clear on both sides.
    #first make v, h parasqs.  then combine v with v to make vzones, h with h for hzones.
    #v and h parasquares do not merge.  but later on, pararooms can be defined by some h, some v borders.
    #
    actually, these should also include blocks based on optgates which actually can't ever be followed - so, paying attention to hints.
    """
    parazones=[]
    vparasqs=set()
    hparasqs=set()
    bads=set()
    for sq in board.orig_open:
        bad=False
        vpath=board.get_vsqs(sq)
        for vsq in vpath:
            rv=add(vsq,0)
            if board.oob(rv) or not board.isopen(rv):
                bad=True
                break
            lv=add(vsq,2)
            if board.oob(lv) or not board.isopen(lv):
                bad=True
                break
        if not bad:
            inters=set(vpath).intersection(hparasqs)
            if inters:
                #vpath is good; we are para.
                bads.update(vpath)
                for h in inters:
                    bads.update(board.get_hsqs(h))
            else:
                vparasqs.update(vpath)
        bad=False
        hpath=board.get_hsqs(sq)
        for hsq in hpath:
            dv=add(hsq,1)
            if board.oob(dv) or not board.isopen(dv):
                bad=True
                break
            uv=add(hsq,3)
            if board.oob(uv) or not board.isopen(uv):
                bad=True
                break
        if not bad:
            inters=set(hpath).intersection(vparasqs)
            if inters:
                bads.update(hpath)
                for v in inters:
                    bads.update(board.get_vsqs(v))
            else:
                #~ #for now just skip intersection hpaths. (actually we should make 2 possible rooms for them)
                hparasqs.update(hpath)
    res=set()
    for sq in vparasqs:
        res.add(sq)
    for sq in hparasqs:
        res.add(sq)
    for badsq in bads:
        if badsq in res:
            res.remove(badsq)

    #a pzone like PPP is not valid!  PP, P, PPP/PPP are valid.
    bad_psqs=set()
    checked=set()
    for psq in res:
        if psq in checked:continue
        pzone=sorted(list(flow_in_set(res,psq)))
        checked.update(pzone)
        row=False
        twod=False
        xs,ys=[],[]

        #some things are always ok:
        if len(pzone)<3:
            continue

        #there are no intersecting zones, so just find top left / bottom right
        minx=min((p[0] for p in pzone))
        miny=min((p[1] for p in pzone))
        maxx=max((p[0] for p in pzone))
        maxy=max((p[1] for p in pzone))
        above=add((minx, miny),3)
        if board.isopen(above):
            facing='vert'
            #the pzone faces up or down
        else:
            facing='ho'
        if facing=='vert':
            width=maxx-minx+1
            depth=maxy-miny+1
        else:
            width=maxy-miny+1
            depth=maxx-minx+1
        #continue means we don't kill it.
        #by default kill except for the following exceptions.

        #OK means that it can only be solved with the correct parity - odd width things
        #require an odd number of exits and even, even.  if they have solutions that
        #allow both, they are not ok and should be killed (cause splitting there will generate
        #spurious borders, which will then be considered new (possibly illegal) rooms)
        if width==1 or width==2:
            #1,x is ok
            #2, x is ok
            continue
        if width==3:
            if depth>1:
                continue
                #3,2 is ok!
                #but 3,1 is not ok (first weird counterexample)
        if width==4:
            if depth>1:
                continue
        if width==5:
            if depth>2:
                continue
        if width==6:
            if depth>2:
                continue
                #6,2 -> 5,2 -> p(5,2) -> p(3,1) which is not ok

        #~ continue
        if depth>1:
            print 'KILLING LARGER PZONE w=%s d=%s sqs=%d facing=%s\n'%(width, depth, len(pzone), facing),
        #~ else:
            #~ print 'Kpz %d-%d'%(width, depth),
        open('parazones.txt','a').write('\n%s pzone width%d depth=%d   %s'%(facing, width, depth, str(pzone)))
        #~ print lens
        bad_psqs.update(pzone)
        #~ if len(pzone)<=2:
            #~ continue
        #~ #elif (len(pzone)%2)==1:
        #~ #else:
            #~ #continue
        #~ elif 1:
            #~ row=True
            #~ #if they're in a row vert or horizontal, kill them.
            #~ if pzone[0][0]==pzone[1][0]:
                #~ #vert
                #~ adder=(0,1)
            #~ elif pzone[0][1]==pzone[1][1]:
                #~ #horizontal
                #~ adder=(1,0)
            #~ else:
                #~ continue
            #~ last=None
            #~ for p in pzone:
                #~ if last and (p[0]+adder[0],p[1]+adder[1])==p:
                    #~ row=False
                    #~ break
                #~ last=p
            #~ ends=(pzone[0][0]-adder[0],pzone[0][1]-adder[1]),(adder[0]+pzone[-1][0],adder[1]+pzone[-1][1])

            #~ for e in ends:
                #~ if board.isopen(e):
                    #~ row=False
            #~ #also if it is going the wrong way, fix it.
            #~ #also, this does not exclude enough.   PPPPP/PPPPP ?  hmm, or maybe it is ok...
        #~ if row:
            #~ bad_psqs.update(pzone)
    for bpsq in bad_psqs:
        res.remove(bpsq)
    for pos in board.orig_open:
        if isreqtunnel(board.rows,pos):
            res.add(pos)
    #adding reqtunnel to parasqs......
    return set(res)
    #YOU cannot have intersecting parallels!  just kill them all!
    return vparasqs,hparasqs

def get_children(pos, hints):
    """based on hints from pos, get the list of positions you must visit.
    used for detecting illegal rooms where you bump your own child"""
    res=[pos]
    ii=0
    while len(hints[pos])==1:
        ii+=1
        if ii>10000:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            break
        pos=add(pos,list(hints[pos])[0][1])
        if pos in res:
            return False
        res.append(pos)
    return res

def get_ordered_forced_path(pos, hints):
    """a list, from start to finish."""
    #~ import ipdb;ipdb.set_trace();print 'ipdb!'

    startpos=pos
    res=[]
    if not len(hints[pos])==1:
        return res
    res.append(pos)
    #child
    while 1:
        if not hints[pos]:
            break
        pos=add(pos, list(hints[pos])[0][1])
        if not len(hints[pos])==1:
            break
        if pos in res:
            break
        res.append(pos)
        #~ if len(res)>1000:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    #parents
    res.reverse()
    pos=startpos
    while 1:
        pos=add(pos, list(hints[pos])[0][0]+2)
        if not len(hints[pos])==1:
            break
        if pos in res:
            break
        res.append(pos)
        #~ if len(res)>1000:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    res.reverse()

    return res

def get_forced_path(pos, hints):
    """go backwards and forwards from pos following unique hints

    obviously this misses cases where there are multiple hints, but they end up in the same place
    that's not implemented in better_prune yet anyway (but it should be sometime)
    """
    res=set()
    if not len(hints[pos])==1:
        return res
    #forwards
    ii=0
    while 1:
        ii+=1
        if ii>10000:
            print 'FAAAAR4'
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            break
        if not hints[pos]:break
        pos=add(pos, list(hints[pos])[0][1])
        res.add(pos)
        if not len(hints[pos])==1:
            break
    #backwards
    #this should actually promote to illegal - cause it means there is a hidden loop.
    ii=0
    while 1:
        ii+=1
        if ii>10000:
            print 'FAAAR5';
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            break
        if not hints[pos]:break
        pos=add(pos, list(hints[pos])[0][0]+2)
        res.add(pos)
        if not len(hints[pos])==1:
            break
    return res



def reqrm_at_end_of_tunnel(board, pos):
    ins=[]
    from simpleroom import mkroom
    allrooms=board.pos2allrooms(pos)
    reqrm=None
    for rm in allrooms:
        if not rm.kind=='reqrooms':
            continue
        if rm not in ins:
            ins.append(rm)
    if isreqtunnel(board.rows, pos):
        tunnelsqs, ends=get_tunnelsqs_ends(board.rows, pos)
        for e in ends:
            other_reqrm=board.pos2rooms[e].get('reqrooms',[])
            if other_reqrm:other_reqrm=other_reqrm[0]
            if other_reqrm not in ins:
                ins.append(other_reqrm)
    if ins:
        if len(ins)==1:
            reqrm=ins[0]
        else:
            reqrm=mkroom(rows=board.rows, pos=None, method='merge', extras={'rooms':ins})
    return reqrm

def merge_alley_into_room(board, alley, rm):
    """if there is an ilroom adn there is an alley, see if the alley+tunnel+flow,
    blocked by board, is a subset of the whole board

    if so merge alley into the room and viola!"""
    tilmeet=floodfill_with_blocks(board.rows,alley,rm.orig_allsqs)
        #this does not shortcircuit when hitting a block, so you reach the end.
    tocheck=board.endpos
    if not board.endpos:
        tocheck=board.start[0]
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    for o in orth(tocheck):
        if o in tilmeet:
            return 0
            #~ #if the flood of the alley is not dominated by tilmeet then it's bad!
    if len(tilmeet)+len(rm.orig_allsqs)>=board.curopen:
        return 0
        #no goods!
    #if tilmeet itnersects with an odd number of the gsqs of the ilroom, merge it.
    ct=0
    for gsq in board.air.orig_gatesqs:
        if set(orth(gsq)).intersection(tilmeet):
            ct+=1
    if ct%2==0:
        return 0
    #~ import ipdb;ipdb.set_trace();print 'ipdb!'

    rm.add_poss(tilmeet)
    rm.contained_alley=alley

    for gsq in rm.orig_gatesqs:
        if not board.isopen(gsq):continue
        ct=0
        for o in orth(gsq):
            if o in rm.orig_sqs:
                #dont want to kill double squares.  just detect gates that now touch 2 interior spaces.
                ct+=1
        if ct>1:
            #make this a normal square, not a gate.
            rm.add_poss(sqs=set([gsq]))
            rm.remove_poss(gatesqs=set([gsq]))
    board.alley=None
    return 1

def squarify(rows):
    ll=len(rows[0])
    for ii,r in enumerate(rows):
        rows[ii]=[1]+r+[1]
    rows.insert(0, [1]*(ll+2))
    rows.append([1]*(ll+2))
