import random,datetime,os
random.seed(1001)

from util_dict import *
import random,time
from shapes_dict import *

#make a field out of a set of pieces

TIME_FORMAT='%Y-%m-%d-%A-%H%M%S' # '2012-09-20-Tuesday-1816'

def output_html(board,override_name=None):
    '''board as a table.'''
    if override_name:
        fn=override_name
    else:
        fn=get_fn(board)
    if not os.path.isdir("field-out"):
        os.mkdir('field-output')
    fp='field-output/%s.html'%fn
    out=open(fp,'w')
    lines=[]
    HTMLHEADER=open('html/field-header.html','r').read()
    lines.append(HTMLHEADER)
    htmlout={}
    #import hashlib
    #hexmatch=hashlib.md5(str(sorted(board.items()))).hexdigest()=='cf9d1d3126ceb6fbdea9c892fd03ff0a' 
    for kk,vv in sorted(board.items()):
        #if hexmatch and kk==(2,-1):
            #import ipdb;ipdb.set_trace()
        if vv==0:
            pentonum=0
        else:
            pentonum=vv%12
            if pentonum==0:
                pentonum=12
        klasses=[]
        if pentonum:
            for name,nei in named_neighbors(kk):
                if nei in board:
                    if board[nei]!=board[kk]:
                        klasses.append('%s-diff'%name)
        klasses.append('pento-%d'%pentonum)
        strklass=' '.join(klasses)
        res='<td class="%s">%s</td>'%(strklass,pentonum and str(pentonum) or '')
        htmlout[kk]=res
    minx=min([x[0] for x in htmlout.keys()])
    maxx=max([x[0] for x in htmlout.keys()])
    miny=min([x[1] for x in htmlout.keys()])
    maxy=max([x[1] for x in htmlout.keys()])
    lines.append('<table cellpadding=0 cellspacing=0 class="pento-table>"')
    for yy in range(miny,maxy+1):
        lines.append('<tr>')
        for xx in range(minx,maxx+1):
            lines.append(htmlout[xx,yy])
    lines.append('</table>')
    for l in lines:
        out.write(l+'\n')
    out.close()
        
def get_fn(board):
    dt=datetime.datetime.now().strftime(TIME_FORMAT)
    if 'name' in board:
        name=board['name']
    else:
        name='no name'
    area=''
    pieces='5'
    fn='%s_%s_%s_%s'%(name,dt,pieces,area)
    return fn
    
    
def test_output():
    testboard={}
    for xx in range(20):
        for yy in range(10):
            val=int(random.random()*24)
            if val>12:
                val=0
            testboard[(xx,yy)]=val
    
    output_html(testboard)

def copy_remove(pieces,piece):
    remaining_pieces=sorted([pp.copy() for pp in pieces])
    for pp in remaining_pieces:
        if set(pp.items())==set(piece.items()):
            remaining_pieces.remove(pp)
            break
    return remaining_pieces

def get_bordering_empty(adder,board):
    new_overlaps=[]
    for addsq in adder:
        neis=neighbors(addsq)
        for nei in neis:
            if board[nei]==0:
                new_overlaps.append(nei)
    return list(set(new_overlaps))

def count(board):
    return len([v for v in board.values() if v])

def floodfill(board,start,killers=None):
    if not killers:
        killers=set()
    done=set()
    todo=set()
    todo.add(start)
    while todo:
        nei=todo.pop()
        if nei in done:continue
        if nei in killers:
            return False,done
        if nei not in board:
            return False,done
        if not board[nei]==0:
            continue
        todo.update(neighbors(nei))
        done.add(nei)
        if len(done)>MAX_FIELD:
            return False,done
    return True,done

def get_all_neighbors(board):
    res=set()
    starts=[sq for sq in board if board[sq]!=0]
    for sq in starts:
        for nei in neighbors(sq):
            if nei in res:continue
            if board[nei]==0:
                res.add(nei)
    return res

def get_totalfield(board):
    neighbors=get_all_neighbors(board)
    killers=set()
    totalfield=0
    while neighbors:
        thisnei=neighbors.pop()
        if thisnei in killers:continue
        res,newkillers=floodfill(board, thisnei, killers=killers)
        if res:
            totalfield+=len(newkillers)
        killers.update(newkillers)
    return totalfield

def do(board,pieces,must_overlap,depth,first_overlaps=None):
    '''first piece placement only do once...
    after the first placement, track first overlaps so that you can 
    skip cases where the last piece placed doesn't overlap first overlaps.
    '''
    myres=[]
    for spot in must_overlap:
        for piece in pieces:
            remaining_pieces=copy_remove(pieces,piece)
            for fliprot in fliprots(piece):
                for sq in fliprot:
                    #place sq at spot
                    adder=translate(fliprot,sub(spot,sq))
                    newboard=board_add(board,adder)
                    if not newboard:
                        continue
                    if remaining_pieces:
                        new_overlaps=get_bordering_empty(adder, board)
                        if depth==0:
                            first_overlaps=set(new_overlaps[:])
                        newres=do(board,remaining_pieces,new_overlaps,depth=depth+1,first_overlaps=first_overlaps)
                        myres.extend([nn for nn in newres if nn not in myres])
                        if len(myres)>MAXRES:
                            break
                    else:
                        #check that this adder intersects with first overlaps
                        if not first_overlaps.intersection(adder.keys()):
                            pass
                            #(fall through and board_sub)
                        else:
                            cc=board.copy()
                            if cc in myres:
                                pass
                            else:
                                #check that its really a field
                                #there is no easy way to check something is a field based only on the first & last piece placement.
                                #proof: making a field out of a giant box with 100 squares, and two small I pieces.  The field won't necessarily border the first/last piece
                                #so you have to check them all.
                                totalfield=get_totalfield(board)
                                if totalfield:
                                    if totalfield>=MAX_FIELD/3:
                                        print 'got one',len(myres),depth,totalfield
                                        myres.append(cc)
                                        output_html(board,override_name='got one %d field=%d'%(len(myres),totalfield))
                                else:
                                    pass
                    board_sub(board,adder)
                    if depth==0:
                        break
                    if len(myres)>MAXRES:
                        break
                if depth==0:
                    break
                if len(myres)>MAXRES:
                    break
            if depth==0:
                #only put one piece
                break
            if len(myres)>MAXRES:
                break
        if depth==0:
            #only put one piece
            break
        if len(myres)>MAXRES:
            break
            
    return myres
                    

seven=[DICT_PENTOS['L'].copy(),
        DICT_PENTOS['I'].copy(),
        DICT_PENTOS['X'].copy(),
        DICT_PENTOS['P'].copy(),
        DICT_PENTOS['Y'].copy(),
        DICT_PENTOS['V'].copy(),
        DICT_PENTOS['T'].copy()]                 
                    
five=[DICT_PENTOS['L'].copy(),
        DICT_PENTOS['I'].copy(),
        DICT_PENTOS['X'].copy(),
        DICT_PENTOS['P'].copy(),
        DICT_PENTOS['T'].copy()]
IS=[DICT_PENTOS['I'].copy(),
        DICT_PENTOS['I'].copy(),
        DICT_PENTOS['I'].copy(),
        DICT_PENTOS['I'].copy(),
        DICT_PENTOS['I'].copy()]

easy=[DICT_PENTOS['L'].copy(),
        DICT_PENTOS['L'].copy(),
        ]

mid=[DICT_PENTOS['L'].copy(),
        DICT_PENTOS['L'].copy(),
        DICT_PENTOS['I'].copy(),
        ]

pieces=easy
pieces=mid
pieces=IS
pieces=five
pieces=seven

#should fix this so same type pieces have the same number.
seen_counts={}
mods={0:-1}
for ii,pp in enumerate(pieces):
    _,letter=pp.items()[0]
    if letter not in mods:
        
        mods[letter]=max(mods.values())+1
    seen_counts[letter]=seen_counts.get(letter,0)+1
    use_val=(seen_counts[letter])*12+mods[letter]
    for kk in pp.keys():
        pp[kk]=use_val

MAXRES=10000

MAX_FIELD=((5*len(pieces)-2)/4)**2
#best case square allocation is a big square.  
#so when doing floodfill, stop after that many

board={}
for xx in range(-15,15):
    for yy in range(-15,15):
        board[(xx,yy)]=0
res=do(board,pieces,[(0,0)],depth=0)
bestsofar=0
for ii,bb in enumerate(res):
    totalfield=get_totalfield(bb)
    bestsofar=max(totalfield,bestsofar)
    if bestsofar==totalfield:
        output_html(bb,override_name='%03d-done%d'%(totalfield,ii))
#import ipdb;ipdb.set_trace()