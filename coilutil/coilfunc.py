import os,time,urllib,urllib2,types,Image,ImageFont,ImageDraw

from coilconfig import *

def maketext(orig):
    sp=orig.split("=")
    x=int(sp[1].replace("&y",""))
    y=int(sp[2].replace("&board",""))
    b=sp[3]
    b=b.replace(".","0").replace("X","1")
    #print " b is",b
    text=''
    while b:
        #print len(b)
        this=b[:x]
        b=b[x:]
        text+=this+"\n"
    return text    
def getvec(d):
    if d=='U':
        return [0,-1]
    if d=='D':
        return [0,1]   
    if d=='L':
        return [-1,0]
    if d=='R':
        return [1,0]

def getd(vec):
    if vec%4==0:
        return 'R'
    if vec%4==1:
        return 'D'
    if vec%4==2:
        return 'L'
    if vec%4==3:
        return 'U'
        
        
        
def choosesquare(death_counts,still_todo):
    #print "choosing square..."
    best=still_todo[0]
    maxsofar=death_counts[still_todo[0]]
    for k in still_todo:
        v=death_counts[k]
        #print k,"=",v
        if v>maxsofar:
            best=k
            maxsofar=v
    #print "chose best:",best,"with val",maxsofar
    if ginorder:
        best=still_todo[0]
        maxsofar=death_counts[still_todo[0]]
    return best,maxsofar
        
        
        
        


        

def pshow(b,special=[],special2=[],save=0,fname=None,imgtext=''):
    #print "special is",special
    #print "special2 is",special2
    #print 'got text',imgtext
    try:
        thisdone=[b.justmoved[-1]]
        thisdone=thisdone[0]
    except:
        thisdone=[]
    if type(special)==types.TupleType:
        special=[special]
    #print "thisdone was",type(thisdone),thisdone
    #print "thisdone[0] was",type(thisdone[0]),thisdone[0]
    scale=15
    
    size=(scale*(b.maxx+1),scale*(b.maxy+1))
    if not imgtext=='':
        size=(scale*(b.maxx+1),scale*(b.maxy+15))
    red=Image.open(open("images"+str(scale)+"\\red.bmp",'r'))
    #red.show()
    black=Image.open(open("images"+str(scale)+"\\black.bmp",'r'))
    green=Image.open(open("images"+str(scale)+"\\green.bmp",'r'))
    #green.show()
    white=Image.open(open("images"+str(scale)+"\\white.bmp",'r'))
    turq=Image.open(open("images"+str(scale)+"\\turq.bmp",'r'))
    blue=Image.open(open("images"+str(scale)+"\\blue.bmp",'r'))
    whiteborder=Image.open(open("images"+str(scale)+"\\whiteborder.bmp",'r'))
    im=Image.new('RGB',size)
    for y,r in enumerate(b.rows):
        for x,e in enumerate(r):
            pixloc=(scale*x,scale*y)
            if (x,y)==(b.now):
                im.paste(red,pixloc)
                continue
            if (x,y) in thisdone:
                im.paste(blue,pixloc)
                continue
            if (x,y) in special:
                im.paste(green,pixloc)
                continue
            if (x,y) in special2:
                im.paste(turq,pixloc)
                continue
            if e==0:
                im.paste(whiteborder,pixloc)
            if e==1:
                im.paste(black,pixloc)
    
    if imgtext:
        tsp=imgtext.split("\n")
        n=0
        for line in tsp:
            
            loc=(10,scale*(b.maxy+n))
            n+=1
            font=ImageFont.truetype('arial.ttf',16)
            dd=ImageDraw.ImageDraw(im)
            #print font,dd,text,loc
            dd.text(loc,text=line,font=font)
    
    if save:
        if fname==None:
            for n in range(100):
                fname="coil%4d"%n+".png"
                fname=fname.replace(" ","0")
                out=os.path.join("output",fname)
                if os.path.exists(out):
                    continue
                break
        else:
            fname=str(fname)+".png"
        out=os.path.join("output",fname)
        im.save(out)
        #print "SAVED"
    else:
        im.show()

def getboard(doboard,limited=0,glogin=0):
    #print "in getboard",doboard,glogin
    if doboard:
        limited=1
        level=doboard
        doboardfile=os.path.join("levels",str(level)+".txt")
        res=[open(doboardfile,'r').readline()]
    else:
        url="http://www.hacker.org/coil/index.php"
        if glogin:
            url=url+"?name=ernie&password=hacker7"
        #print "getting level:"
        res=urllib.urlopen(url).readlines()
        #print "got"
    
    #print "got res",res,"level",level,type(res)
    for l in res:
        l=l.strip()
        if not l.find("Level: ")==-1:
            #print l
            try:
                lsp=l.split("Level: ")
                level=int(lsp[1].split("<")[0])
                print "i am in level",level
            except:
                traceback.print_exc()
        if l.startswith("FlashVars"):
            orig=l
            #print "set text to:",l
            break
    #print "got orig:",orig
    text=maketext(orig.replace("\n","").replace('"','').replace("FlashVars=","").replace(" ",""))
    if not limited:
        outfile="levels\\"+str(level)+".txt"
        out=open(outfile,'w')
        out.write(orig)
        out.write("\n\n")
        out.write(text)
        out.close()
    return level,text,1
        
def dodone(b,dsol,gsubmit,glogin,glive,startt):
    baseurl="http://www.hacker.org/coil/index.php"
    if glogin:
        baseurl+="?name=ernie&password=hacker7"
    baseurl+="&"
    solpath=baseurl
    solpath+="x="+str(dsol.start[0]-1)
    solpath+="&y="+str(dsol.start[1]-1)
    solpath+="&path="
    for m in dsol.moves:
        #print m
        solpath+=getd(m)
    print "final path is:"
    print solpath
    print "that one took: %5.4f" % (time.clock()-startt)
    #b.show()
    if glive:
        level=b.level
        out=open('progress.log','a')
        logentry="LEVEL:"+str(level)+"took\t"
        logentry+=str(time.clock()-startt)
        logentry+="finished at "+str(time.asctime())
        logentry+="at X,Y:"
        x,y=b.now
        x=x-1
        y=y-1
        logentry+=str(x)+","+str(y)
        logentry+="\n"
        out.write(logentry)
        out.close()

    if gsubmit:
        submit(b,dsol,solpath)
    if gshowrealmoves:
        print "start at: ",b.now
        print "realmoves:"
        for m in b.realmoves:
            print getd(m)
                            

def submit(b,dsol,solpath):
    tries=5
    while tries:
        try:
            urllib2.urlopen(solpath)
            tries=0
        except:
            time.sleep(35)
            tries+=-1
    #dsol.show()
    
class Solution:
    def __init__(self,start):
        self.start=start
        self.moves=[]
        
    def move(self,d):
        #print "moved",d
        #print self.moves
        self.moves.append(d)

    def show(self):
        count=0
        for m in self.moves:
            print m,
            if count%6==0: 
                print ""
            count+=1

    
        
        