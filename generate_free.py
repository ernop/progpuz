from util import fliprots, ULzero, show, neighbors
import time, os, shutil

class Polyomino(object):
    def __init__(self, squares=None):
        self.squares=set()
        self.canonical=False #sqs are flipped / rotated / translated to the position which maximizes get_canval(sqs) (only based in ULZERO)
        self.canval=None
        self.zerod=False #ulzero has been called since last modification
        self.ct=0
        if squares:
            self.addsqs(squares)
            self.canonicalize()

    def change(self):
        self.zerod, self.canonical, self.canval=False, False, None

    def __eq__(self, other):
        if self.canonical and other.canonical and self.canval==other.canval:
            return True
        return False

    def __unicode__(self):
        self.show()

    def addsq(self,sq):
        self.squares.add(sq)
        self.ct+=1

    def addsqs(self,sqs):
        for sq in sqs:
            self.addsq(sq)
        self.change()

    def rot(self):
        self.squares=set([(sq[1],-1*sq[0]) for sq in self.squares])
        self.change()

    def flip(self):
        self.squares=set([(-1*sq[0],sq[1]) for sq in self.squares])
        self.change()

    def ULzero(self):
       #move upper left square to zero
       #(push everything down/right til its all visible (or up, left))
       if self.zerod:
            return
       minx=min([sq[0] for sq in self.squares])
       miny=min([sq[1] for sq in self.squares])
       self.squares=set([(sq[0]-minx,sq[1]-miny) for sq in self.squares])
       self.change()

    def canonicalize(self):
        '''rot/flip the squares into a canonical form (maximize the binary number value of the squares read as rows MAXCT digits long (works only to ct==MAXCT)'''
        if self.canonical:
            return
        bestval=None
        best=None
        self.ULzero()
        for sqs in fliprots(self.squares):
            val=get_binary_canval(sqs)
            if not bestval or val>bestval:
                best=sqs
                bestval=val
        self.squares=best
        self.canonical=True
        self.zerod=True
        self.canval=bestval

    def show(self,mxx=0,myy=0,after=True, before=True):
        if before:
            print '*'*30
        else:
            print ''
        maxx=max(mxx-1,max([sq[0] for sq in self.squares]))
        maxy=max(myy-1,max([sq[1] for sq in self.squares]))
        for yy in range(maxy+1):
            for xx in range(maxx+1):
                sq=(xx,yy)
                if sq in self.squares:
                    print 'X',
                else:
                    print '-',
            print '\n',
        if after:
            print '='*30

    def compare(self,other):
        self.ULzero()
        other.ULzero()
        return self.squares==other.squares

    def raw_children(self):
        '''raw children polyominos'''
        res=[]
        added_neighbors=set()

        for sq in self.squares:
            for nei in neighbors(sq):
                if nei in self.squares:
                    continue
                if nei in added_neighbors:
                    continue
                added_neighbors.add(nei)
                sqs=self.squares.copy()
                sqs.add(nei)
                pp=Polyomino(squares=sqs)
                res.append(pp)
        return res

    def unique_children(self):
        res=[]
        raws=self.raw_children()
        for raw in raws:
            raw.canonicalize()
            if raw in res:
                continue
            res.append(raw)
        return res

    def get_rows(self):
        self.canonicalize()
        maxx, maxy=max([x[0] for x in self.squares]),max([x[1] for x in self.squares])
        res=[]
        for yy in range(maxy+1):
            row=[]
            for xx in range(maxx+1):
                if (xx,yy) in self.squares:
                    row.append(0)
                    #flip it
                else:
                    row.append(1)
            res.append(row)
        from coilutil.split_utils import squarify
        squarify(res)
        return res

def test():

    t=Polyomino()
    t.addsqs([(0,0),(1,0),(2,0),(2,1),(2,-1)])
    t.canonicalize()
    t.show()

def load_pickle(ct):
    fn='pickle%d.pickle'%ct
    try:
        fp=open(fn,'rb')
    except IOError,e:
        return False
    res=pickle.load(fp)
    print 'loaded %d polyominos of %d cells'%(len(res), ct)
    return res

def gen_free_polyominos(ct):
    res=load_pickle(ct)
    if res:
        return res
    if ct==1:
        pp=Polyomino()
        pp.addsq((0,0))
        return [pp]
    subs=gen_free_polyominos(ct-1)
    res=[]
    for sub in subs:
        children=sub.unique_children()
        for child in children:
            if child in res:
                continue
            res.append(child)
    res.sort(key=lambda x:-1*x.canval)
    print 'ct=%d, total %d'%(ct, len(res))
    save_pickle(ct, res)
    return res

def save_pickle(ct, res):
    fn='pickle%d.pickle'%ct
    fp=open(fn,'wb')
    pickle.dump(res, fp)

def get_binary_canval(sqs):
    #I should do consecutive diagonal rows!  that'd be awesome.
    canval=0
    for ii in range(MAXCT):
        for jj in range(MAXCT):
            if (ii,jj) in sqs:
                canval+=2**(MAXCT*MAXCT-MAXCT*jj-ii-1)
                #canval+=2**(ii+MAXCT*jj)
    return canval

import cPickle as pickle

MAXCT=11
def do_ct(ct, onestep):
    assert ct<=MAXCT
    st=time.clock()
    res=gen_free_polyominos(ct)
    print 'gentime %0.4f'%(time.clock()-st)
    coilsolvable_count=0
    onestepsolvable_count=0
    coilst=time.clock()
    tlen=len(res)
    for ii,guy in enumerate(res):
        if ii%100==0:
            print ii,tlen
            guy.show()
        #~ guy.show(after=False, before=False)
        from coilutil.split import do_manual
        rows=guy.get_rows()
        guyname=2**(MAXCT**2)-1-guy.canval
        coilsolvable=do_manual(rows=rows, levelnum=guyname, onestep=False)
        onestepsolvable=do_manual(rows=rows, levelnum=guyname, onestep=True)
        if coilsolvable:
            #~ print 'coil solvable'
            coilsolvable_count+=1
        if onestepsolvable:
            #~ print 'coil solvable'
            onestepsolvable_count+=1
        #~ else:
            #~ print 'coil unsolvable'
    print 'coiltime %0.2f'%(time.clock()-coilst)
    print 'ct=%d, total %d, coilsolvable count %d'%(ct, len(res), coilsolvable_count)

def make_html(ct,onestep=False):
    lines=[]
    lines.append('<h2>Table for %d</h2>'%ct)
    dirs=os.listdir('output')
    dirs.sort(key=lambda x:int(x))
    lines.append('<table><thead><tr><th>name<th>blank<th>onestep solutions<th>onestep solution images<th>coilstep solutions<th>coilstep solution images</tr></thead><tbody>')
    onestep_count=0
    coil_count=0
    ii=0
    for dd in dirs:
        fp=os.path.join('output',dd)
        files=os.listdir(fp)
        blank=None
        solvhtml=''
        name=str(dd)
        coilhtmls=[]
        onestephtmls=[]
        newname=str(dd)
        onect, coilct=0,0
        for ff in sorted(files):
            newname=''
            if 'blanks' in ff:
                blankfn='blank%d.png'%(ii)
                sfp=os.path.join(fp, ff)
                dfp=os.path.join('output',blankfn)
                shutil.move(sfp,dfp)
            elif 'onestep' in ff:
                sfp=os.path.join(fp, ff)
                solfilename='blank%d-onestep-subsol%d.png'%(ii, onect)
                dfp=os.path.join('output',solfilename)
                shutil.move(sfp,dfp)
                br=''
                if len(onestephtmls)%8==0 and onect>2:
                    br='<br>'
                onect+=1
                onestephtmls.append('%s<img src="polycovers/%d/%s">'%(br, ct, solfilename ))
            elif 'coilstep' in ff:
                sfp=os.path.join(fp, ff)
                solfilename='blank%d-coil-subsol%d.png'%(ii, coilct)
                dfp=os.path.join('output',solfilename)
                shutil.move(sfp,dfp)

                br=''
                if len(coilhtmls)%8==0 and coilct>2:
                    br='<br>'
                coilct+=1
                coilhtmls.append('%s<img src="polycovers/%d/%s">'%(br, ct, solfilename))

        onestephtml=''.join(onestephtmls)
        coilhtml=''.join(coilhtmls)
        if onestephtml:
            onestep_count+=1
        if coilhtml:
            coil_count+=1
        row='<tr><td>%s<td><img src="polycovers/%d/%s"><td>%d<td>%s<td>%d<td>%s'%(name, ct, blankfn, len(onestephtmls), onestephtml, len(coilhtmls), coilhtml)
        #~ row='<tr><td>%s<td><img src="output/%s/%s"><td>%s'%(name, dd, blank, solvhtml)
        lines.append(row)
        ii+=1

    lines.insert(0, '<style>td {border-top:1px dotted lightgrey;}</style>')
    lines.insert(1, '<p>There are %d free polyominos with %d cells<p>'%(len(dirs), ct))
    lines.insert(2, '<p>%d of them are onestep-coverable'%(onestep_count))
    lines.insert(3, '<p>%d of them are coilstep-coverable'%(coil_count))
    fn='%02dtable.html'%(ct)
    lines.append('</table>')
    out=open(fn,'w')
    for ll in lines:
        out.write(ll+'\n')
    out.close()
    #~ import ipdb;ipdb.set_trace()
    if os.path.exists(str(ct)):
        shutil.rmtree(str(ct))
    os.rename('output',str(ct))
    exi='polycovers/%d'%ct
    print 'removing',exi
    if os.path.isdir(exi):
        shutil.rmtree(exi)
    shutil.move(str(ct),'polycovers')

import sys
ct=int(sys.argv[-1])
onestep=True
MAXCT=ct
#~ ct=4
do_ct(ct=ct,onestep=onestep)
make_html(ct=ct,onestep=onestep)
