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

def get_covers(board,shapes,depth=0,use_global=False,use_fullboard_identical=False):
    ''''''
    global GLOBAL_BAD
    allres=[]
    #pick one spot to cover
    spot=pick_spot(board)
    if not spot:
        print '!'*30
        import ipdb;ipdb.set_trace()
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
                            #genuinely skipping something
                            #print 'B'*20
                            #show(newboard)
                            board_sub(newboard,adder)
                            continue
                        if depth==0:
                            #add some global illegal positions (fliprots of the initial placement all can be skipped in future)
                            bad_positions=fliprots(newboard.copy(),preserve_hw=True)
                            #for every single possible sq placement of this, its illegal.
                            for bp in bad_positions:
                                GLOBAL_BAD.add(tuple(sorted([sq for sq in bp if bp[sq]!=0])))
                    if 0 and use_fullboard_identical:
                        #exclde all globally identical positions
                        tester=tuple(sorted([k for k in newboard.keys() if newboard[k]!=0]))
                        if tester in GLOBAL_BAD:
                            board_sub(newboard,adder)
                            print 'r',
                            continue
                        bad_positions=fliprots(newboard.copy(),preserve_hw=True)
                        for bp in bad_positions:
                            GLOBAL_BAD.add(tuple(sorted([sq for sq in bp if bp[sq]!=0])))
                        print 'n',
                    if random.random()<0.005:
                        show(newboard)
                    #adding this was ok.  go deeper.
                    subsols=get_covers(newboard,remaining_shapes,depth=depth+1,use_fullboard_identical=True)
                    if subsols:
                        allres.extend(subsols)
                    #only need to subtract if we added since board_add does nothing if fails.
                    board_sub(board,adder)
    
    print '*'*depth,len(allres),len(GLOBAL_BAD)
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

WIDTH=5
HEIGHT=8
board=simple_board(WIDTH,HEIGHT)
shapes=PENTOS.values()
if 1:
    shapes=[]
    for n in range(4):
        shapes.append(name_shape(Z.copy(),n+97-32))
    for n in range(4):
        shapes.append(name_shape(P.copy(),n+97-32+8))
    #for n in range(4):
        #shapes.append(name_shape(X.copy(),n+97-32+10))
    #for n in range(4):
        #shapes.append(name_shape(V.copy(),n+97-32+15))
    
#shapes=[I]*45
#shapes=PENTOS
st=time.clock()
res=get_covers(board,shapes,use_global=False,use_fullboard_identical=True)
res=get_canonicals(res,preserve_hw=True)
print '='*50,'DONE'
for r in res:
    show(r)
took=time.clock()-st
print '%dx%d got: %d in %0.5f'%(WIDTH,HEIGHT,len(res),took)