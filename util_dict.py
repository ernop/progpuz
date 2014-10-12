#all functions operate on sets.
#except ones ending _dict which operate on dicts (to allow tracking the distinctness of the original shape)

def sub(a,b):
   return (a[0]-b[0],a[1]-b[1])

def ULzero(shape):
   #move upper left square to zero
   minx=min([sq[0] for sq in shape.keys()])
   miny=min([sq[1] for sq in shape.keys()])
   return {(k[0]-minx,k[1]-miny):v for k,v in shape.items()}
  
def rot(shape):
   #rot x==>y,  y==>-x
   #return set([(sq[1],-1*sq[0]) for sq in shape])
   return {(k[1],-1*k[0]):v for k,v in shape.items()}

def flip(shape):
   return {(-1*k[0],k[1]):v for k,v in shape.items()}
   #return set([(-1*sq[0],sq[1]) for sq in shape])

FLIPROTS={}

def fliprots(shape,preserve_hw=False):
   '''all unique (over translation, flipping, rotation) versions of a shape'''
   global FLIPROTS
   ss=tuple(sorted(shape.items()))
   if ss in FLIPROTS:
      return FLIPROTS[ss]
   res=[]
   if preserve_hw:
      orig_hw=get_hw(shape)
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
      if preserve_hw:
         if get_hw(rr)!=orig_hw:
            continue
      res2.append(rr)
   FLIPROTS[ss]=res2
   
   return res2

def test_add(aa,bb):
   '''see if they overlap'''
   res={}
   for shape in (aa,bb,):
       for sq in shape:
         if sq in res:
            return False
         res[sq]=shape[sq]
   return res

def neighbors(s):
   return ((s[0]-1,s[1]),(s[0]+1,s[1]),(s[0],s[1]+1),(s[0],s[1]-1))

def translate(shape, coord):
   if coord==(0,0):return shape.copy()
   return {(sq[0]+coord[0],sq[1]+coord[1]):v for sq,v in shape.items()}

def isempty(sq,shape):
   return shape[sq]==0

#all additions of T+L:
def all_combinations(bigger,smaller):
   possibles=[]
   for fr in fliprots(bigger):
      for sq in fr:
         for neighbor in neighbors(sq):
            if isempty(neighbor,fr):
               for smallersq in smaller:
                  news2=translate(smaller,sub(neighbor,smallersq))
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

def get_canonicals(shapes,preserve_hw=False):
   '''preserve the same hxw profile or not?'''
   res=[]
   for sh in shapes:
      can=get_canonical(sh,preserve_hw=preserve_hw)
      if can in res:
         continue
      res.append(can)
   return res

def get_hw(shape):
   kk=shape.keys()
   return [max([sq[0] for sq in kk])+1,max([sq[1] for sq in kk])+1]

def get_canonical(shape,preserve_hw=False):
   '''return the preferred flip, rotation, translation of a shape'''
   bestval=0
   best=None
   hw=get_hw(shape)
   for shape in fliprots(shape):
      if get_hw(shape)!=hw:
         continue
      val=canonical_value(shape)
      if not bestval or val>bestval:
         best=shape
         bestval=val
   return best

def canonical_value(shape):
   '''arbitrary thing to order shapes by'''
   shape2=ULzero(shape)
   import md5
   val=md5.md5(str(sorted(shape2.items()))).hexdigest()
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

def show_set(shape,mxx=0,myy=0):
   print '*'*30
   maxx=max(mxx-1,max([sq[0] for sq in shape]))
   maxy=max(myy-1,max([sq[1] for sq in shape]))
   for yy in range(maxy+1):
      for xx in range(maxx+1):
         sq=(xx,yy)
         if sq in shape:
            print '*',
         else:
            print '-',
      print '\n',
   print '='*30

def show(shape,mxx=0,myy=0):
   if type(shape) in (set,tuple):
      return show_set(shape,mxx=mxx,myy=myy)
   print '*'*30
   maxx=max(mxx-1,max([sq[0] for sq in shape]))
   maxy=max(myy-1,max([sq[1] for sq in shape]))
   for yy in range(maxy+1):
      line=''
      for xx in range(maxx+1):
         
         sq=(xx,yy)
         if sq in shape:
            line+=str(shape[sq])
         else:
            line+='-'
      print line
   print '='*30

def combine(a,b):
   possibles=all_combinations(a,b)
   canonical=get_canonicals(possibles)
   canonical.sort(key=lambda x:canonical_value(x))
   return canonical

def combine_many(many,shape):
   res=[]
   for guy in many:
      res.extend(combine(guy,shape))
   canonical=get_canonicals(res)
   canonical.sort(key=lambda x:canonical_value(x))
   return canonical
