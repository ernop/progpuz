from util_dict import *
import random,time
from shapes_dict import *

def pick_spot(board):
    for xx in range(WIDTH):
        for yy in range(HEIGHT):
            if board[(xx,yy)]==0:
                return (xx,yy)
    return False

def show_board(board):
    print '+'*20
    for xx in range(WIDTH):
        for yy in range(HEIGHT):
            if (xx,yy) in board:
                print board[(xx,yy)]
            else:
                print '-',
        print '\n',
    print '='*20

GLOBAL_BAD=set()

def test_neighbor_placement(board, adder, remaining_shapes):
    '''for every open neighbor of adder, does one of the remaining shapes even fit to cover it?'''
    done=[]
    for sq in adder:
        for nei in neighbors(sq):
            if nei not in board:continue
            if nei not in done:
                done.append(nei)
                if isempty(nei, board):
                    lastshape=None
                    res=get_covers(board,remaining_shapes,subquery=True,spot=nei)
                    if not res:
                        return False
    return True
                         
def get_covers(board,shapes,depth=0,use_global=False,use_fullboard_identical=False,subquery=False,spot=None):
    ''''''
    global GLOBAL_BAD
    allres=[]
    #pick one spot to cover
    if spot:
        pass
    else:
        spot=pick_spot(board)
        if not spot:
            print '!'*30
            #import ipdb;ipdb.set_trace()
            show(board)
            bb=board.copy()
            return [bb,]
    lastshape=None
    for ii,shape in enumerate(shapes):
        if shape==lastshape:
            continue
        lastshape=None
        remaining_shapes=shapes[:]
        remaining_shapes.remove(shape)
        for jj,fr in enumerate(fliprots(shape)):
            for kk,sq in enumerate(fr):
                adder=translate(fr,sub(spot,sq))
                newboard=board_add(board,adder)
                #does it fit in the current board, without going out of bounds?
                if newboard:
                    if use_global:
                        tester=tuple(sorted(adder.keys()))
                        if tester in GLOBAL_BAD:
                            board_sub(newboard,adder)
                            continue
                        if depth==0:
                            #add some global illegal positions (fliprots of the initial placement all can be skipped in future)
                            #this doesnt work if you have multiple copies of the same shape
                            bad_positions=fliprots(newboard.copy(),preserve_hw=True)
                            #for every single possible sq placement of this, its illegal.
                            for bp in bad_positions:
                                GLOBAL_BAD.add(tuple(sorted([sq for sq in bp if bp[sq]!=0])))
                    if 0 and use_fullboard_identical:
                        #exclde all globally identical positions
                        #this might miss some solutions if the fullboard identical position can be reached multiple ways.
                        tester=tuple(sorted([k for k in newboard.keys() if newboard[k]!=0]))
                        if tester in GLOBAL_BAD:
                            board_sub(newboard,adder)
                            print 'r',
                            continue
                        bad_positions=fliprots(newboard.copy(),preserve_hw=True)
                        for bp in bad_positions:
                            GLOBAL_BAD.add(tuple(sorted([sq for sq in bp if bp[sq]!=0])))
                        print 'n',
                    
                    #adding this was ok.  go deeper.
                    
                    if not subquery:
                        if not test_neighbor_placement(newboard, adder, remaining_shapes):
                            board_sub(newboard, adder)
                            print 'prune',
                            continue
                        else:
                            print 'unprune'
                            
                        
                    
                    if random.random()<0.005:
                        show(newboard)
                    if subquery:
                        #any piece was available to place there.
                        board_sub(newboard,adder)
                        return True
                    subsols=get_covers(newboard,remaining_shapes,depth=depth+1,use_fullboard_identical=True)
                    if subsols:
                        allres.extend(subsols)
                    #only need to subtract if we added since board_add does nothing if fails.
                    board_sub(board,adder)
    
    #if not subquery:print '*'*depth,len(allres),len(GLOBAL_BAD)
    return allres

def board_add(board,adder):
    for sq in adder:
        if sq not in board or board[sq]!=0:
            return False
    for sq in adder:
        board[sq]=adder[sq]
    return board

def board_sub(board,adder):
    for sq in adder:
        if sq not in board:
            continue
        if board[sq]!=adder[sq]:
            import ipdb;ipdb.set_trace()
            
        board[sq]=0        

def simple_board(width,height):
    board={}
    for xx in range(width):
        for yy in range(height):
            board[(xx,yy)]=0
    return board

def name_shape(shape,ii):
    for k in shape:
        shape[k]=chr(ii)
    return shape

WIDTH=10
HEIGHT=9

shapes=PENTOS.values()
if 1:
    shapes=[]
    for n in range(6):
        shapes.append(name_shape(L.copy(),n+97-32))
    for n in range(6):
        shapes.append(name_shape(N.copy(),n+97-32+8))
    for n in range(6):
        shapes.append(name_shape(V.copy(),n+97-32+10))
    #for n in range(4):
        #shapes.append(name_shape(V.copy(),n+97-32+15))
    
#shapes=[I]*45
#shapes=PENTOS
shapes=PENTOS.values()
HEIGHT=4
WIDTH=15
board=simple_board(WIDTH,HEIGHT)

st=time.clock()
res=get_covers(board,shapes,use_global=False,use_fullboard_identical=True)
res=get_canonicals(res,preserve_hw=True)
print '='*50,'DONE'
for r in res:
    show(r)
took=time.clock()-st
print '%dx%d got: %d unique in %0.5f'%(WIDTH,HEIGHT,len(res),took)