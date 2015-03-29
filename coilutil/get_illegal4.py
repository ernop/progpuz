import time,traceback,config

from admin import save_backtrack
from split_utils import orth,add, dist
import simpleroom

def get_illegal4(board,covered,origpos,endpos,debug=False):
    """
    1. get all rooms adjacent to covered.
    2. check them
    """
    #~ st=time.time()
    #~ inf_il=False
    #~ for il in board.original_illegal_rooms:
        #~ if not covered.isdisjoint(il.orig_allsqs):
            #~ inf_il=True
            #~ break
    #~ if not inf_il:
        #~ return
    if config.skip_predetermined:
        predetermined=True
        for pos in covered:
            if len(board.global_hints[pos])!=1:
                predetermined=False
                break
        if predetermined:
            return
    covered.add(origpos)
    illegalcount=0
    if board.alley:
        illegalcount+=1
    if board.air:
        illegalcount+=1
    to_try=[]
    for c in covered:
        to_try.extend([(c[0]+1,c[1]),(c[0]-1,c[1]),(c[0],c[1]+1),(c[0],c[1]-1),])
    to_try=[t for t in to_try if board.rows[t[1]][t[0]]==0]
    rms=[]
    oksubrooms=[]
    #~ rmkeys=[]
    #~ subkeys=[]
    hashids=[]
    for pos in to_try:
        for rm in board.pos2allrooms(pos):
            if rm.hashid in hashids:
                continue
            hashids.append(rm.hashid)
            if rm.kind=='pararooms':
                skiproom=False
                for rmpos in rm.orig_gatesqs:
                    if dist(rmpos, board.startpos)==1:
                        skiproom=True
                        break
                #CHECK THIS
                if skiproom:
                    #~ print 'skiproom'
                    continue
            subrooms=rm.make_leftover_subrooms(board.rows, externalendpos=endpos)
            for sub in subrooms:
                #~ if sub.key in subkeys:
                    #~ continue
                #~ subkeys.append(sub.key)
                oksubrooms.append(sub)
    #maybe add in newly created optrooms here.
    oksubrooms.sort(key=lambda x:len(x.orig_allsqs))
    for subroom in oksubrooms:
        if board.alley and board.alley in subroom.orig_allsqs:
            continue
        #~ if board.air and (not board.air.orig_allsqs.isdisjoint(subroom.orig_allsqs) or not board.air.get_tunnelsqs(board).isdisjoint(subroom.orig_allsqs)):
            #~ board.counts[subroom.usage]['illegal_i']+=1
            #~ continue
        res=subroom.has_sol(toplevel=True)
        if res=='timeout':
            board.counts[subroom.usage]['timeout']+=1
            continue
        elif res:
            board.counts[subroom.usage]['not_illegal']+=1
            continue
        else:
            board.counts[subroom.usage]['illegal']+=1
            illegalcount+=1
            if board.air and not subroom.orig_allsqs.isdisjoint(board.air.orig_allsqs):
                illegalcount-=1
                #we will replace the air.
            #~ else:
                #~ board.air=subroom
            #if it's a sub illegal room of an air, have it take over from the air (and so if there's another illegal within the air
            #that will make us fail.  and if it's just independent from air, we die now.
            
        if illegalcount>1:
            save_backtrack(board,text='gl4bt',extra_illegalroom=subroom)
            return illegalcount
        #we just found our first illegal, or we found another illegal room.
        #actually we should keep the smaller illegal if it is possible... we should keep them both!
        #ideally we'd keep them both if they are nonsuperior to eachother.  then if we find another illegal room
        #that doesn't interset even one of them, we can just bt!  this could have been what's going wrong, actually...
        if board.air and len(subroom.orig_allsqs)>len(board.air.orig_allsqs):
            pass
            #skip when air intersets (as it must do here) and is larger.
        else:
            board.air=subroom
            board.air.get_tunnelsqs(board)
        
        
    covered.remove(origpos)
    #~ took=time.time()-st
    #~ if took>1:
        #~ print 'took %0.4f'%took
    return False
