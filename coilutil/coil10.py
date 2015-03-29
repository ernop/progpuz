#ok, 05-28-late
#05-29 more

#06-06 added 1 x border,
#not copy table
#sett stuff is broken
#cansee2 broken

from coilconfig import *
from coilfunc import *
import Image,ImageFont,ImageDraw
import os,urllib,urllib2,time,types
time.clock()

try:
    import psyco
    psyco.full()
    print "psyco full"
except:
    print "NO PSYCO!"

global vectors
vectors=[(1,0),(0,1),(-1,0),(0,-1)]

import copy,traceback,time,os

def allsame(cchains,ccount):#,debug=False):
    for kk,v in cchains.items():
        if not len(v)==ccount:
            return 0
    return 1

        
class Walker2(object):
    __slots__=('tread','firstloc','loc','wallv','rtype','culd','bad')
    
    def __init__(self):
        self.tread={}
    
    def __str__(self):
        return "w:firstloc:"+str(self.firstloc)+"nowloc:"+str(self.loc)+"wallv:"+str(self.wallv)+" mytread"+repr(self.tread)
        
    def __repr__(self):
        return "w:firstloc:"+str(self.firstloc)+"nowloc:"+str(self.loc)+"wallv:"+str(self.wallv)+" mytread"+repr(self.tread)

class Walker(object):
    __slots__=('loc','rotcount','wallv','rtype','tread')
    def __init__(self,thiselement,rtype):
        self.rotcount=0
        self.loc=thiselement
        self.rtype=rtype
        self.tread={}

def merge(cchains,a,b):#,debug=False):
    a=abs(a)
    b=abs(b)
    newfriends=cchains[a]
    for e in cchains[b]:
        if e not in newfriends:
            newfriends.append(e)
    #
    nextchain=0
    todo=[]
    for kk,v in cchains.items():
        nextchain=0
        for e in newfriends:
            if e in v:
                todo.append(kk)
                nextchain=1
                break
        if nextchain:
            continue
    for kk in todo:
        for e in newfriends:
            if e not in cchains[kk]:
                cchains[kk].append(e)


def getfirsts(l):
    ret=[]
    for e in l:
        ret.append(e[0])
    return ret

def add(sum,d):
    return sum[0]+vectors[d%4][0],sum[1]+vectors[d%4][1]
    #if d%2==0:
        #return (sum[0]+vectors[d%4][0],sum[1]+vectors[d%4][1])
    #return (sum[0],sum[1]+vectors[d%4][1])

def getdist(p, o):
    res=abs(p[0]-o[0])+abs(p[1]-o[1])
    return res


def neighbors2x2ok(ns):
    #print "entered 2x2 with neighbors:",ns
    #and no relevant corners!
    #print "len, ns is",len(ns),ns
    #print "entered n2x2ok with",ns
    if len(ns)==0:
        print "WTF, neighbors 2x2 len(ns)==0"
        res="Impossible"
    elif len(ns)==1:
        res=1
    elif len(ns)==2:
        a=ns[0]
        b=ns[1]
        dist=getdist(a,b)
        if dist==1:
            res= 0
        elif dist==2:
            res=1
        elif dist==3:
            if a[0]==b[0]:
                res=1
            elif a[1]==b[1]:
                res=1
            else:
                res=0
        elif dist==4:
            res=1
    elif len(ns)==3:
        res=1
    else:
        print "len",len(ns)
        print "ns:",ns
        assert len(ns)==4
        a,b,c,d=ns
        res=0
        if a[0]==b[0] or b[0]==c[0] or c[0]==d[0] or d[0]==a[0]:
            res="Impossible"
        elif a[1]==b[1] or b[1]==c[1] or c[1]==d[1] or d[1]==a[1]:
            res="Impossible"
    #print "res is",res
    return res

def getchain(tofind):
    tocheck=[tofind[0],]
    done=[]
    thischain=[]
    while len(tocheck):
        if len(tofind)==0:
            break
        #print ""
        #print "tocheck:",tocheck
        #print "thischain",thischain
        #print "done",done
        #print "tofind",tofind
        pt=tocheck.pop()
        if pt in tofind:
            done.append(pt)
            thischain.append(pt)
            tofind.remove(pt)
        for n in range(4):
            potential=add(pt,n)
            if potential in done:
                continue
            if potential in tofind:
                #print "found",potential
                tofind.remove(potential)
                thischain.append(potential)
                tocheck.append(potential)
            #else:
                #print "missed",potential
            done.append(potential)

    #print "returning tofind",tofind,"thischain",thischain
    return tofind,thischain

global gallchains,gcount,gtot
gallchains={}

#gtot=0

def getchains(tofind):
    #finds chains in the keys of a dictionary, returns some dictionaries.
    hashable=str(tofind)
    if hashable in gallchains:
        res=gallchains[hashable]
    else:
        chains=[]
        bkup=copy.copy(tofind)
        tofind=tofind.keys()
        while len(tofind):
            #print "tofind is now:",tofind
            tofind,chain=getchain(tofind)
            #print "\ngot chain,tofind",chain,tofind
            chains.append(chain)
            #print "chains so far",chains
        fixedchains=[]
        for c in chains:
            fixedchain={}
            for e in c:
                fixedchain[e]=bkup[e]
            fixedchains.append(fixedchain)
        res=fixedchains
        gallchains[hashable]=fixedchains
    return res

class Board(object):
    __slots__=('realmoves','death_counts','nowstore','culstore','thismove','culdesacs','depth','done','btracks','level','still_todo','initialopen','todo','justmoved_d','justmoved','corners','now','aff','currentalleys','lastdv','remaining','maxy','maxx','hy','hx','rows')
    def __init__(self):
        self.now=None
        self.realmoves=[]
        self.depth=0
        self.aff={}
        self.currentalleys=[]
        self.lastdv=None
        self.clearbtracks()
        self.culdesacs=[]
        self.justmoved=[]
        self.nowstore=[]
        self.culstore=[]

    def clearbtracks(self):
        self.btracks={'cds':0,'cdas':0,'alleycul':0,'alley':0,'split':0,'deadend':0,'ibox':0,'done':0,'assigned':0,'deeptunnel':0}
        #print "set btracks,",self.btracks

    def start(self,text):
        self.readboard(text)
        self.remaining=0
        for l in self.rows:
            for c in l:
                if c==0: self.remaining+=1
        self.maxx=len(self.rows[0])
        self.maxy=len(self.rows)
        self.corners=[(0,0),(0,self.maxy),(self.maxy,0),(self.maxx,self.maxy),]
        self.hx=self.maxx/2
        self.hy=self.maxy/2
        
    def readboard(self,text):
        tsp=text.split()
        self.rows=[]
        origlen=len(tsp[0])
        all1row=[]
        for e in range(origlen+2):
            all1row.append(1)
        self.rows.append(all1row)
        for l in tsp:
            thisrow=[1,]
            l=l.strip()
            if l.isspace(): continue
            for c in l:
                thisrow.append(int(c))
            thisrow.append(1)
            self.rows.append(thisrow)
        self.rows.append(all1row)
        #print "made board:"
        #for r in self.rows:
            #print r
        
    def show(self,spec=[]):
        for y,l in enumerate(self.rows):
            tr=''
            try:
                nn=self.now
            except:
                traceback.print_exc()
                nn=None
            for x,c in enumerate(l):
                if (x,y)==nn:
                    tr+="N"
                    continue
                elif (x,y) in spec:
                    tr+="X"
                    continue
                tr+=str(c)
            print tr

    def cleana(self):
        st=len(self.aff)
        #print "cleaning len",len(self.aff),
        newa={}
        for k,v in self.aff.items():
            if not self.check(k):
                newa[k]=v
            else:
                print "X"
        self.aff=newa
        #print len(newa)
   
    def set(self):
        x,y=self.now
        if self.rows[y][x]==1:
            pass
            #print "bad set"
        else:
            self.rows[y][x]=1
            self.remaining=self.remaining-1
        
    def unset_loc_test(self,e):
        if self.rows[e[1]][e[0]]==1:
            self.rows[e[1]][e[0]]=0
            self.remaining=self.remaining+1
        #else:
            #print "unset_loc problem"

    def unset(self):
        if self.rows[self.now[1]][self.now[0]]==0:
            print "bad unset"
        else:
            self.rows[self.now[1]][self.now[0]]=0
        #print "set ",self.now[0],self.now[1]
            self.remaining=self.remaining+1

    def unset_many(self,tounset):
        for e in tounset:
            self.unset_loc_test(e)

    def check(self,loc):
        return self.rows[loc[1]][loc[0]]
        
    def addnow(self,d):
        #if d%2==0:
            #return (self.now[0]+vectors[d%4][0],self.now[1])
        #return (self.now[0],self.now[1]+vectors[d%4][1])
        x,y=self.now
        return x+vectors[d%4][0],y+vectors[d%4][1]

    def getdvs_loc(self,loc):
        goods=[]
        for n in range(4):
            if not self.check(add(loc,n)):
                goods.append(n)
        return goods
    
    def getdvs_lastdv(self):
        goods=[]
        possdvs=(self.lastdv+1,self.lastdv-1)
        for dv in possdvs:
            if not self.check(self.addnow(dv)):
                goods.append(dv)
        return goods
        
    def getdvs(self):
        #print "getting dvs of",self.now
        #for r in self.rows:
            #print r
        goods=[]
        for n in range(4):
            tocheck=self.addnow(n)
            #print "about to check:",tocheck
            if not self.check(tocheck):
                #print tocheck,"ok"
                goods.append(n)
                #print "goods is:",goods
        #print "in the end, goods is:",goods
        return goods
    def getneighbors(self,loc=None):
        goods=[]
        if loc==None:
            loc=self.now
        for n in range(4):
            this=add(loc,n)
            if not self.check(this):
                goods.append(this)
        return goods

    def getopen(self,dosort=0):
        death_counts={}
        for y,r in enumerate(self.rows):
            for x,val in enumerate(r):
                if val==0:
                    n=len(self.getneighbors((x,y)))
                    if n==1:
                        death_counts[(x,y)]=10000000
                        self.currentalleys.append((x,y))
                    if n==2:
                        death_counts[(x,y)]=3
                    if n==3:
                        death_counts[(x,y)]=250
                    if n==4:
                        death_counts[(x,y)]=500
        return death_counts
    
    def isdeeptunnel(self,x):
        n=self.getneighbors(x)
        if not len(n)==2:return 0
        for e in n:
            if not len(self.getneighbors(e))==2:
                return 0
        #print "x was deep tunnel",x
        return 1

    def chooseone(self,aff):
        bestdist=1000
        for l,vec in aff.items():
            for c in self.corners:
                dist=getdist(l,c)
                if dist<bestdist:
                    bestl,bestvec=l,vec
                    bestdist=dist
                    if dist<self.hx and dist<self.hy:
                        break
        return bestl,bestvec
        
    def wallwalk(self,loc,wallv,rotcount,rtype):
        walll=add(loc,wallv)
        #if walking on air:
        if not self.check(walll):
            loc=walll
            wallv=wallv-rtype
            return loc,wallv,0
        prefl=add(loc,wallv+rtype)
        #if blocked
        if self.check(prefl):
            wallv=wallv+rtype
            return loc,wallv,rotcount+1
        #no problems
        loc=prefl
        return loc,wallv,0

    def cansee3(self):
#~         debug=0
        #if self.now==(13,7):
            #if self.remaining==29:
                #print "at bad point!"
                #debug=1
        #self.cleana()
        goal=self.aff.keys()
        if len(goal)==0:
            return 1
        chains=getchains(self.aff)
        walkers={}
        cchains={}
        cwlocs={}
        awlocs={}
        for kk,e in enumerate(chains):
            tk=kk+1
            cchains[tk]=[tk]
        for i,c in enumerate(chains):
#~             if debug:
#~                 text="chain "+str(i+1)+" len,s is:"+str(len(c))+repr(c)
#~                 pshow(self,c,imgtext=text,save=1)
#~                 
            thiselement,thisvec=c.popitem()
            t=i+1
            rtype=1
            w1=Walker(thiselement,rtype)
            w1.wallv=thisvec+2
            cwlocs[thiselement]=t
            nt=t*-1
            rtype=-1
            walkers[t]=w1
            w2=Walker(thiselement,rtype)
            w2.wallv=thisvec+2
            awlocs[thiselement]=nt
            walkers[nt]=w2
        gotresult=0
        while gotresult==0:
            
            if allsame(cchains,len(chains)):
                result=1
                reason='found all'
                break
            thistimeremove=[]
            for k,w in walkers.items():
                
                if k in thistimeremove:
                    continue
                place=w.loc
                if w.rotcount==0:
                    if place in w.tread :
                        w.tread[place]+=1
                    else:
                        w.tread[place]=1
                if w.tread[place]>3:
                    result=0
                    reason='overtread'
                    gotresult=1
                    break
                
                if w.rotcount>3:
                    gotresult=1
                    result=0
                    reason='toorot'
                    break
                met=0
                if k>0:
                    if place in awlocs:
                        met=1
                        other=awlocs[place]
                else:
                    if place in cwlocs:
                        met=1
                        other=cwlocs[place]
                if met:
                    if not (other)== ((-1*k)):
                        
                        merge(cchains,k,other)
#~                         if debug:
#~                             print ""
#~                             print "walker ",k," met walker",other,"merging chains"
#~                             for c in cchains:
#~                                 print c
#~                             for c in chains:
#~                                 print c
                        thistimeremove.append(k)
                        thistimeremove.append(other)
                w.loc,w.wallv,w.rotcount=self.wallwalk(w.loc,w.wallv,w.rotcount,w.rtype)
                if w.rotcount>0:
                    if k>0:
                        cwlocs[place]=None
                        cwlocs[w.loc]=k
                    else:
                        awlocs[place]=None
                        awlocs[w.loc]=k
            if gotresult:
                break
            for e in thistimeremove:
                if e in walkers:
                    walkers.pop(e)
            if len(walkers)==0:
                #DUH
                if allsame(cchains,len(chains)):
                    result=1
                    reason='nowalkers,allsame'
                    gotresult=1
                    break#print "no walkers left..."
                gotresult=1
                result=1
                reason='nowalkers, not allsame'
#~                 if debug:
#~                     print "ran out of walkers, cchains are"
#~                     for c in cchains:
#~                         print c
#~                     for c in chains:
#~                         print c
#~                     print reason
#~                 
        #if result==0:
            #print "got result",result
            
        return result,reason
    
    def cansee(self):
        #print "self aff is",self.aff
        tofind=copy.copy(self.aff.keys())
        #self.show(self.aff)
        
        first,wallv=self.chooseone(self.aff)
        wallv+=2
        rtype=1
        tofind.remove(first)
        this=first
        rotcount=0
        
        rotated=0
        done={}
        #print "wallv is",wallv
        while len(tofind):
            l,wallv,rotcount=self.wallwalk(this,wallv,rotcount,rtype)
#~             debug=0
            if l in tofind:
                tofind.remove(l)
            if rotcount>5:
                res=0
                return res
            if not l==this:
                if l in tofind:
                    tofind.remove(l)
                nn=done.get(l,0)
                if nn==1:
                    done[l]=2
                elif nn==2:
                    done[l]=3
                elif nn==3:
                    res=0
                    return res
                else:
                    done[l]=1
                this=l
        res=1
        return res
   
    def isalley(self,x):
        if not self.check(x):
            if len(self.getneighbors(x))==1:
                return 1
        return 0

    def istunnel(self,loc):
        #print "loc is",loc
        #print "check loc is:",self.check(loc)
        dvs=self.getdvs_loc(loc)
        #print "dvs of loc are",dvs
        if len(dvs)==2:
            a,b=dvs
            #make sure it's not a corner angle
            if ((a+1)%4==b) or ((a-1)%4==b):
                if not self.check(add(add(loc,a),b)):
                    return 0
            return 1
        return 0
            

    def get_blanks(self,ns):
        goods=[]
        for n in ns:
            if not self.check(n):
                goods.append(n)
                continue
        return goods
            
    def countalleys2(self):
        #print "entered countalleys with affected:",self.aff.keys()
        #pshow(self,self.aff.keys())
        tempaff=self.aff.keys()
        alleys=[]
        done=[]
        while len(tempaff):
            e=tempaff.pop()
            if e in done:
                continue
            elif len(self.getdvs_loc(e))<3:
                for el in self.getneighbors(e):
                    if not el in done:
                        if not el in tempaff:
                            tempaff.append(el)
                done.append(e)
            if self.isalley(e):
                if e not in alleys:
                    alleys.append(e)
        return alleys
   
    def doalleys(self):
        alleys=self.countalleys2()
        #print "now I am at",self.now
        #print "got alleys",alleys
        #print "and currentalleys is",self.currentalleys
        nearalleys=[]
        for e in alleys:
            if e not in self.currentalleys:
                self.currentalleys.append(e)
        #print "merged",self.currentalleys
        toremove=[]
        for e in self.currentalleys:
            #print "checking",e
            if not self.isalley(e):
                #print "found e:",e,"to not be an alley"
                toremove.append(e)
            #else:
                #print "found e:",e,"to still be an alley"
                #pshow(self,e)
        for b in toremove:
            self.currentalleys.remove(b)
        #print "cleaned",self.currentalleys
        for e in self.currentalleys:
            if getdist(e,self.now)==1:
                #print "but it was close"
                #print "returning currentalleys:",self.currentalleys[1:]
                #pshow(self,self.currentalleys[1:])
                nearalleys.append(e)
                #self.currentalleys.remove(e)
        #print "returning currentalleys:",self.currentalleys
        #pshow(self,self.currentalleys)
        return self.currentalleys,nearalleys

    def move(self,dv):
        self.justmoved_d.append(dv)
        
        self.thismove.append(self.now)
        dvs=self.getdvs()
        #print repr(dvs)
        for edv in dvs:
            if edv==dv: continue
            tt=self.addnow(edv)
            if not self.check(tt):
                self.aff[tt]=edv
        now=add(self.now,dv)
        self.now=now
        
        self.thismove.append(now)
        if self.now in self.aff:
            self.aff.pop(now)
        #print "setting in move init"
        self.set()
        next=self.addnow(dv)
        while not self.check(next):
            self.thismove.append(next)
            #print "going",getd(dv)
            cv=dv+1
            acv=dv-1
            affcv=add(now,cv)
            affacv=add(now,acv)
            for a,b in [(affcv,cv),(affacv,acv)]:
                if not self.check(a):
                    self.aff[a]=b
            this=next
            self.now=this
            now=this
            if this in self.aff:
                self.aff.pop(this)
            #print "setting in move loop"
            self.set()
            next=self.addnow(dv)
        self.thismove.append(now)
    
    def multimove(self,dv):
        self.thismove=[]
        self.realmoves.append(dv)
        #print "starting multimove"
        #pshow(self)
        #print "\nin multimove"
        startloc=copy.deepcopy(self.now)
        self.justmoved_d=[]
        self.aff={}
        self.lastdv=dv
        #print repr(dv)
        #print "setting in multimove"
        self.set()
        self.move(dv)
        
        dvs=self.getdvs_lastdv()
        #print repr(dvs)
        while len(dvs)==1:
            dv=dvs[0]
            self.move(dv)
            self.lastdv=dv
            dvs=self.getdvs_lastdv()
        
        #cleanup
        dvs=self.getdvs_lastdv()
        for edv in dvs:
            if edv==dv: continue
            tt=self.addnow(edv)
            if not self.check(tt):
                self.aff[tt]=edv
        self.justmoved.append(self.thismove)
        #print "at end of multimove, with affected:"
        #pshow(self,self.aff.keys())
        #for m in self.justmoved:
            #print m
        
        

    def fork(self,sol):
        #print self.depth
        #print "FORK"
        dvs=self.getdvs()
        #origrows=copy.deepcopy(self.rows)
        #orignow=copy.deepcopy(self.now)
        while len(dvs):
            #print "original:"
            #pshow(self)
            dv=dvs.pop()
            self.aff={}
            tsol=copy.deepcopy(sol)
            self.nowstore.append(copy.deepcopy(self.now))
            self.culstore.append(copy.deepcopy(self.culdesacs))
            self.todo=dv
            #print "checking dv",dv
            self.btracks=self.do(tsol)
            if gshowbacktracks:
                
                if not self.btracks['reason']=='backtrack':
                    print ""
                    print "now at:",self.now
                    print "reason",self.btracks['reason']
                    print "relevant:",self.btracks['relevant']
            if gsavebacktracks:
                #if not self.btracks['reason']=='split':
                    #continue
                if not self.btracks['reason']=='backtrack':
                    text=''
                    text+="now at:"+repr(self.now)+"\n"
                    text+="reason"+self.btracks['reason']+"\n"
                    text+="relevant:"+repr(self.btracks['relevant'])+"\n"
                    #print "text is:",text
                    pshow(self,self.btracks['relevant'],imgtext=text,save=1)
            
            
            tounset=self.justmoved.pop()
            self.unset_many(tounset)
            self.unset_many([self.now])
            self.now=self.nowstore.pop()
            self.culdesacs=self.culstore.pop()
            #print "setting at end of fork"
            self.set()
            
            if self.btracks['done']==1:
                if not self.btracks['assigned']==1:
                    self.btracks['solution']=tsol
                    self.btracks['assigned']=1
                return self.btracks
            
            
                    #self.show(self.btracks['relevant'])
                    #pshow(self,self.btracks['relevant'],save=1,text=self.btracks['reason'])
            #print self.btracks['reason']
            
            
        
        #lastrows=copy.deepcopy(self.rows)
        #assert origrows==lastrows
        #assert self.now==orignow
        self.btracks['reason']='backtrack'
        #print "end of fork"
        return self.btracks
    
    def emit(self):
        st=time.clock()
        chains=getchains(self.aff)
#~         print ""
#~         print "in emit, got chains:"
#~         for ii,c in enumerate(chains):
#~             print ii,c
#~         print "self now is:",self.now
        walkers=[]
        thiscds=[]
        for c in chains:
            found=0
            #print c
            for ll in c:
                if getdist(self.now,ll)==1:
#~                     print "skippd chain: due to self now",self.now,c
                    continue
#~             print "chain wsa ok",c
            loc,dv=c.items()[0]
            w1=Walker2()
            w1.rtype=1
            w1.loc=loc
            w1.wallv=dv+2
            w1.firstloc=loc
            w1.tread={loc:w1.wallv}
            w2=Walker2()
            w2.rtype=-1
            w2.loc=loc
            w2.wallv=dv+2
            w2.firstloc=loc
            w2.tread={loc:w2.wallv}
            w1.culd=None
            w2.culd=None
            w1.bad=0
            w2.bad=0
            walkers.append((w1,w2))
        thisstep=0
        toremove=[]
        res='notsplit'
        #print ""
        #print "starting while loop"
        wcount=len(walkers)
        #print "initial",wcount
        actualsteps=0
        dsquares=self.getneighbors(self.now)
        while thisstep<gmaxsteps:
            actualsteps+=1
            if wcount==0:
                break
#~             debug=1
#~             if debug:
#~                 print "looping:"
#~                 print "toremove is:"
#~                 for b in toremove:
#~                     print b
#~                 print "thissteyp is:",thisstep
#~                 print "walkers is:"
#~                 for w1,w2 in walkers:
#~                     print w1
#~                     print w2
            thisstep+=1
            for w1,w2 in walkers:
                if w1.bad or w2.bad: continue
                if w1.loc in dsquares or w2.loc in dsquares:
                    w1.bad=1
                    w2.bad=1
                    wcount+=-1
                    #print "bumpbed into now"
                    continue
                
                w1.loc,w1.wallv=self.wallwalk2(w1.loc,w1.wallv,w1.rtype)
                w2.loc,w2.wallv=self.wallwalk2(w2.loc,w2.wallv,w2.rtype)

                #print "stepped"
                #print "locs:",w1.loc,w2.loc
                #print "treads:"
                #print w1.tread
                #print w2.tread
                if (w1.loc,(w1.wallv%4)) in w1.tread.items():                    
                    #print 'returned to first'
                    #print 'w1, returned to first'
                    #print "firstloc is:",w1.firstloc
                    #print "w1.loc is",w1.loc
                    #print "tread is:",w1.tread
                    res='split'
                    break
                if (w2.loc,(w2.wallv%4)) in w2.tread.items():
                    #print 'w2, returned to first'
                    #print "firstloc is:",w2.firstloc
                    #print "w2.loc is",w2.loc
                    #print "tread is:",w2.tread
                    res='split'
                    break
                w1.tread[w1.loc]=w1.wallv%4
                w2.tread[w2.loc]=w2.wallv%4
                if not(w1.culd==None and w2.culd==None): continue
                if w2.loc in w1.tread:
#~                     if debug:print "bumpbed at:",w2.loc
                    w2.culd=w2.loc
                    continue
                if w1.loc in w2.tread:
#~                     if debug:print "bumpbed at:",w1.loc
                    w1.culd=w1.loc
                    continue
            for w1,w2 in walkers:
                if w1.bad or w2.bad:
                    continue
                if w1.culd:
                    if not w1.culd in thiscds:
                        thiscds.append(w1.culd)
                elif w2.culd:
                    if not w2.culd in thiscds:
                        thiscds.append(w2.culd)
            if res=='split':
                
                thiscds=[]
                #print "split!"
                #self.show()
                break
        if gshowactualsteps:
            if actualsteps>100:
                print "steps:",actualsteps,"res",res,len(thiscds),"%4.6f"%(time.clock()-st)
        return res,thiscds

    
    def wallwalk2(self,loc,wallv,rtype):
        moved=0
        rotcount=0
        while moved==0:
            loc,wallv,rotcount=self.wallwalk(loc,wallv,rotcount,rtype)
            if rotcount==0:
                moved=1
            if rotcount>4:
                moved=1
        return loc,wallv

    def do(self,sol):
        #print "DO"
        self.multimove(self.todo)
        for v in self.justmoved_d:
            sol.move(v)
        if self.remaining==0:
            self.done=1
            #print "done"
            self.btracks['done']=1
            self.btracks['reason']='done'
            self.btracks['relevant']=[]
            return self.btracks
        if len(self.getneighbors())==0:
            self.btracks['deadend']+=1
            self.btracks['reason']='deadend'
            self.btracks['relevant']=[]
            
            return self.btracks

        #for c in self.culdesacs:
            #if not self.check2x2s(c):
                #self.culdesacs.remove(c)
                #print "was no longer a culdesac, removed"
            #else:
                #print "was still one, left it"
        #if len(self.culdesacs)>0:
            #print "culdesac..."


        if checkalleys:
            alleys,nearalleys=self.doalleys()
            #print "got alleys, nearalleys",alleys,nearalleys
            
            extraalley=0
            if len(nearalleys)==2:
                extraalley=1
            if len(alleys)-len(nearalleys)+extraalley>1:
                #print "died; alleys",len(alleys),'nearalleys',len(nearalleys)
                self.btracks['alley']+=1
                self.btracks['reason']='alley'
                self.btracks['relevant']=alleys
                self.death_counts[self.now]+=10
                return self.btracks
            #if len(alleys)+len(self.culdesacs)>1:
                #print "bad alleys;"
                #self.btracks['alleycul']+=1
                #self.btracks['reason']='alley+cul'
                #self.btracks['relevant']=alleys
                #self.death_counts[self.now]+=1
                #return self.btracks
        if checkemit:
            res,cds=self.emit()
            #print "got res,cds",res,cds
            if res=='split':
                self.btracks['split']+=1
                self.btracks['reason']='split'
                self.btracks['relevant']=(0,0)
                return self.btracks
            for cd in self.culdesacs:
                if self.check(cd):
                    self.culdesacs.remove(cd)
            for cd in cds:
                if cd not in self.culdesacs:
                    self.culdesacs.append(cd)

                    #print "clipped"
            #print "self culdesacs are:"
            #for c in self.culdesacs:
                #print c
            #print "total of",len(self.culdesacs),"cds"
            if len(self.culdesacs)>1:
                #print "too many culdesacs...",self.culdesacs
                #pshow(self,self.culdesacs,imgtext=repr(self.culdesacs)+"culds",save=1)
                if not getdist(self.culdesacs[0],self.culdesacs[1])<3:
                    self.btracks['cds']+=1
                    self.btracks['reason']='cds'
                    self.btracks['relevant']=self.culdesacs
                    return self.btracks
                #else:
                    #print "culdesacs are touching..."
                    #self.show(self.culdesacs)
                    #pass
                    
#~             if len(self.culdesacs) and len(self.culdesacs)+len(self.currentalleys)>1:
#~                 for a in self.currentalleys:
#~                     if getdist(self.culdesacs[0],a)>10:
#~                         if getdist(self.now,a) != 1:
#~                             pshow(self,self.culdesacs,imgtext=repr(self.culdesacs)+"alley,culd",save=1)
#~                             self.btracks['cdas']+=1
#~                             self.btracks['reason']='cds and alleys'
#~                             self.btracks['relevant']=[]
#~                             return self.btracks
#~                     
#~             

        if checkissplit:
            reason='split'
            if newcansee:
                res,reason=self.cansee3()
            else:
                res=self.cansee()
            if not res:
                #text="res is:"+str(res)
                #pshow(self,self.aff,imgtext=res,save=1)
                self.btracks['split']+=1
                self.btracks['reason']=reason
                self.btracks['relevant']=self.aff
                #self.death_counts[self.now]+=1
                return self.btracks     

 

        #print "about to fork; state now is:"
        #self.show()
        self.fork(sol)
        return self.btracks
        

def start(doboard=None,login=0,submit=0):
    totaltime=0
    limited=len(doboard)
    a=1
    while a:
        print 'a',a
        if limited:
            a=a-1
        try:
            thisb=0
            while len(doboard):
                thisb=doboard.pop()
            tries=100
            while tries:
                try:
                    level,text,res=getboard(thisb,limited,glogin)
                    tries=0
                except:
                    traceback.print_exc()
                    print "failed getting leve, will wait 5 seconds and try again, ",tries,"times"
                    time.sleep(5)
                    tries+=-1
                
            startt=time.clock()
            if not res:
                break
            b=Board()
            b.level=level
            b.start(text)
            print ""
            b.death_counts=b.getopen(dosort=True)
            b.still_todo=b.getopen(dosort=True).keys()
            print "LEVEL:",b.level
            global tot
            tot=len(b.still_todo)
            print "initial todo len is:",str(tot)
            #b.show()
            b.initialopen=copy.copy(b.still_todo)
            thisnum=0
            levelt=0
            ttime=0
            donecount=0
            while len(b.still_todo):
                donecount+=1
                sttime=time.clock()
                loc,val=choosesquare(b.death_counts,b.still_todo)
                x,y=loc
                #x,y=9,4
                b.still_todo.remove((x,y))
                #print "len still todo:",len(b.still_todo)
                thisnum+=1
                isdt=0
                if b.isdeeptunnel((x,y)):
                    b.btracks['deeptunnel']=1
                    isdt=1
                b.now=(x,y)
                undone=[]
                for e in b.initialopen:
                    if e not in b.still_todo:
                        undone.append(e)
                
                #print "setting in while loop"
                b.set()
                text=''
                text+=str(level)+" - "+str(thisnum)+"/"+str(tot)+" "+str(x)+","+str(y)+" val "+str(val)
                print text,
                if not isdt:
                    sol=Solution((x,y))
                    b.fork(sol=sol)
                ttime=(time.clock()-sttime)
                levelt+=ttime
                rest=''
                rest+="\tthis:%5.2f"%ttime
                rest+="\ttotal:%5.2f\t"%levelt
                
                if b.btracks['done']:
                    dodone(b,b.btracks['solution'],gsubmit,glogin,glive,startt)
                    
                    if gsavestarts:
                        toimg=(text+rest).replace("\t","   ")
                        fname="%3d"%level+"-%4d"%donecount+"-"+str(x)+","+str(y)+"-DONE"
                        fname=fname.replace(" ","0")
                        pshow(b,undone,save=1,imgtext="DONE"+toimg,fname=fname)
                    break

                ress=[]
                for k in ['deadend','alley','cds','split','ibox','deeptunnel']:
                    v=b.btracks[k]
                    if v==0 or v=='0':
                        continue
                    ress.append((v,k))
                ress.sort()
                ress.reverse()
                #print "ress is:",ress
                
                for v,k in ress:
                    v="%d"%v
                    rest+=k+"="+v+"\t"
                print rest
                b.currentalleys=[]
                b.aff.clear()
                b.unset()
                b.clearbtracks()
                b.culdesacs=[]
                
                if gsavestarts:
                    fname="%3d"%level+"-%4d"%donecount+"-"+str(x)+","+str(y)
                    fname=fname.replace(" ","0")
                    toimg=(text+rest).replace("\t","   ")
                    #print "text is",toimg
                    pshow(b,undone,save=1,imgtext=toimg,fname=fname)
        except:
            traceback.print_exc()

print "newcansee value:",newcansee
if checkalleys:
    print "checking alleys"
if checkissplit:
    print "checking split"
if check2box:
    print "checking 2boxes"
if checkemit:
    print "checking emit"
print "gmaxsteps is:",gmaxsteps
todo=[]
start(todo,glogin,gsubmit)