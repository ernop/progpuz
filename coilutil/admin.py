import pprint,time,traceback,urllib2,os,random,sys,copy, urllib
try:
    import Image,ImageFont,ImageDraw
    imaging=True
except:
    imaging=False
import cPickle,shutil
import split_utils
import config
dirs='pickles levels illegals'.split()
for d in dirs:
    if not os.path.isdir(d):
        os.mkdir(d)
font=None
hint2image={}
color_dict=None
color_images={}
last_startsave=1000*1000
def rndcolor():
    return (random.choice(range(255)),random.choice(range(255)),random.choice(range(255)))

class Bag():
    pass


def general_load_pickle(fn):
    st=time.time()
    if not os.path.isfile(fn):
        return []
    try:
        fp=open(fn)
        print 'loading...',fn
        res=cPickle.load(fp)
        print 'loaded:',len(res),'in %0.2f'%(time.time()-st)
        fp.close()
    except IOError:
        import ipdb;ipdb.set_trace()
        traceback.print_exc()
        res={}
        print 'FAIL:',fn
    #~ print 'took %0.5f'%(time.time()-st)
    return res

def general_save_pickle(fn,data):
    st=time.time()
    tmp=fn+'-temp'
    real=tmp.replace('-temp','')
    try:
        fp=open(tmp,'w')
        cPickle.dump(data,fp)
        fp.close()
        shutil.copy(tmp,real)
        os.remove(tmp)
        #~ print 'saved',len(data),'to',real,
    except Exception, e:
        #~ import ipdb;ipdb.set_trace()
        #~ traceback.print_exc()
        #~ return 'FAIL to:',fn
        pass
    #~ print 'took %0.5f'%(time.time()-st)

def load_images(imgdir):
    loaded_images={}
    from BmpImagePlugin import Image
    loaded_images['in1']=Image.open(open(imgdir+'/in1.bmp','r'))
    loaded_images['inout']=Image.open(open(imgdir+'/passby.bmp','r'))
    loaded_images['in2']=loaded_images['in1'].rotate(-90)
    loaded_images['in3']=loaded_images['in1'].rotate(-180)
    loaded_images['in0']=loaded_images['in1'].rotate(-270)
    loaded_images['1out']=Image.open(open(imgdir+'/1out.bmp','r'))
    loaded_images['2out']=loaded_images['1out'].rotate(-90)
    loaded_images['3out']=loaded_images['1out'].rotate(-180)
    loaded_images['0out']=loaded_images['1out'].rotate(-270)
    loaded_images['skip']=Image.open(open(imgdir+'/skip.bmp','r'))
    for upos in ['','u_']:
        loaded_images[upos+'00']=Image.open(open(imgdir+'/'+upos+'00.bmp','r'))
        loaded_images[upos+'22']=loaded_images[upos+'00'].rotate(180)
        loaded_images[upos+'33']=loaded_images[upos+'00'].rotate(90)
        loaded_images[upos+'11']=loaded_images[upos+'33'].rotate(180)

        loaded_images[upos+'30']=Image.open(open(imgdir+'/'+upos+'30.bmp','r'))

        loaded_images[upos+'01']=loaded_images[upos+'30'].rotate(-90)
        loaded_images[upos+'12']=loaded_images[upos+'30'].rotate(-180)
        loaded_images[upos+'23']=loaded_images[upos+'30'].rotate(-270)

        loaded_images[upos+'03']=loaded_images[upos+'30'].transpose(Image.FLIP_LEFT_RIGHT).rotate(-90)
        loaded_images[upos+'10']=loaded_images[upos+'30'].transpose(Image.FLIP_TOP_BOTTOM)
        loaded_images[upos+'21']=loaded_images[upos+'10'].rotate(-90)
        loaded_images[upos+'32']=loaded_images[upos+'30'].transpose(Image.FLIP_LEFT_RIGHT)
        colors='red black green white turq blue whiteborder purple yellow'.split()

        for color in colors:
            loaded_images[color]=Image.open(open(imgdir+'/'+color+'.bmp','r'))
    return loaded_images

def res2code(res):
    """convert the hints for a pos into an image showing what sides can enter, what can leave."""
    codes=[]
    for n in [0,1,2,3]:
        codes.append('dv%d-typ%d'%(n,res[n]))
    code='_'.join(codes)
    return code

def load_done(levelnum):
    picklename='pickles/%s.pickle'%levelnum
    return general_load_pickle(picklename)

last_save_done=0
def modified_starts(levelnum,donestarts, board):
    return
    if config.save_donestarts:
        global last_save_done
        if not time.time()-last_save_done>30:
            return
        last_save_done=time.time()
        picklename='pickles/%s.pickle'%levelnum
        general_save_pickle(picklename,donestarts)
    if config.save_unsolved_counts:
        global last_startsave
        if last_startsave- len(board.starts)+1>config.save_unsolved_every:
            last_startsave=len(board.starts)
            fname='%s-unsolved_counts-startsleft%d'%(board.levelnum,len(board.starts))
            makeimg_numdict(board.orig_rows,board.orig_open,board.starts,{},board.levelnum,fname)

scale=config.scale
imgdir='d:/proj/progpuzgit/coilutil/images'+str(scale)
loaded_images=load_images(imgdir)

def pshow(board=None,special=[],special2=[],save=1,fname=None,\
    imgtext=None,special_dict={},worktype=None,\
    inouts={},byrooms={},overwrite=True,rows=None,hintdict=None,rescale=None, force=False, onestep=False):
    from BmpImagePlugin import Image
    if getattr(board,'loaded_all_solpaths',0) and config.no_save_when_check_all_sol and not force:
        return
    global loaded_images
    if not imaging:
        print 'no imaging'
        return
    if not (rows or board):
        print 'broken'
    if rows:
        board=Bag()
        board.rows=rows
        board.maxx=len(rows[0])-1
        board.maxy=len(rows)-1
        board.orig_open=set()
        board.levelnum='test'
        for yy in range(len(rows)):
            for xx in range(len(rows[0])):
                if not rows[yy][xx]:
                    board.orig_open.add((xx,yy))
        board.now=None
    if special_dict:
        for k,v in special_dict.items():
            if k not in board.orig_open:
                print 'problem; received color for pos',k,'which is not in orig_open'
                import ipdb;ipdb.set_trace();print 'ipdb!'
    if not worktype:
        if board:
            worktype=board.levelnum
        else:
            worktype=''
    outdir='output/'+worktype
    if len(fname)>150:
        overwrite=False
        fname=fname[0:200]+'..'+fname[-5:]
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    if not overwrite and os.path.exists(outdir+'/'+fname+'.png'):
        #~ print 'no overwrite',fname
        return
    if type(special)==tuple:
        special=[special]
    scale=config.scale
    size=(int(scale*(board.maxx+1)),int(scale*(board.maxy+1)))
    if imgtext:
        size=(size[0],size[1]+scale*(2+imgtext.count("\n")))
    im=Image.new('RGB',size,color='white')
    imgdir='d:/proj/progpuzgit/coilutil/images'+str(scale)
    if hintdict:
        global hint2image
        for k,v in hintdict.items():
            if v not in hint2image:
                target=os.path.join(imgdir,v+'.bmp')
                hint2image[v]=Image.open(target)
                #~ print 'loaded:',v
    global color_dict
    if not color_dict:
        color_dict={}
        #~ colors='red black green white turq blue whiteborder purple yellow'.split()
        colors='black whiteborder'.split()

        for color in colors:
            color_dict[color]=Image.open(open(imgdir+'/'+color+'.bmp','r'))
    thisdone=[]
    global color_images
    for color in special_dict.values():
        if color in color_images:
            continue
        #~ print 'loading',color
        color_images[color]=Image.new(mode='RGB',size=(scale,scale),color=color)
    st=time.time()
    for y in range(len(board.rows)):
        for x in range(len(board.rows[0])):
            pixloc=(scale*x,scale*y)
            if (x,y) in inouts:
                imname=''.join([str(n) for n in inouts[(x,y)]])
                im.paste(loaded_images[imname.lower()],pixloc)
                continue
            elif (x,y) in special_dict:
                im.paste(color_images[special_dict[(x,y)]],pixloc)
                continue
            elif hintdict and (x,y) in hintdict:
                im.paste(hint2image[hintdict[(x,y)]],pixloc)
                continue
            elif (x,y) in board.orig_open:
                im.paste(color_dict['whiteborder'],pixloc)
                continue
            else:
                im.paste(color_dict['black'],pixloc)
    if imgtext:
        tsp=imgtext.split("\n")
        n=0
        global font
        if not font:
            #~ print 'load font'
            font=ImageFont.truetype('arial.ttf',15)
        dd=ImageDraw.ImageDraw(im)
        for line in tsp:
            #~ import ipdb;ipdb.set_trace()
            loc=(5,(scale)*(board.maxy+n)+5)
            n+=1
            dd.text(loc,text=line,font=font,fill='blue')
    if save:
        if rescale:
            im=im.resize((im.size[0]*rescale,im.size[1]*rescale))
        fname=fname.strip().replace('\n','')
        if not fname.endswith(".png"):
            fname=str(fname)+".png"
        if not os.path.exists(outdir):
            print 'make outdir??'
            os.mkdir(outdir)
        outpath=os.path.join(outdir,fname)
        st=time.time()
        im.save(outpath)
        #~ print "\nSAVED to %s %0.4f"%(outpath,(time.time()-st)),
    else:
        im.show()

def show(rows):
    for r in rows:
        l=''.join(str(n) for n in r)
        print l

def loadrows(levelnum):
    #~ try:
        #~ levelnum="%04d"%int(levelnum)
    #~ except:
        #~ pass

    import ipdb;ipdb.set_trace()
    lines=open(os.path.join('levels/%s'%levelnum+'.txt'),'r').readlines()
    rows=[]
    skipnext=False
    for l in lines:
        if l.startswith("Flash"):
            skipnext=True
            continue
        if skipnext:
            skipnext=False
            continue
        l=l.strip()
        if '=' in l:
            l=l.rsplit('=',1)[-1]
        l=l.replace("X","1").replace(".","0")
        l=[int(c) for c in l]
        rows.append(l)
#~     rows=boxify(rows)
    #FUCK.  already done!^^^^^^^^^
    return rows

def getrows(levelnum):
    if levelnum is not None:
        target=os.path.join('levels/%s'%levelnum+'.txt')
        line=open(target,'r').readline()
        if 'FlashVars' in line:
            rows=makerows(line)
        else:
            lines=open(target,'r').readlines()
            rows=mkrows_square(lines)
    else:
        rows,levelnum=dlrows()
    return rows,levelnum

def dlrows():
    url="http://www.hacker.org/coil/index.php?name=ernie&password="+getpw()
    import urllib,os
    for n in range(100):
        try:
            #~ print 'urllib read',
            res=urllib.urlopen(url).readlines()
            #~ print 'red',
            break
        except:
            print 'read fail'
            traceback.print_exc()
            print 'sleeping 10'
            time.sleep(10)
    for l in res:
        l=l.strip()
        if "Level: " in l:
            lsp=l.split("Level: ")
            #~ levelnum='%04d'%int(lsp[1].split("<")[0])
            rawlevelnum=int(lsp[1].split('<')[0])
            #~ import ipdb;ipdb.set_trace()
            #~ print "i am in raw level",rawlevelnum
        if l.startswith("FlashVars"):
            flashline=l
            break
    #~ import ipdb;ipdb.set_trace()
    rows=makerows(flashline)
    text='\n'.join([''.join([str(c) for c in l]) for l in rows])
    outfile="levels/%04d"%rawlevelnum+".txt"
    n=96
    levelnum='%04d'%rawlevelnum
    #~ import ipdb;ipdb.set_trace()
    should_save=True
    while 1:
        if not os.path.exists(outfile):
            char=chr(n)
            if n==96:
                char=''
            levelnum='%04d%s'%(rawlevelnum, char)
            break
        if levels_are_equal(outfile,flashline):
            should_save=False
            break
        else:
            n+=1
            levelnum='%04d%s'%(rawlevelnum, chr(n))
            outfile="levels/%s.txt"%(levelnum)

    if should_save:
        print 'saving to: %s'%outfile
        print '%d x %d'%( len(rows[0]),len(rows))
        if not os.path.exists(outfile):
            out=open(outfile,'w')
            out.write(flashline)
            out.write("\n\n")
            out.write(text)
            out.close()
    return rows,levelnum

def levels_are_equal(outfile, l):
    """check if the first row of outfile matches this l.  if not, return false and we will save this
    level to another file instead."""
    if not os.path.isfile(outfile):
        return False
    l2=open(outfile,'r').readlines()[0].strip()
    if l2==l:
        return True
    return False

def mkrows_square(lines):
    rows=[]
    for l in lines:
        row=l.strip()
        rows.append([int(c) for c in row])
    return boxify(rows)

def makerows(line):
    line=line.replace("FlashVars=","").strip()
    sp=line.split("=")
    x=int(sp[1].replace("&y",""))
    y=int(sp[2].replace("&board",""))
    b=sp[3]
    b=b.replace(".","0").replace("X","1")
    rows=[]
    while b:
        this=b[:x]
        b=b[x:]
        if len(this)==1:continue
        rows.append([int(c) for c in this])
    return boxify(rows)

def boxify(rows):
    x,y=len(rows[0]),len(rows)
    for n in range(y):
        rows[n].insert(0,1)
        rows[n].append(1)
    rows.insert(0,[1 for n in range(x+2)])
    rows.append([1 for n in range(x+2)])
    return rows

def getpw():
    l=open('pw.txt','r').readline().strip()
    return l

def make_rooms_image(rows,method,levelnum, board):
    rooms=getattr(board, method)
    special_dict={}
    for rm in rooms:
        for lp in rm.sqs:
            pos=rm.local2global(lp)
            special_dict[pos]=rm.color
    fname="%s-%s"%(levelnum,method)
    pshow(overwrite=True,rows=rows,special_dict=special_dict,worktype='%s'%levelnum,fname=fname)

def make_tunnel_image(rows,levelnum):
    donesqs=set()
    special_dict={}
    for xx in range(config.maxx):
        for yy in range(config.maxy):
            pos=(xx,yy)
            if pos in donesqs:
                continue
            if not split_utils.isopen(rows,pos):
                continue
            if not split_utils.isreqtunnel(rows,pos):
                continue
            tunnelsqs,ends=split_utils.get_tunnelsqs_ends(rows,pos)
            donesqs.update(tunnelsqs)
            for tsq in tunnelsqs:
                if split_utils.isdeeptunnel(rows,tsq):
                    special_dict[tsq]=(250,50,30)
                else:
                    special_dict[tsq]=(50,50,230)

def getd(dv):
    if dv==0:
        return 'R'
    if dv==1:
        return 'D'
    if dv==2:
        return 'L'
    return 'U'

def getdv(d):
    if d=='R':
        return 0
    elif d=='D':
        return 1
    elif d=='L':
        return 2
    return 3

def boardinit(board,levelnum):
    """boring setup for a board."""
    board.multimovecount=0
    board.levelnum=levelnum
    worktype=board.levelnum
    fname='%s-blanks'%board.levelnum
    imgtext=''
    #~ import ipdb;ipdb.set_trace()
    pshow(board,worktype=worktype,fname=fname,imgtext=imgtext,overwrite=False, force=True)
    #~ if 0:
        #~ for method in 'optrooms reqrooms'.split():
                    #~ #flowtoreqgates
            #~ make_rooms_image(board.rows,method,board.levelnum, board)
        #~ make_tunnel_image(board.rows,board.levelnum)
    #~ rooms=sorted(board.pararooms, key=lambda x:(x.product_of_pararoom_merging,len(x.orig_allsqs)))
    #~ special_dict={}
    #~ for rm in rooms:
        #~ for lp in rm.sqs:
            #~ pos=rm.local2global(lp)
            #~ special_dict[pos]=rm.color
        #~ for gsq in rm.gatesqs:
            #~ pos=rm.local2global(gsq)
            #~ special_dict[pos]=(75,75,75)
    #~ fname='%s-pararooms.png'%levelnum
    #~ pshow(overwrite=0,rows=board.rows,special_dict=special_dict,worktype='pararooms',fname=fname)
    #~ pshow(  overwrite=0,rows=board.rows,special_dict=special_dict,worktype='%s'%board.levelnum,fname=fname)

    #~ rooms=[p for p in board.pararooms if not getattr(p,'product_of_pararoom_merging',None)]
    #~ rooms=sorted(rooms, key=lambda x:(not x.product_of_pararoom_merging,len(x.orig_allsqs)))
    #~ special_dict={}
    #~ for rm in rooms:
        #~ for lp in rm.sqs:
            #~ pos=rm.local2global(lp)
            #~ special_dict[pos]=rm.color
        #~ for gsq in rm.gatesqs:
            #~ pos=rm.local2global(gsq)
            #~ special_dict[pos]=(75,75,75)
    #~ fname='%s-pararooms-orig.png'%levelnum
    #~ pshow(overwrite=0,rows=board.rows,special_dict=special_dict,worktype='%s'%board.levelnum,fname=fname)
    #~ pshow(overwrite=0,rows=board.rows,special_dict=special_dict,worktype='pararooms',fname=fname)

    #~ fname='%s-parasqs.png'%levelnum
    #~ special_dict={}
    #~ for sq in board.parasqs:
        #~ special_dict[sq]=(100,200,100)
    #~ pshow(overwrite=0,rows=board.rows,special_dict=special_dict,worktype='%s'%board.levelnum,fname=fname)
    #~ fname='%s-deeptunnel'%levelnum
    #~ special_dict={}
    #~ for sq in board.deeptunnels:
        #~ special_dict[sq]=(100,200,100)
    #~ pshow(overwrite=0,rows=board.rows,special_dict=special_dict,worktype='%s'%board.levelnum,fname=fname)

def copysols(sols):
    return sols[:]
    if sols=='timeout':
        return sols
    if not sols:
        return sols
    sols2=[]
    for sol in sols:
        sols2.append(copysol(sol))
    return sols2

def copysol(sol):
    #~ import ipdb;ipdb.set_trace()
    return sol
    #sols are tuples now, so.
    sol2=[]
    for sa in sol:
        sa2=(sa[0],sa[1],sa[2][:],sa[3][:],sa[4])
        sol2.append(sa2)
    return sol2

def save_all_sols(rm,method='no-method'):
    """call on a room to save its sols out.  needs levelnum"""
    sc=(0,255,0)
    ec=(255,0,0)
    BLUE=(0,0,255)
    if not rm.levelnum:
        print 'error; room needs levelnum.'
        sys.exit()
    if not rm.all_sols:
        rm.all_sols=rm.get_all_sols()
    if rm.all_sols=='timeout':
        return
    for ii,s in enumerate(rm.all_sols):
        fname='roomsol%s-%04d%s'%(rm.hashid,ii,method)
        worktype=rm.levelnum
        if os.path.isfile(os.path.join('output',worktype,fname)):
            continue
        special_dict={}
        for sg in s:
            start,indv,path,covered,end=sg
            special_dict[start]=sc
            rc=(random.randrange(50,220),random.randrange(50,220),random.randrange(50,220))
            for p in covered:
                special_dict[p]=rc
            special_dict[end]=ec
            if start==end:
                special_dict[end]=BLUE

        imgtext=None
        pshow(rows=rm.rows,fname=fname,imgtext=imgtext,worktype=worktype,special_dict=special_dict)



def count_actual_open(board):
    ct=0
    for xx in range(board.maxx+1):
        for yy in range(board.maxy+1):
            pos=(xx,yy)
            if board.isopen(pos):
                ct+=1
    return ct

def donestart(board,res=None,message=None,onestep=False, thissol=None):
    board.sttime=time.time()-board.thisst
    if not res:
        board.donestarts.add(board.start)
    #only add if board is not done!
    if board.start not in board.sol_starts.keys():
        board.donestarts.add(board.start)
    levelnum=board.levelnum
    modified_starts(board.levelnum,board.donestarts, board)
    fraction_solved=(1.0*board.maxopen-board.thisst_best_curopen)/board.maxopen
    value=int(1000.0*fraction_solved)

    if not thissol:
        if not board.thisst_best_sol:
            return
        thissol=board.thisst_best_sol[:]
    dv=thissol[0]
    if value>1:
        inouts=make_inouts(board,sol=thissol, onestep=onestep)
        decs=0
    #~ if board.levelnum=='16238247935'  and not onestep and value:
        #~ import ipdb;ipdb.set_trace()
    if config.abs_do_best_seen or (config.save_valuable_sols and value>config.save_valuable_sols_minvalue) or \
    (board.thisst_best_curopen>board.best_curopen and value>config.save_valuable_sols_minvalue) or thissol:
        worktype=levelnum
        if onestep:
            steptext='onestep'
        else:
            steptext='coilstep'
        mult=0
        for ii,ss in enumerate(thissol):
            mult+=(4**ii)*ss
        fname=worktype+'-%03d-%03d-%s-%s-%s'%(board.startpos[0],board.startpos[1],getd(dv),mult, steptext)
        #~ imgtext=fname+"      %0.2f    "%(board.sttime)
        imgtext=''
        if board.thisst_best_curopen==0 or board.curopen==0:
            pshow(board,fname=fname,imgtext=imgtext,inouts=inouts,worktype=worktype, force=True, onestep=onestep)
    if board.best_curopen and board.thisst_best_curopen<int(1.01*board.best_curopen) and board.curopen<orig_open_count:
        #if we're at least 80 as good as the last best solution.
        board.best_curopen=board.thisst_best_curopen
        board.best_sol=board.thisst_best_sol
        save_backtrack(board,text="best sol for this start.",force=True,sol=board.thisst_best_sol)
    if config.save_unsolved_counts:
        global last_startsave
        if last_startsave- len(board.starts)+1>config.save_unsolved_every:
            last_startsave=len(board.starts)
            fname='%s-unsolved_counts-startsleft%d'%(board.levelnum,len(board.starts))
            makeimg_numdict(board.orig_rows,board.orig_open,board.starts,{},board.levelnum,fname)





def makeimg_numdict(orig_rows,orig_open,startsleft,numdict,worktype,fname):
    st=time.time()
    special_dict={}
    colors=[(0,50,20),(0,100,20),(0,150,20),(0,200,20),(0,255,20)]
    startcounts={}
    #~ print startsleft
    for s in startsleft:
        startcounts[s[0]]=startcounts.get(s[0],0)+1
    #~ import ipdb;ipdb.set_trace()
    for pos,ct in startcounts.items():
        #~ import ipdb;ipdb.set_trace()
        orig_ct=0
        for v in ((0,1),(0,-1),(1,0),(-1,0)):
            if orig_rows[pos[1]+v[1]][pos[0]+v[0]]:
                continue
            orig_ct+=1
        removed_ct=orig_ct-ct
        #~ print ct,orig_ct
        if ct==orig_ct:
            special_dict[pos]=(200,255,0)
        elif ct==0:
            #not show absolut starts, but what % is left.
            special_dict[pos]=(255,100,100)
        elif removed_ct==1:
            special_dict[pos]=(205,0,0)
        elif removed_ct==2:
            special_dict[pos]=(100,100,0)
        elif removed_ct==3:
            special_dict[pos]=(80,80,80)

    st2=time.time()
    pshow(overwrite=True,special_dict=special_dict,rows=orig_rows,fname=fname,worktype=worktype)
    #~ print 'save took: %0.5f %0.5f'%((time.time()-st),time.time()-st2)

def doneboard(board):
    if not board.config.debug and not board.config.do_target and not board.config.forkmonpos:
        try:
            assert board.solvetime is not None
        except:
            #~ print 'didnt solve board; end.'
            return False
            #~ if config.profile:
                #~ return
            #~ else:
                #~ print 'ERORR'
                #~ sys.exit()
        worktype='allsols'#board.levelnum
        board.rows=board.orig_rows[:]
        special_dict={}
        #ALLSOLS!
        for s,dv in board.sol_starts.keys():
            special_dict[s]=(200,200,0)
        methods=['split']
        if config.setup_initial_illegal:
            methods.append('setup_initial_illegal')
        method='-'.join(methods)
        if not config.one_sol:
            fname='allsols-%s-%s'%(board.levelnum,method)
            imgtext=worktype+' - took :%0.2f   %s'%(board.solvetime,"\nmethods:"+method)
            pshow(board,fname=fname,imgtext=imgtext,special_dict=special_dict,worktype=worktype)
        #~ savesol(board)
        #~ savesolpath(board)
    try:
        assert board.solvetime is not None
    except:
        print 'didnt solve board; end.'
        if config.profile:
            return
        else:
            print 'ERORR'
            sys.exit()
    board.alldone=1
    #the final write of all the solutions (if you are in one_sol==0, the solutions haven't been being written as they go)
    if 0:
        dosolved(board)

def savesol(board):
    print 'savesol.'
    if config.one_sol:
        solfile='sols/%s'%board.levelnum+'.txt'
    else:
        solfile='allsols/%s'%board.levelnum+'.txt'
    if not os.path.isdir('sols'):
        os.mkdir('sols')
    if not os.path.isdir('allsols'):
        os.mkdir('allsols')

    if os.path.exists(solfile):
        if not config.one_sol:
            #don't compare when you are not in one sol mode.
            comparesols(solfile,board.sol_starts.keys())
    else:
        out=open(solfile,'w')
        #~ print 'sols:',board.sol_starts.keys(),'saved to:',solfile
        out.write(repr(sorted(board.sol_starts.keys())))
        out.close()

def savesolpath(board):
    return
    """save entire sol path!  so we know when going wrong! holy fuck!"""
    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    if board.loaded_all_solpaths:
        print 'not saving all solpaths, cause i loaded them.'
    else:
        if not os.path.isdir('solpaths'):os.mkdir('solpaths')
        solpathfile='solpaths/%s'%board.levelnum+'.pickle'
        general_save_pickle(solpathfile, data=board.sol_starts)
    #~ for

def comparesols(solfile,sols):
    old=open(solfile,'r').readline().strip()
    if old==repr(sorted(sols)):
        print '%d sols OK!'%len(sols)
    else:
        if not config.one_sol:
            if not config.live:
                oldsols=set(eval(old))
                sols=set(sols)
                missing_sols=oldsols.difference(sols)
                new_sols=sols.difference(oldsols)


                print 'SOL problem!'
                print '%d old sols===>:'%len(oldsols),repr(sorted(oldsols))
                print '%d new sols===>:'%len(sols),repr(sorted(sols))
                if missing_sols:
                    print '\n%d missing sols:'%len(missing_sols),[m for m in missing_sols]
                if new_sols:
                    print '\n%d new sols:'%len(new_sols),[n for n in new_sols]
                sys.exit()



def make_inouts(board,sol,lastsq=None, onestep=False):
    """for a board with a current sol
    """
    sol=sol[:]
    #~ import ipdb;ipdb.set_trace()
    startpos,startdv=board.startpos,board.startdv
    inouts={}
    last='IN'
    now=startpos
    filled=set()
    filled.add(now)
    inouts[now]=['IN']
    while len(sol):
        thisdv=sol.pop(0)
        next=split_utils.add(now,thisdv)
        while split_utils.isopen(board.orig_rows,next) and next not in filled:
            inouts[now].append(thisdv)
            if lastsq and now==lastsq:
                break
            now=next
            filled.add(now)
            inouts[now]=[thisdv]
            next=split_utils.add(now,thisdv)
            if onestep:
                break
    if len(inouts[now])<2:
        inouts[now].append('OUT')
    return inouts


def make_room_inouts(rm,sol):
    """make raw [dv,dv] combinations for each square based on this specific sol.  'IN' 'OUT' are acceptable also.
    """

    inouts={}

    filled=set()

    rows=rm.rows
    #~ sol=sol
    #~ import ipdb;ipdb.set_trace()
    for ii,sg in enumerate(sol):
        now,indv,path,_,_=sg
        path=path[:]
        filled.add(now)
        inouts[now]=['IN']
        for ii,thisdv in enumerate(path):
            next=split_utils.add(now,thisdv)
            while split_utils.isopen(rows,next) and next not in filled:
                inouts[now].append(thisdv)
                now=next
                filled.add(now)
                inouts[now]=[thisdv]
                next=split_utils.add(now,thisdv)
        if len(inouts[now])<2:
            inouts[now].append('OUT')
    return inouts


def sol2txt(sol):
    return ''.join([getd(s) for s in sol])

def dosolved(board):
    global last_startsave
    last_startsave=1000*1000

    if board.startpos:
        board.sol_starts[(board.startpos, board.startdv)]=board.thisst_best_sol
    if not config.one_sol:
        if not board.alldone:
            return
            #don't do it now... just accumulate them in sol_starts and this will be called again in doneboard.
    print '**'*50,'board took:%0.4f'%board.solvetime
    if board.alldone and config.one_sol:
        return
    if 0:
        submit(board)
    res=Bag()
    res.start=str(board.startpos)
    res.level=str(board.levelnum)
    res.time='%0.3f'%(board.solvetime)
    toprint=res.level+"\t"+res.start+"\t"+res.time
    print toprint
    if config.savestats:
        print 'saving stats'
        #~ print 'open'
        out=open('stats.txt','a')
        out.write('\t'.join([board.levelnum,'%.3f'%board.solvetime,]))
        out.write("\t")
        out.write('\t'.join(["%s=%s"%(f,getattr(config,f)) for f in config.toshow_fields]))
        out.write('\n')
        out.close()
    board.showstats(force=1)
    return res

def submit(board):
    start_pos=board.startpos
    path=''
    for s in board.sol:
        path+=getd(s)
    values={'x':str(start_pos[0]-1),
        'y':str(start_pos[1]-1),
        'path':path,
        'name':'ernie',
        'password':getpw(),
            }
    url = 'http://www.hacker.org/coil/index.php'
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    dlen=len(data)
    to=0
    while to<dlen:
        print data[to:to+100]
        to+=100
    init_wait=1
    if not board.config.submit:
        print 'not submitting; returning'
        return
    if board.config.submit:
        for n in range(1,100):
            try:
                print 'open',
                response = urllib2.urlopen(req)
                print 'SUBBED!'
                break
            except:
                traceback.print_exc()
                init_wait+=10
                print 'waiting',init_wait
                time.sleep(init_wait)
        print 'reeturning....'

def mktimedict(times):
    special_dict={}
    tottime=sum(times.values())
    try:
        maxtime=max(times.values())
        for pos,taken in times.items():

            special_dict[pos]=(int(255.0*(taken+0.01)/(maxtime+0.01)),0,0)
    except ValueError:
        pass
    return special_dict


def mkpartial(found_left,maxopen):
    numparts=10
    color_dict={}
    for pos,val in found_left.items():
        color_dict[pos]=(255*((maxopen-val)+100)/(maxopen+100.0),0,0)
    return color_dict
    reversed={}
    for pos,progress in found_left.items():
        if progress in reversed:
            reversed[progress].append(pos)
        else:
            reversed[progress]=[pos]
    print 'reversed is:::'
    pprint.pprint(reversed)
    num=len(reversed)
    print 'reversed has distict:',num
    perpart=num/numparts
    print 'perpart is:',perpart
    sorted_keys=sorted(reversed.keys())
    print sorted_keys
    while sorted_keys:
        this_chunk=sorted_keys[:perpart]
        sorted_keys=sorted_keys[perpart:]
        thiscolor=(255/numparts*n,0,0)
        print 'part n:',n,'has color:',thiscolor
        for index in sorted_keys[n:n+perpart]:
            print index,reversed[index]
            for pos in reversed[index]:
                color_dict[pos]=thiscolor
    return color_dict

def showstats():
    import pstats
    stats = pstats.Stats("test_function.cprof")
    stats.strip_dirs().sort_stats('time').print_stats()

def multuple(a,b):
    return tuple([int(n*b) for n in a])





def mk_o1_board():
    n2color={0:(40,50,120),
        1:(90,50,30),
        2:(50,100,15),
        3:(70,130,30),
        4:(140,200,56),
        5:(200,50,170),
            }

    for n in range(100):
        try:
            rows=loadrows(n)
            config.maxx,config.maxy=len(rows[0])-1,len(rows)-1
        except:
            continue
        allneighbors=get_allneighbors(config)
        print 'making board'

        board=split.Board(config,rows=rows)
        print 'made'
        special_dict={}
        worktype='seen-neighbor-types-diag-all-all'
        fname='%s-%04d'%(worktype,n)

        allneighbornums={}
        for pos in fullboard(board.config):
#~             if board.isopen(pos):
                allneighbornums[pos]=len(board.getopen_loc(pos))

        for pos in innerboard(board.config):
#~             if board.isopen(pos):
                isee=set()
                myneighbors=allneighbors[pos]
                for nei in myneighbors:
#~                     if board.isopen(nei):
                        isee.add(allneighbornums[nei])
                if len(isee)==5:
                    print 'at pos:',pos
                    print 'isee is!',isee
                    print 'myneighbors',myneighbors
                    print [(n,allneighbornums[n]) for n in myneighbors]
                    print '\n\n'

                special_dict[pos]=n2color[len(isee)]
        print 'rand'
#~         imgtext="\n".join([str(k)+":"+','.join(map(str,v)) for k,v in n2color.items()])
        imgtext=worktype
        pshow(board,special_dict=special_dict,fname=fname,worktype=worktype,imgtext=imgtext)

def save_backtrack(board,extra_alley=None,extra_illegalroom=None,text=None,force=False,violated_hint=None,sol=None,fn=None):
    config.btcount+=1
    if not config.save_backtracks:
        return
    if not force and config.btcount%config.save_backtracks_every!=0:
        return
    special_dict={}
    if not fn:
        fn=''
    if not text:
        text=''
    vp=None
    #~ print '\n'+text

    #~ import ipdb;ipdb.set_trace();print 'ipdb!'

    if 'hint' in text:
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        vv=text.split('-(')[1].split(')')[0]
        violated_hint=tuple([int(v) for v in vv.split(',')])
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    text+='\n'+str(board.endpos)
    if violated_hint:
        vp,tofrom=violated_hint
        special_dict[violated_hint]=(20,20,240)
        #~ text+=str(violated_hint)+'violated hint.'
    if board.alley:
        special_dict[board.alley]='yellow'
        text+='\none alley %s'%(str(board.alley))
    if board.air:
        for sq in board.air.orig_allsqs:
            special_dict[sq]=(200,100,100)
        #~ import ipdb;ipdb.set_trace()
        text+='\na.i.r. %d %d'%(board.air.xoffset+1,board.air.yoffset+1)
    if extra_alley:
        special_dict[extra_alley]='yellow'
        text+='\nextr alley %s'%(str(extra_alley))
    if extra_illegalroom:
        for sq in extra_illegalroom.orig_allsqs:
            special_dict[sq]=(200,100,150)
        text+='\nextra illegalroom %d %d'%(extra_illegalroom.xoffset,extra_illegalroom.yoffset)
    worktype=board.levelnum
    fname=worktype
    if fn:
        fname+=fn
    if sol:
        fname+='-best_sol'
    else:
        fname+='-backtrack'
    if not sol:
        sol=board.sol
        #default to current sol.
    inouts=make_inouts(board,lastsq=vp,sol=sol)
    if violated_hint:
        inouts.pop(violated_hint)
    boardhash=''
    fname+='%04d-dt-%06d-%03d-%03d-%s %s'%(config.btcount, board.curopen,board.startpos[0],board.startpos[1],getd(board.startdv),boardhash)
    import ipdb;ipdb.set_trace()
    #~ imgtext=worktype+'     '+text
    imgtext=''
    pshow(board,fname=fname,overwrite=True,imgtext=imgtext,inouts=inouts,special_dict=special_dict,worktype=worktype)

def kill_caches():
    global g_allsols_cache
    global g_hassols_cache
    g_allsols_cache={}
    g_hassols_cache={}

def load_allsols_pickle(levelnum):
    if not config.load_allsols_pickle:
        return {}
    picklename='pickles/%sallsols.pickle'%levelnum
    res=general_load_pickle(picklename)
    return res

def save_allsols_pickle(levelnum,data):
    if not config.load_allsols_pickle:
        return
    picklename='pickles/%sallsols.pickle'%levelnum
    general_save_pickle(picklename,data=data)

def load_hassols_pickle(levelnum):
    if not config.load_hassols_pickle:
        return {}
    picklename='pickles/%shassols.pickle'%levelnum
    res=general_load_pickle(picklename)
    return res

def save_hassols_pickle(levelnum,data):
    if not config.load_hassols_pickle:
        return
    picklename='pickles/%shassols.pickle'%levelnum
    general_save_pickle(picklename,data=data)

#~ def done_simpleroom(levelnum):
    #~ if not config.load_allsols_pickle:
        #~ return
    #~ print 'doing save allsols.:'
    #~ save_allsols_pickle(levelnum,g_allsols_cache)
    #~ print 'doing save hassols'
    #~ save_hassols_pickle(levelnum,g_hassols_cache)

def save_rm_solcounts(board):
        colors={}
        b=(0,30,0)
        BLUE=(0,0,140)
        RED=(255,0,0)
        GREEN=(0,140,0)
        PINK=(255,105,180)
        PURPLE=(148,0,211)
        ORANGE=(255,80,0)
        GREY=(120,135,150)
        KHA=(240,234,150)
        YEL=(139,105,20)
        OR=(238,64,0)
        SAM=(198,113,113)
        LAS=(238,238,238)
        solnum2color={1:BLUE,
            2:GREEN,
            3:PINK,
            4:PURPLE,
            5:ORANGE,
            6:GREY,
            7:KHA,
            8:YEL,
            9:OR,
            10:SAM,
            11:LAS}
        for rm in board.optrooms:
            if not rm.all_sols:
                col=YEL
            elif rm.all_sols=='timeout':
                col=(255,255,255)
            else:
                num=len(rm.all_sols)
                if num in solnum2color:
                    col=solnum2color[num]
                else:
                    col=RED
            for sq in rm.orig_sqs:
                colors[sq]=col
        fname='%sroom_solcounts'%(board.levelnum)
        worktype=board.levelnum
        imgtext='room_solcounts!\nblue:1\ngreen:2\npink:3\npurple:4\norange:5\ngrey:6\nkhaki:7\nyellow:8\nredorange:9\nsalmon:10\nlast:11\nRED:12+'
        pshow(rows=board.rows,fname=fname,worktype=worktype,imgtext=imgtext,special_dict=colors)

def save_sq_hintcounts(board):
        colors={}
        b=(0,30,0)
        BLUE=(0,0,140)
        RED=(255,0,0)
        GREEN=(0,140,0)
        PINK=(255,105,180)
        PURPLE=(148,0,211)
        ORANGE=(255,80,0)
        GREY=(120,135,150)
        KHA=(240,234,150)
        YEL=(139,105,20)
        OR=(238,64,0)
        SAM=(198  ,	113 , 	113  	)
        LAS=(238,238,238)
        solnum2color={1:BLUE,
            2:GREEN,
            3:PINK,
            4:PURPLE,
            5:ORANGE,
            6:GREY,
            7:KHA,
            8:YEL,
            9:OR,
            10:SAM,
            11:LAS}
        for sq in board.global_hints:
            num=len(board.global_hints[sq])
            if num in solnum2color:
                col=solnum2color[num]
            else:
                col=RED
            colors[sq]=col
        fname='%ssq_hintcounts'%(board.levelnum)
        worktype=board.levelnum
        imgtext='sq hintcounts!\nblue:1\ngreen:2\npink:3\npurple:4\norange:5\ngrey:6\nkhaki:7\nyellow:8\nredorange:9\nsalmon:10\nlast:11\nRED:else'
        pshow(overwrite=0, rows=board.rows,fname=fname,worktype=worktype,imgtext=imgtext,special_dict=colors)

def save_global_hints(board,global_hints=None,ii=None,force=False, extra_text=None, rm=None, green=None, red=None, blue=None, yellow=None):
        return
        if not extra_text:
            extra_text=''
        if not global_hints:
            global_hints=board.global_hints
            force=True
        if not force and config.randomly_save_hints:
            if random.randrange(config.save_hints_every)!=0:
                return
        hintdict={}
        inouts={}
        for pos,hints in global_hints.items():
            if rm:
                if pos not in rm.orig_sqs:
                    continue
            ins,outs=set(),set()
            for h in hints:
                ins.add((h[0]+2)%4)
                outs.add(h[1])
            res={}
            for n in [0,1,2,3]:
                num=0
                if n in ins:
                    num+=1
                if n in outs:
                    num+=2
                res[n]=num
            code=res2code(res)
            if len(ins)==1 and len(outs)==1:
                inouts[pos]=str(h[0])+str(h[1])
            else:
                hintdict[pos]=code
        undet,det=len(hintdict),len(inouts)
        if not ii:ii=''
        ii=str(ii)
        extra_text+=' time:%s '%str(config.LO)
        if config.bump_prune:
            extra_text+='bump'
        else:
            extra_text+='nobump'
        fname='%s-hints-%s-un%06d-det%06d-%s'%(board.levelnum,ii,undet, det,extra_text)
        worktype=board.levelnum
        imgtext='%s-%s HINTS\nundet:%05d\ndet:%05d \n%0.3f%% %s!'%(board.levelnum, str(ii), undet, det, 100.0*det/(det+undet), extra_text)
        special_dict={}
        if green:
            fname='%s-bumps-%s-%s'%(board.levelnum,str(green[0][0]), str(green[0][1]))
            for g in green:
                special_dict[g]=(140,250,140)
                if g in inouts:
                    inouts.pop(g)
        if red:
            for r in red:
                special_dict[r]=(250,140,140)
                if r in inouts:
                    inouts.pop(r)
        if blue:
            fname='%s-transbumps-%s-%s'%(board.levelnum,str(green[0][0]), str(green[0][1]))
            for b in blue:
                special_dict[b]=(140,140,250)
                if b in inouts:
                    inouts.pop(b)
        if yellow:
            for y in yellow:
                special_dict[y]=(250,250,140)
                if y in inouts:
                    inouts.pop(y)
        if 'DONE' in fname:
            #~ import ipdb;ipdb.set_trace()
            pshow(rows=board.rows,inouts=inouts,hintdict=hintdict,fname=fname,worktype='allhints',imgtext=imgtext, special_dict=special_dict, force=force)
        if 'bumps' in fname:
            pshow(rows=board.rows,inouts=inouts,hintdict=hintdict,fname=fname,worktype='allhints',imgtext=imgtext , special_dict=special_dict, force=1, overwrite=0)
        pshow(rows=board.rows,inouts=inouts,hintdict=hintdict,fname=fname,worktype=worktype,imgtext=imgtext , special_dict=special_dict, force=force)
        #~ print 'undetermined %06d determined %06d'%(undet, det)

def load_global_hints_pickle(levelnum):
        if not config.load_global_hints_pickle:
            return {}
        picklename='pickles/%sglobal_hints.pickle'%levelnum
        res=general_load_pickle(picklename)
        return res

def save_global_hints_pickle(levelnum,data):
    if not config.load_global_hints_pickle:
        return
    picklename='pickles/%sglobal_hints.pickle'%levelnum
    general_save_pickle(picklename,data=data)


if __name__=="__main__":
    a=loadrows('test')
    import pprint
    pprint.pprint(a)
