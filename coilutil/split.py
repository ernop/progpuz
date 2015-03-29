#There are rooms where every pos has only one acceptable hint, but there are more than one remaining sol.
###
###in general, POS is the global positions
###(we add a border around the board, which is visible in the logical sections - the upper left open square of the board is 1,1
###but submission and stufff will take care of that
###sq refers to a relative pos, inside a room.  so it's like pos=~rooms xoffset + sq + border stuffs.

import os,sys,time,traceback,random,pprint,copy,shutil,hashlib
try:
    import cPickle
except:
    import pickle as cPickle

import config
import simpleroom
import admin
import config as settings
from board import Board
from get_illegal4 import get_illegal4
from split_utils import *
from admin import *
from simpleroom import *

sys.setrecursionlimit(9000)
boardhashes=set()

def move(board,now,dv,lastdv,onestep=False):
    next=add(now,dv)
    covered=set()
    sawr=[]
    sawl=[]
    lastr=[]
    lastl=[]
    #lastr, lastl are running lists of the open line of squares seen on either side.
    #if at some moment the squares on one side stop being open, there are some things that need to happen
    #maybe this new square is already in the glob, meaning we're split.
    #now,bump,covered,movebacktrack,movedata,next_dvs,glob_change
    next_dvs=[]
    movebacktrack=False
    movedata=''
    board.vergr=[]
    board.vergl=[]
    back=add(now,dv+2)
    glob_change=set()
    firstpos=now
    while board.isopen(next):
        if config.check_hints and (lastdv, dv) not in board.global_hints[now] and not (board.air and now in board.air.orig_allsqs):
            bad=False
            if board.air:
                if now in board.air.get_tunnelsqs(board):
                #don't mind violating a hint in the tunnelsq of a current illegal!
                    bad=True
                #and, if you violate a hint and your reqrm is touching the current air, its not actually a violation.
                #so, this is slightly better than just preemptively removing starting req room hints.
                #actually this is not any better.  in the case of a merge one, we may hav reduced it to a smaller one but itll still be part of the reqrms
                #which means that we will never be able to bt in the orig reqrm
                if not bad:

                    reqrms=board.pos2rooms[now].get('reqrooms',[])
                    for reqrm in reqrms:
                        if not reqrm.orig_allsqs.isdisjoint(board.air.orig_allsqs):
                            bad=True
                            break
            if not bad:
                if config.skip_hintchecks_while_in_orig_illegal:
                    for il in board.original_illegal_rooms:
                        if now in il.orig_allsqs:
                            bad=True
                            break
            if not bad:
                if board.alley:
                    rms=board.pos2allrooms(board.alley)
                    for rm in rms:
                        if now in rm.orig_allsqs:
                            bad=True
                            break
                            #if a room has been made into an alley, skip if we are in any of that guy's rooms... this could hurt later.
                            #for now just skip optrooms, hope we don't have to bump to reqrooms.
            #or, if we are in the same room as a start no matter what.
            if not bad:
                startrms=board.pos2allrooms(board.start[0])
                for rm in startrms:
                    if now in rm.orig_allsqs:
                        bad=True
                        break
        #this means we can't use hints around the startroom... annoying.
            if not bad:
                illegalcount=0
                if board.alley:illegalcount+=1
                if board.air:illegalcount+=1
                inout=(lastdv,dv)
                if 0 and inout not in board.global_hints[now]:
                    #violated hint.
                    #from the hint violation!
                    illegalcount+=1
                    if illegalcount>1:
                        #it was illegal; you are done!
                        movebacktrack=True
                        movedata='viola-'+str(now)
                        board.set_many(covered)
                        save_backtrack(board=board,text='v.hint'+movedata,violated_hint=(now,inout),force=0)
                        board.unset_many(covered)
                        board.counts['vhint']['bt']+=1
                        return now,None,covered,movebacktrack,movedata,next_dvs,glob_change
                    #do nothing now.  hints can only kill a var - but we don't save when they pop up.
                    #hopefully other methods will be able to identify the room we have fucked up.
                    board.counts['vhint']['notenough']+=1
                    reqrm=reqrm_at_end_of_tunnel(board, now)
                    board.air=reqrm
                    board.air.get_tunnelsqs(board)
                    #~ print 'promoted new ilroom due to hint violation!'
    #~ else:
            #~ board.counts['vhint']['ok']+=1
        lastdv=dv
        now=next
        covered.add(now)
        rpos=add(now,dv+1)
        lpos=add(now,dv-1)
        if board.isopen(rpos):
            lastr.append(rpos)
        else:
            if lastr:
                if rpos in board.glob:
                    movedata='split-while-moving-right'
                    movebacktrack=True
                    return now,None,covered,movebacktrack,movedata,[],glob_change
                else:
                    newglob=glob_diff(board.allneighbors,board,rpos,board.glob)
                    board.glob.update(newglob)
                    glob_change.update(newglob)
                sawr.append(lastr)
                lastr=[]
        if board.isopen(lpos):
            lastl.append(lpos)
        else:
            if lastl:
                if lpos in board.glob:
                    movedata='split-while-moving-left'
                    movebacktrack=True
                    return now,None,covered,movebacktrack,movedata,[],glob_change
                else:
                    newglob=glob_diff(board.allneighbors,board,lpos,board.glob)
                    board.glob.update(newglob)
                    glob_change.update(newglob)
                sawl.append(lastl)
                lastl=[]
        next=add(now,dv)
        if onestep:
            break
    if lastr:
        board.vergr=lastr
        next_dvs.append((dv+1)%4)
    if lastl:
        board.vergl=lastl
        next_dvs.append((dv-1)%4)
    bump=next
    board.sawl=sawl
    board.sawr=sawr
    if board.isopen(back):
        board.back=[back]
    else:
        board.back=None

    if onestep:
        if board.isopen(next):
            bump=None
        if not bump:
            next_dvs.append(dv)
        if (board.vergr) and (board.vergl):
            if bump and bump in board.glob:
                movedata='split-bump'
                #~ pdb.set_trace()
                movebacktrack=True
                #~ if firstpos in covered:
                    #~ pdb.set_trace()
                    #~ print 'stf'
                return now,None,covered,movebacktrack,movedata,[],glob_change
            if (dv+1)%4 not in next_dvs:next_dvs.append((dv+1)%4)
            if (dv-1)%4 not in next_dvs:next_dvs.append((dv-1)%4)
        elif (not board.vergr and not board.vergl):
            if bump:
                movebacktrack=True
            if board.curopen==len(covered):
                movedata=0
                movebacktrack=False
                return now,None,covered,movebacktrack,movedata,[],glob_change
        elif board.vergr:
            if (dv+1)%4 not in next_dvs:next_dvs.append((dv+1)%4)
        else: #board.vergl
            if (dv-1)%4 not in next_dvs:next_dvs.append((dv-1)%4)
        movedata='normal_runout'
        return now,bump,covered,movebacktrack,movedata,next_dvs,glob_change

    else:
        if (board.vergr) and (board.vergl):
            if bump and bump in board.glob:
                movedata='split-bump'
                #~ pdb.set_trace()
                movebacktrack=True
                #~ if firstpos in covered:
                    #~ pdb.set_trace()
                    #~ print 'stf'
                return now,None,covered,movebacktrack,movedata,[],glob_change
            next_dvs=[(dv+1)%4,(dv-1)%4]
        elif (not board.vergr and not board.vergl):
            if bump:
                movebacktrack=True
            if board.curopen==len(covered):
                movedata=0
                movebacktrack=False
                return now,None,covered,movebacktrack,movedata,[],glob_change
        elif board.vergr:
            next_dvs=[(dv+1)%4]
        else:
            next_dvs=[(dv-1)%4]
        movedata='normal_runout'
        #~ if firstpos in covered:
            #~ pdb.set_trace()
            #~ print 'stf'

        return now,bump,covered,movebacktrack,movedata,next_dvs,glob_change

def multimove(board,origpos,origdv,lastdv,onestep=False):
    board.multimovecount+=1
    movebacktrack=False
    movedata=''
    next_dvs=[origdv]
    allcovered=set()
    now=origpos
    allsawr=[board.vergr[:]]
    allsawl=[board.vergl[:]]
    allback=[]
    thissol=[]
    glob_change=set()
    one_hint=0
    while (not movebacktrack) and (one_hint or len(next_dvs)==1):
        thissol.append(next_dvs[0])
        board.sol.append(next_dvs[0])
        now,bump,covered,movebacktrack,movedata,next_dvs,movenewglob=move(board,now,next_dvs[0],lastdv,onestep=onestep)


        #
        #return now,None,covered,movebacktrack,movedata,next_dvs,glob_change
        glob_change.update(movenewglob)
        allcovered.update(covered)
        allsawr.extend(board.sawr)
        allsawr.append(board.vergr)
        allsawl.extend(board.sawl)
        allsawl.append(board.vergl)
        if board.back:
            allback.append(board.back[0])
        board.set_many(covered)
        #~ if config.do_one_hint:
            #~ one_hint=len(board.global_hints[now])==1 and (board.air or board.alley)
            #~ if one_hint:
                #~ #just change the dvs to follow the hint!
                #~ next_dvs=[list(board.global_hints[now])[0][1]]


        endnewglob=glob_diff(board.allneighbors,board,now,board.glob)
        glob_change.update(endnewglob)
        board.glob.update(endnewglob)
        lastdv=board.sol[-1]
    newsides=[]
    for side in [allsawr,allsawl]:
        newside=[]
        for section in side:
            for s in section:
                if board.isopen(s) and dist(s,now)>1:
                    newside.append(s)
        newsides.append(newside)
    board.sawr,board.sawl=[[n] for n in newsides]
    board.back=[]
    for b in allback:
        if board.isopen(b) and dist(b,now)>1:
            board.back.append(b)
    #~ check_hint_obedience(board,now)
    return now,bump,allcovered,movebacktrack,movedata,next_dvs,thissol,glob_change

def get_alleys(board,origdv,endpos):
    """verify current alleys; update with any newly created ones.  if over the limit
    return the last one.  otherwise just modify board"""
    illegalcount=0
    if board.air:
        illegalcount+=1
    if board.alley:
        illegalcount+=1
        if not isalley(board,board.alley):
            board.alley=None
            illegalcount-=1
        if board.air and (not board.air.orig_allsqs.isdisjoint(set([board.alley])) or not set(board.orig_alleytunnel).isdisjoint(set([board.alley]))):
            board.alley=None
            illegalcount-=1
    if illegalcount>1:
        if illegalcount>1:
            #~ board.counts['alley']['bt']+=1
            save_backtrack(board,text='weird_extraair')
            return illegalcount
    tocheck=[board.sawr,board.sawl,]
    if board.back:
        tocheck.append([[n] for n in board.back])
    if len(board.vergr)>1:tocheck.append([[board.vergr[0]]])
    if len(board.vergl)>1:tocheck.append([[board.vergl[0]]])
    for side in tocheck:
        for section in side:
            if not section:continue
            for s in section:
                if not s:
                    continue
                if isalley(board,s):
                    if s==board.alley:
                        continue
                    if board.air and s in board.air.orig_allsqs:
                        board.air=None
                        #switch the room to an alley.
                    else:
                        #a genuine new illegal
                        #or it may just be an extension of an ilroom!  hole fuck!
                        if board.air and board.air.kind=='merge' and merge_alley_into_room(board, s, board.air):
                            #~ print 'successfully merged!'
                            #alley no longer exists, it is part of ilroom.
                            pass
                        else:
                            illegalcount+=1
                        if illegalcount>1:
                            break
                    board.alley=s
            if illegalcount>1:
                break
        if illegalcount>1:
            break
    if illegalcount>1:
        board.counts['alley']['bt']+=1
        save_backtrack(board,text='alleybt',extra_alley=s)
        return illegalcount
    if board.alley:
        board.counts['alley']['nobt']+=1
        board.alleytunnel,board.alleytunnelends=get_tunnelsqs_ends(board.rows,board.alley)
    if board.alley and board.air and (board.alley in board.air.orig_allsqs):
        if config.monitor_active:
            #~ print 'removing illegal cause it had an alley in it!'
            pdb.set_trace()
        board.air=None

def rm_is_solved(rows,rm):
    for sq in rm.orig_allsqs:
        if isopen(rows,sq):
            return False
    return True

def mark_solved(board,covered,endpos):
    """if a room is cleanly solved, then any solution starting inside it could also have started from outside it or one of its gatesqs.
    does this apply to optrooms too!?  yes!  there is no requirement that a clean solved opt / req room be started interior!
    #how about pararooms???? no, it's ok too.  at least allow the gatesqs!
    """
    if not config.mark_solved:
        return
    if not config.one_sol:
        return
        #don't do this when you are getting all sols, cause it WILL miss some.
    donehashids=set()
    badstarts=set()
    badtunnels=set()
    inf_rooms_hash=set()
    inf_rooms=[]
    for c in covered:
        relrooms=board.pos2rooms[c]
        for kind,rmlist in relrooms.items():
            for rm in rmlist:
                if rm.hashid not in inf_rooms_hash:
                    inf_rooms.append(rm)
                    inf_rooms_hash.add(rm.hashid)

    badstart_positions=set()
    for rm in inf_rooms:
        if board.start[0] in rm.orig_allsqs:
            continue
        if endpos in rm.orig_allsqs:
            continue
        if rm.eversolved:
            continue
        res=rm_is_solved(board.rows,rm)
        if res:
            rm.eversolved=True
            badstart_positions.update(rm.orig_sqs)
            #~ if config.monitor_start and config.monitored_start[0] in badstart_positions:
            board.ever_covered.update(rm.orig_sqs)
            #also, if we have a tunnel to another room which is also solved,
            #~ for gatesq in rm.orig_gatesqs:
                #~ tun,ends=get_tunnelsqs_ends(board.orig_rows,gatesq)
                #~ ok=True
                #~ for e in ends:
                    #~ if not e:
                        #~ continue
                    #~ endroom=board.sq2req[e]
                    #~ if endroom==rm:
                        #~ continue
                    #~ break
                #~ if rm_is_solved(board.rows,endroom):
                    #~ #we can kill intermediate squares!
                    #~ for tsq in tun:
                        #~ for n in [0,1,2,3]:
                            #~ would=(tsq,n)
                            #~ if would in board.starts:
                                #~ badtunnels.add(would)
                                #~ board.starts.remove(would)
                                #~ board.donestarts.add(would)

    #additional step - necesasry for level 78, anyway.
    #only remove a sq every room it is a gatesq of has been eversolved.
    not_finished=set()
    for pos in badstart_positions:
        bad=False
        rms=[]
        for th in board.pos2rooms[pos].values():
            rms.extend(th)
        for rm in rms:
            if pos in rm.orig_gatesqs:
                if not rm.eversolved:
                    bad=True
                    break
        if bad:
            not_finished.add(pos)
    badstart_positions=badstart_positions.difference(not_finished)
    board.starts=[s for s in board.starts if s[0] not in badstart_positions]
    #~ if config.monitor_start and config.monitored_start not in board.starts and config.monitored_start[0] in badstart_positions:
    #~ if len(badstart_positions):
        #~ print '\nremoved %d bad start positions ===> %d'%(len(badstart_positions),len(board.starts)),
    #~ if config.monitor_start:
        #~ if config.monitored_start in badstarts or config.monitored_start in badtunnels:
            #~ print 'have somehow removed monitored start.'
    board.badstart_positions_len+=len(badstart_positions)
    if board.badstart_positions_len>1000:
        board.badstart_positions_len=0
        #~ print 'saving donestarts from mark_solved.'
        modified_starts(board.levelnum,board.donestarts, board)

def pack(board):
    board.alleystore.append(board.alley)
    board.airstore.append(board.air)
    board.vergstore.append((board.vergr[:],board.vergl[:]))

def unpack(board):
    board.alley=board.alleystore.pop()
    board.glob=board.glob.difference(board.globstore.pop())
    #~ board.nowglob=board.glob.copy()
    oldil=board.air
    board.air=board.airstore.pop()
    if config.monitor_active:
        print 'POPPED. il stuff now:'
        board.si
        #~ if board.air!=oldil:
            #~ if board.air.sqs!=oldil.sqs or board.air.gates!=oldil.gates or (board.air.xoffset,board.air.xoffset) != (oldil.xoffset,oldil.yoffset):
                #probably not good... why not?
                #~ print 'UNPACK CHANGED ILLROOM!~'
    board.vergr,board.vergl=board.vergstore.pop()

def fork(board,origpos,origdv, onestep=False):
    #~ if board.levelnum=='16238247935' and origpos==(3,3) and not onestep:
        #~ import ipdb;ipdb.set_trace()
    board.depth+=1
    pack(board)
    lastdv=None
    if board.sol:lastdv=board.sol[-1]
    endpos,bump,covered,movebacktrack,movedata,next_dvs,thissol,allnewglob=multimove(board,origpos,origdv,lastdv,onestep=onestep)
    board.globstore.append(allnewglob)
    if board.depth%50==0:
        n=board.depth/50
    board.endpos=endpos
    if not covered<board.ever_covered:
        mark_solved(board,covered,endpos)
    if movebacktrack:
        save_backtrack(board,text='mv'+movedata)
    elif movedata==0:
        donestart(board,res=0,message='Done',onestep=onestep, thissol=board.sol)
        board.unset_many(covered)
        board.sol=board.sol[:-1*len(thissol)]
        return 0
    else:
        backtrack=get_alleys(board,origdv,endpos)
        if not backtrack:
            has_zero=False
            for dv in next_dvs:
                #~ if board.levelnum=='16238247935' and not onestep:import ipdb;ipdb.set_trace()
                forkres=fork(board,endpos,dv,onestep=onestep)
                if forkres==0:
                    has_zero=True
                    if config.one_sol or config.live:
                        board.unset_many(covered)
                        board.sol=board.sol[:-1*len(thissol)]
                        return 0
            if has_zero:
                board.unset_many(covered)
                board.sol=board.sol[:-1*len(thissol)]
                return 0
    board.unset_many(covered)
    if board.isopen(origpos):
        board.set(origpos)
    board.sol=board.sol[:-len(thissol)]
    unpack(board)
    board.depth-=1

def do_placement(board,dv,pos):
    """basic placement stuff?
    stuff keeps getting pushed into here...
    """
    for rlpos in board.restore_later_hints:
        board.global_hints[rlpos]=board.restore_later_hints[rlpos]
    #~ if config.disable_hints_in_starting_reqrm:
        #~ print 'restoring',len(board.restore_later_hints),
    for k,v in board.restore_later_hints.items():
        board.global_hints[k]=v
    if board.orig_alley:
        if pos==board.orig_alley:
            if board.extra_alley:
                board.alley=board.extra_alley
        else:
            board.alley=board.orig_alley
    for nei in orth(pos):
        if nei==add(pos, dv):
            continue
        if not board.isopen(nei):
            continue
        neinei=board.orig_open_open[nei][:]
        if pos in neinei:
            neinei.remove(pos)
        if len(neinei)==1:
            #~ print 'made starting alley.',
            if board.alley:
                #~ print 'two starting alleys.',
                return 1
            else:
                board.alley=nei
        if len(neinei)==0:
            #~ print 'split start.',
            return 1

    illegalcount=0
    if board.alley:
        illegalcount+=1
    board.air=None
    ils=[]
    if board.original_illegal_rooms:
        for il in board.original_illegal_rooms:
            if pos in il.orig_allsqs:
                continue
            #starting one space away from a pararoom's para can actually make that not para anymore - which means the room won't actually be illegal anymore.
            #so we should allow placement here without triggering illegal.
            if il.kind=='pararooms':
                skip=False
                for ilgsq in il.orig_gatesqs:
                    if dist(ilgsq,pos)==1:
                        #~ print 'SKIPPING!',
                        skip=True
                        break
                if skip:
                    continue
            ils.append(il)
        if ils:
            ils.sort(key=lambda x:len(x.orig_allsqs))
            board.air=copy.deepcopy(ils.pop(0))
            board.air.get_tunnelsqs(board)
            illegalcount+=1
            for il in ils:
                if not il.orig_allsqs.isdisjoint(board.air.orig_allsqs):
                    continue
                illegalcount+=1
                #~ print 'xxx',
                break

    #if we start in a reqroom with even number of solutions, then the remaining reqroom is illegal, no ifs ands or buts!
    #(there is probably sth true about this for pararooms too, but tricky


    #first, find the reqrm or the reqrm at end of tunnels.
    board.unset(pos)

    #this part is setting up an initial illegal room.  we can actually do quite a lot here.
    #if we start in a reqroom that has an even number of exits, and are facing outwards, then the stuff we leave behind is
    #going to be illegal.  we have to make sure it doesn't conflict with existing illegals though.
    reqrm=reqrm_at_end_of_tunnel(board, pos)

    #reqrms have only isolated, rgates.  so if we start in one or inner, definitely illegal.
    #there is always a reqrm.
    if reqrm and pos in reqrm.orig_gatesqs and add(pos, dv) in reqrm.orig_sqs:
        #if we are facing IN from a req gate, it may be ok.
        reqrm=None
    if reqrm and pos not in reqrm.orig_allsqs:
        #this is the case when we make reqroom from an alley, since the reqrm doesn't extend into the tunnel actually.
        reqrm=None
    if board.air and reqrm and not reqrm.orig_allsqs.isdisjoint(board.air.orig_allsqs):
        #if we have an untouched illegal room that is air, and start in a solved reqrm, but it intersects, cancel it.
        #rather than overwrite the existing air which would be a fuckup.
        reqrm=None
    if reqrm and board.orig_alley and board.orig_alley in reqrm.orig_allsqs:
        reqrm=None
    elif reqrm and board.orig_alley and not board.orig_alleytunnel.isdisjoint(reqrm.orig_allsqs):
        reqrm=None
    elif reqrm and board.extra_alley and board.extra_alley in reqrm.orig_allsqs:
        reqrm=None
    elif reqrm and board.extra_alley and not board.orig_extraalleytunnel.isdisjoint(reqrm.orig_allsqs):
        reqrm=None
    if reqrm and reqrm.gatesqs and len(reqrm.gatesqs)%2==0:
        if reqrm and board.air:
            #we have an untouched illegalroom, and we have are starting inside an even reqroom that doesn't overlap, so...
            #~ print 'cant start in even reqroom with il on board.',
            if config.do_target:
                import ipdb;ipdb.set_trace()
            return True
        #~ print 'start in even, remainder is il!',
        board.air=copy.deepcopy(reqrm)
        board.air.get_tunnelsqs(board)
    board.set(pos)
    for ii,il in enumerate(board.original_illegal_rooms):
        if il.contained_alley:
            if pos!=il.contained_alley:
                if board.alley:
                        #~ print 'weird double alley afer merge!'
                        return False
                else:
                        #~ print 'restore alley',
                        board.alley=il.contained_alley
    #~ if board.alley:
        #~ print 'alley:',str(board.alley!=None)[0],
    #~ print 'il:',str(board.air!=None)[0],
    if illegalcount>1:
        #~ print 'bad plcmnt.',
        save_backtrack(board=board,text='bad plcmnt')
        return illegalcount
    board.restore_later_hints={}
    #what does it mean for restoring hints when there is no reqroom?
    if reqrm and config.disable_hints_in_starting_reqrm:
        #reqrm does not exist when it is an alley AND the alley has been merged into an ilroom
        #but the hints will be killed there anyway
        for opos in reqrm.orig_allsqs:
            board.restore_later_hints[opos]=board.global_hints[opos]
            board.global_hints[opos]=board.orig_global_hints[opos]



def do_manual(rows=None,levelnum=None, onestep=False):
    levelst=time.time()
    levelnum=str(levelnum)
    #~ import simpleroom
    #~ simpleroom.g_allsols_cache={}
    #~ simpleroom.g_hassols_cache={}
    #~ simpleroom.kill_caches()
    #
    #this isn't actually necessary, but it's good cause you save ram.

    config.one_sol=0
    config.live=False
    config.levelnum=levelnum
    config.maxx,config.maxy=len(rows[0])-1,len(rows)-1

    if config.do_sol:
        sol=open('sols/%s.txt'%levelnum,'r').read()
        x=int(sol.split('((')[1].split(',')[0])
        y=int(sol.split(',')[1].split(')')[0])
        config.targetpos=x,y
        config.targetdv=int(sol.split(',')[2].split(')')[0])
        config.target=(config.targetpos, config.targetdv)
        config.monitored_start=(config.targetpos, config.targetdv)
    board=Board(config, rows=rows, levelnum=levelnum, onestep=onestep)
    board.allneighbors=get_allneighbors(config)
    board.boardst=levelst
    totst=len(board.starts)
    #~ print 'board starts is:',totst
    board.rows=[r[:] for r in board.orig_rows]
    has_solution=False
    origalleys=getorigalley(board)
    #~ if board.levelnum=='3489660927':
        #~ import ipdb;ipdb.set_trace()
    if len(origalleys)<=2:
        while board.starts:
            ii=len(board.starts)
            pos, dv=board.newstart()
            #~ print pos,dv
            #~ board.show()
            #~ if levelnum=='31336081391615' and pos==(4,1) and dv==2 and onestep:
                #~ import ipdb;ipdb.set_trace()
            #~ if levelnum=='3489660927' and pos==(4,1) and dv==2 and onestep:
                #~ import ipdb;ipdb.set_trace()
            #~ if levelnum=='3489660927':
                #~ import ipdb;ipdb.set_trace()
            if len(origalleys)==2 and pos not in origalleys:
                continue
            #~ print "%s: %03d-%03d %s %s / %s"%(levelnum,pos[0],pos[1],getd(dv),str(totst-ii),str(totst)),
            if not oob(config, pos) and not board.isopen(pos):
                import ipdb;ipdb.set_trace()
                board.show()
                sys.exit()
            board.set(pos)
            #~ if config.monitor_start and (pos,dv)==config.monitored_start:
                #~ import ipdb;ipdb.set_trace()
            #~ illegal_placement=do_placement(board,dv,pos)
            #~ if illegal_placement:
                #~ donestart(board,message='illegal placement')
                #~ board.unset(pos)
                #~ continue
            alley_backtrack=get_alleys(board,dv,pos)
            if alley_backtrack:
                #~ donestart(board,message='badalley')
                board.unset(pos)
                continue
            if board.isopen(add(pos,dv+1)) and not board.isopen(add(add(pos,dv+1),dv)):
                #for example  if you are moving upwards.  If right is open and upper right is open, add right.
                #only set up fake initial sometimes.
                board.sawr=[[add(pos,dv+1)]]
            else:
                board.sawr=[[]]
            if board.isopen(add(pos,dv-1)) and not board.isopen(add(add(pos,dv-1),dv)):
                board.sawl=[[add(pos,dv-1)]]
            else:
                board.sawl=[[]]
            if config.monitor_start and (pos,dv)==config.monitored_start:
                import ipdb;ipdb.set_trace()
            res=fork(board,pos,dv, onestep=onestep)
            #MAIN

            if res==0:
                board.solvetime=time.time()-board.boardst
                #~ donestart(board,res=res,message='DONE', onestep=onestep)
                has_solution=True
                res=dosolved(board)
                if config.one_sol or config.live:
                    doneboard(board)
                    board.unset(pos)
                    return res
            else:
                donestart(board,message='runout  ')

            board.unset(pos)
    doneboard(board)
    if has_solution:
        return True

def do_in_order():
    #~ print 'inorder',
    global boardhashes
    boardhashes=set()
    if config.live:
        while 1:
            res=do_levelnum()
            if not res:
                #not sure what this is all about now.
                pass
                #~ sys.exit()
            if config.one_level:
                break
            #~ reload(config)
            config.do_target=False
            config.save_backtracks_every=10000
            #don't continue doing target on the next level.....
            print ''
    elif config.levelnum=='test':
        #~ print 'doing TEST'
        #~ simpleroom.g_allsols_cache={}
        res=do_levelnum(config.levelnum)
    else:
        #this is stupid hack.
        try:
            int(config.levelnum)
            ipart=int(config.levelnum)
            cc=96
            char=''
        except:
            ipart=int(config.levelnum[:-1])
            cc=ord(config.levelnum[-1])
            char=chr(cc)
        first=1
        for n in range(ipart,10000):
            if first:
                first=0
            else:
                cc=96
                char=''
            levelnum='%04d%s'%(n,char)
            while os.path.exists('levels/%s.txt'%(levelnum)):
                ###this is necessary, for some dumb ass reason.  first problem is if you run from 20 -> 29, works if clear cache, fails on 29 if not.
                #~ print '\n','=='*50,'doing levelnum',levelnum
                res=do_levelnum(levelnum)
                if config.debug or config.do_target:
                    break
                if config.one_level:
                    return
                if config.profile:
                    return
                config.do_target=False
                config.abs_do_best_seen=0
                print ''
                cc+=1
                char=chr(cc)
                levelnum='%04d%s'%(n, char)
                if not os.path.exists('levels/%s.txt'%(levelnum)):
                    break

def main():
    #~ config.one_sol=False
    if 'nobump' in sys.argv:
        config.bump_prune=0
        sys.argv.remove('nobump')
    if 'direct' in sys.argv:config.check_all_sol_paths=0;sys.argv.remove('direct')
    if 'one' in sys.argv:
        config.one_level=1
        sys.argv.remove('one')
    if 'profile' in sys.argv:
        print 'profiling'
        sys.argv.remove('profile')
        config.profile=1
        config.one_level=True
        config.one_sol=True
        config.use_start_cache=0
        config.do_ipdb=0
        config.save_unsolved_counts=0
    if 'nohint' in sys.argv:
        print 'not checking hints.'
        sys.argv.remove('nohint')
        config.check_hints=0
    if 'savehint' in sys.argv:
        print 'saving every hint gten.'
        sys.argv.remove('savehint')
        config.save_hints_every=1
    if 'savebt' in sys.argv:
        print 'saving every bt.'
        sys.argv.remove('savebt')
        config.save_backtracks_every=1
        config.no_save_when_check_all_sol=0
    if 'promotion' in sys.argv:
        print 'monitoring promotion to illegal'
        sys.argv.remove('promotion')
        config.monitor_promotion=1
    if 'promote' in sys.argv:
        print 'monitoring promotion to illegal'
        sys.argv.remove('promote')
        config.monitor_promotion=1
    if 'allsols' in sys.argv:config.one_sol=0;sys.argv.remove('allsols');
    if len(sys.argv)>1:
        config.levelnum=sys.argv[1]
        #~ config.ZONE=1
        config.live=0
        config.submit=0
    if len(sys.argv)>2:
        config.do_target=1
        config.target=((int(sys.argv[2]),int(sys.argv[3])),int(sys.argv[4]),)
        #~ print 'doing target.',config.target
        config.save_backtracks_every=1
        config.monitor_start=1
        config.monitored_start=config.target
    for field in config.toshow_fields:
        print field,'=',getattr(config,field)
    if config.profile:
        print 'profiling'
        import cProfile
        cProfile.run("do_in_order()",sort=-1,filename="test_function.cprof")
        showstats()
    else:
        #~ print 'not profiling'
        if config.do_ipdb:
            pass
        else:
            import psyco
            psyco.profile()
            print 'psyco'

        #~ import psyco
        #~ psyco.profile()
        #~ print 'PSYCO'
        print 'levelnum:',config.levelnum
        do_in_order()





if __name__=="__main__":
    #~ main()
    rows=[[1,1,1,1],[1,0,0,1],[1,0,1,1],[1,1,1,1]]
    canval=123
    do_manual(rows=rows, levelnum=canval)
