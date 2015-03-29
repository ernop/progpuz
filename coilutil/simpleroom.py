import pprint,shutil,time,random,traceback,hashlib,traceback,os,copy
try:
    import cPickle
except:
    import pickle as cPickle
from split_utils import *
from admin import *
import config
from room import Room

#really, really need to check to see what the cache hits are actually like.

last_bigsave=0
g_allsols_cache={}
g_hassols_cache={}
g_hit,g_miss=1,1

def get_sqs_gates(rows,pos,method):
    if method=='flood':
        sqs=floodfill(rows,pos)
        gates=set()
    #~ elif method=='flowtooptgates':
        #~ sqs,gates=flow_to_gates(rows,pos)
    elif method=='optrooms':
        sqs,gates=flow_to_gates(rows,pos,envelop=True)
    #~ elif method=='reqrooms':
        #~ sqs,gates=flow_to_req_gates(rows,pos)
    elif method=='reqrooms':
        sqs,gates=flow_to_req_gates(rows,pos,envelop=True)
    elif method=='optrooms_at_end_of_tunnel':
        sqs,gates=optrooms_at_end_of_tunnel(rows,pos)
    elif method=='reqrooms_at_end_of_tunnel':
        sqs,gates=optrooms_at_end_of_tunnel(rows,pos)
    else:
        print 'unknown method %s'%method
        sys.exit()
    return sqs,gates

def optrooms_at_end_of_tunnel(rows,pos):
    tunnelsqs,ends=get_tunnelsqs_ends(rows,pos)
    sqs=set()
    if len(ends)!=2:
        #~ pdb.set_trace()
        sqs=set()
    gates=set()

    for e in list(ends):
        endroom=mkroom(rows,e,method='optrooms')
        sqs.update(endroom.orig_allsqs)
        sqs.update(endroom.orig_allsqs)
    sqs.update(tunnelsqs)
    gatesqs=set()
    for sq in sqs:
        gatesqs.update([nei for nei in orth(sq) if isopen(rows,nei) and nei not in sqs])
    changed=1
    while changed:
        changed=0
        for g in gatesqs:
            for g2 in gatesqs:
                if dist(g,g2)==1:
                    sqs.add(g)
                    sqs.add(g2)
                    more=row2roomsqs(rows,g)
                    sqs.update(more)
                    more=row2roomsqs(rows,g2)
                    sqs.update(more)
                    changed=1
        gatesqs=set()
        for sq in sqs:
            gatesqs.update([nei for nei in orth(sq) if isopen(rows,nei) and nei not in sqs])

    gates=set()
    for gatesq in gatesqs:
        outsqs=[n for n in orth(gatesq) if isopen(rows,n) and n not in sqs]
        gates.add((gatesq ,len(outsqs)))
    return sqs,gates

def merge_pararooms(rooms):
    """since the rooms should already include the full parazones around them, if there are any overlaps then merge,
    so it includes sqs of both if inter, gates of either if only in one.
    and if a sq is gate in one, sq in other, becomes sq.
    and sqs which are in ones sqs and not in the other.
    """

    if len(rooms)==2:
        sqs=set()
        gatesqs=set()
        gates=set()
        allsqs=set()
        aa=rooms[0]
        bb=rooms[1]
        allsqs.update(aa.orig_allsqs)
        allsqs.update(bb.orig_allsqs)
        for sq in allsqs:
            if sq in aa.orig_sqs or sq in bb.orig_sqs:
                #all sqs stay.
                sqs.add(sq)
            elif sq in aa.orig_gatesqs:
                #if it is a gate in the same way, it's a gate.  if it's not the same way (i.e. a merge across a 1 space wide parazone...  merge it in.)
                aa_near=[o for o in orth(sq) if o in aa.orig_sqs]
                bb_near=[o for o in orth(sq) if o in bb.orig_sqs]
                    #if it can see both, but in a different way.
                if aa_near and bb_near and sorted(aa_near)!=sorted(bb_near):
                    sqs.add(sq)
                else:
                    gatesqs.add(sq)
            elif sq in bb.orig_gatesqs:
                aa_near=[o for o in orth(sq) if o in aa.orig_sqs]
                bb_near=[o for o in orth(sq) if o in bb.orig_sqs]
                if aa_near and bb_near and sorted(aa_near)==sorted(bb_near):
                    sqs.add(sq)
                else:
                    gatesqs.add(sq)
        gates=set([(g,1) for g in gatesqs])
        room=Room(sqs=sqs, gates=gates, kind='pararooms')
        return room
    else:
        while len(rooms)>2:
            res=merge_pararooms([rooms[:2]])
            rooms=rooms[2:]
            rooms.append(res)
            #just keep merging to the first one?
        return merge_pararooms(rooms)

def get_merge_sqs(rows,rooms):
    """"""
    sqs=set()
    gates=set()
    for rm in rooms:
        sqs.update(rm.orig_sqs)
    gatesqs=set()
    for sq in sqs:
        gatesqs.update([nei for nei in orth(sq) if isopen(rows,nei) and nei not in sqs])
    gates=set()
    for gatesq in gatesqs:
        outsqs=[n for n in orth(gatesq) if isopen(rows,n) and n not in sqs]
        ns=len(outsqs)
        if ns==0:
            #alleys are req gates.
            ns=1
        gates.add((gatesq ,len(outsqs)))
    sqs,gates=fix_enveloped(rows,sqs,gates)
    return sqs,gates

def mkroom(rows,pos,head=None,levelnum=None,limit=None,method='minimal',extras=None):
    """make a room at a given spot; returns False if it's not possible to make one there.
    from the incoming rows & pos, prepares a local list of sqs and gates.  there should be no zeros or right/bottom edges in these.

    that can happen if the spot has no squares, or if it includes the head (current running position of the cursor)

    methods:
    has_ sol ==> bool
    all_sols (future)

    sqs, gatesqs MIGHT be messed up in solving; but gates are not touched.  recalc from that if necessary.
    """
    if method!='merge' and not isopen(rows,pos):
        print 'pos to make the room is not open!',pos
        return False
    if head is None:
        head=(-10,-10)

    if method=='merge':
        sqs,gates=get_merge_sqs(rows,extras['rooms'])
    else:
        sqs,gates=get_sqs_gates(rows,pos,method)
    for s in sqs:
        if head is None:
            break
        if dist(s,head)==1:
            return False
    for g in gates:
        if head is None:
            break
        if dist(g[0],head)==1:
            return False
    if not gates and not sqs:
        return False
    rm=Room(sqs, gates, kind=method, levelnum=levelnum)
    return rm

def arcpos(pos,dv):
    return add(pos,(dv+2)%4)

def follow(rm,pos,global_hints):
    startpos=pos
    entry_gate=None
    while 1:
        if pos not in global_hints or len(global_hints[pos])!=1:
            break
        nn=list(global_hints[pos])

        indv,outdv=nn[0]
        pos=add(pos,outdv)
        if pos in rm.orig_gatesqs:
            entry_gate=pos
    return pos,entry_gate

def prune_room_sols(rm,global_hints,board,debug=False):
    """
    based on the incoming global hints, prune room sols.  return the # of pruned sols

    #should NOT remove solutions which are identical except for order.  because, that can fuck up
    better prune sols cause it may detect a dependency on order, and if the right-order one is missing the sol
    will be totally killed.
    """
    bad_rmsols=[]
    if config.skip_prune_in_orig_illegal:
        for il in board.original_illegal_rooms:
            if not rm.orig_allsqs.isdisjoint(il.orig_allsqs):
                return 0
    for ii,s in enumerate(rm.all_sols):
        sol_ok=True
        for sg in s:
            #one start, path, etc. end
            start,indv,path,covered,end=sg
            covered=('IN',start,)+covered+('OUT',)
            global_start=rm.local2global(start)
            if start==end:
                #it's a declined optgate
                has_passby_hint=False
                if global_hints[global_start]:
                    for hint in global_hints[global_start]:
                        indv,outdv=hint
                        global_outpos=rm.local2global(arcpos(start,indv))
                        global_outpos2=rm.local2global(add(start,outdv))
                        if global_outpos not in rm.orig_sqs and global_outpos2 not in rm.orig_sqs:
                            has_passby_hint=True
                            break
                    if not has_passby_hint:
                        sol_ok=False
                        reason='had no passby hint.'
                        break
            else:
                for jj,pos in enumerate(covered):
                    if pos=='IN':
                        continue
                    if pos=='OUT':
                        continue
                    global_pos=rm.local2global(pos)
                    if not global_hints[global_pos]:
                        continue
                    indv=makevec2(covered[jj-1],covered[jj])
                    outdv=makevec2(covered[jj],covered[jj+1])
                    if indv=='IN':
                        indvs=[n for n in [0,1,2,3] if (n+2)%4!=outdv]
                        had_one=False
                        for i in indvs:
                            if (i,outdv) in global_hints[global_pos]:
                                had_one=True
                                break
                        if not had_one:
                            sol_ok=False
                            reason='indv was IN but there was no suitable outdv in global hints at %s'%str(global_pos)
                            break
                    elif outdv=='OUT':
                        outdvs=[n for n in [0,1,2,3] if (n+2)%4!=indv]
                        had_one=False
                        for o in outdvs:
                            if (indv,o) in global_hints[global_pos]:
                                had_one=True
                                break
                        if not had_one:
                            sol_ok=False
                            reason='outdv was OUT but ther was no global IN for %s'%str(global_pos)
                            break
                    else:
                        if (indv,outdv) not in global_hints[global_pos]:
                            sol_ok=False
                            reason='normal case;',(indv,outdv),'was not in',global_hints[global_pos]
                            break
        if not sol_ok:
            #~ print 'badsol.',reason
            bad_rmsols.append(s)
    if bad_rmsols:
        if len(bad_rmsols)==len(rm.all_sols):
            print 'would remove all, so just promote me!'
            board.promote_to_illegal(list(rm.orig_allsqs)[0])
            return False
        for s in bad_rmsols:
            rm.remove_sol(s)
    return len(bad_rmsols)

def better_prune_sols(rm,global_hints,board):
    """
    identify entry&exit combinations of a room which are actually the same path (using global hints)
    so say room has A,B as entrances, C,D as exits.  if you find that D exit must return to the same room as A, then we know that D must happen before A
    so solutions which have A before D can't be valid - only solutions left are B -> D, A -> C ones.

    IT's coming from inside this roOM!!!!
    """
    badsols=set()
    out_in=set()
    #put something here when we discover than an entry actually must come after a given parent.  so sols that have entry, parent in order
    if len(rm.gatesqs)==2:
        return 0
    if board.orig_alley and board.orig_alley in rm.orig_allsqs:
        return 0
    if board.extra_alley and board.extra_alley in rm.orig_allsqs:
        return 0
    for gsq in rm.gatesqs:
        global_gsq=rm.local2global(gsq)
        if len(global_hints[global_gsq])!=1:
            continue
        #we have exactly one global hint here.
        indv,outdv=list(global_hints[global_gsq])[0]
        #we are looking for entry gates!
        if add(global_gsq,indv+2) in rm.orig_allsqs:
            #came from this room.
            continue
        if add(global_gsq,outdv) not in rm.orig_allsqs:
            #if the way out is in the room
            continue
        got=0
        for pre_outdv in [0,1,2,3]:
            nei=add(global_gsq,pre_outdv)
            if nei in rm.orig_sqs:
                continue
            if not board.isopen(nei):
                continue
            #so we have found one whose parent is out of this room.
            #~ if rm.hashid=='822f107aeea4d8490db65a1ae725c6caX023X012':# and gsq==(3,5):
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            parent_pos=follow_reverse(board,global_gsq,pre_outdv,rm,global_gsq)
            if parent_pos==global_gsq:
                continue
            if parent_pos in rm.orig_gatesqs:
                outsq, insq=rm.global2local(parent_pos), gsq
                out_in.add((outsq, insq, ))
                #~ if rm.hashid=='822f107aeea4d8490db65a1ae725c6caX023X012':
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                break
                #both are local now.
    if out_in:
        for outsq, insq in out_in:
            #so we know there is a path going out outsq and coming back to insq.
            for ii,sol in enumerate(rm.all_sols):
                for sa in sol:
                    start,firstdv,path,covered,end=sa
                    #if the path at this gate is determined outwards, try the next one.
                    if start==insq:
                        #if we start on a square without having seen the outsq that got us there...
                        #~ try:
                        badsols.add(sol)
                        break
                    if end==outsq:
                        #sol is good - got to the parent first.
                        #actually we can also say that after reaching this, the next entry MUST be the insq! (because
                        #the path can't even run by even optgates in the meantime?  not implemented, anyway.
                        break
                    if start==outsq:
                        badsols.add(sol)
                        #this room has a 2-way gate.  so while we know that you must exit outsq before entering
                        #insq, what do we know about this?  somehow it was not already removed.
                        #~ print 'how the hell are you starting on a spot that must exit?'
    if badsols:
        if len(badsols)==len(rm.all_sols):
            if 2*len(out_in)==len(rm.gatesqs):
                #like level 5i, you have a central room that just has finished loops into the other rooms.
                #don't remove anything.
                badsols=set()
            else:
                board.promote_to_illegal(list(rm.orig_allsqs)[0])
                return False
                print 'removed all! sols from a room. fuck.'
        for s in badsols:
            rm.remove_sol(s)
        #~ rm.modify_hints_based_on_allsols()

    return len(badsols)

def bump_prune_sols(board):
    """"""
    total=0
    for kind in board.roomkinds:
        for rm in getattr(board,kind, []):
            #~ print 'doing',rm.hashid#,len(rm.all_sols)
            if board.bumps:
                for b in board.bumps:
                    #~ print 'bumps: %d'%len(board.bumps),b,rm.hashid
                    #~ if b==((68, 39), (76, 38)):
                        #~ import ipdb;ipdb.set_trace();print 'ipdb!'((68, 39), (76, 38))
                    badsols=[]
                    lastpath=board.forced_paths[b[0]]
                    firstpath=board.forced_paths[b[1]]
                    #for our solutions, if any of them overlap lastpath before firstpath, they must be bad!
                    for sol in rm.all_sols:
                        #~ print sol
                        has_seen_lastpath=0
                        for sa in sol:
                            #the only problem is when the sol has lastpath and firstpath, and you see lastpath first!
                            #just seeing lastpath first without ever seeing firstpath is not a problem!
                            start, _, _, covered, _=sa
                            do_break=False
                            covered=(start,)+covered
                            for c in covered:
                                if rm.local2global(c) in firstpath:
                                    if has_seen_lastpath:
                                        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                                        badsols.append(sol)
                                    do_break=True
                                    break
                            if do_break:
                                break
                            ok=True
                            for c in covered:
                                if rm.local2global(c) in lastpath:
                                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                                    #~ badsols.append(sol)
                                    has_seen_lastpath=1
                                    break
                                    #have seen lastpath so if we later see firstpath, kill it.
                    if badsols:
                        #~ print 'badsols %s rm.all_sols %d'%(len(badsols),len(rm.all_sols))
                        #~ import ipdb;ipdb.set_trace()
                        if len(badsols)==len(rm.all_sols):
                            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                            print 'bump promote!?'
                            board.promote_to_illegal(list(rm.orig_allsqs)[0])
                            return False
                        total+=len(badsols)
                        for bs in badsols:
                            rm.remove_sol(bs)
            return total

def follow_hint_in_room(global_pos, rm):
    """for a given room, find out where it is predicted to end up.
    returns a list of global positions. - this is just naive, requires absolute existence of hints
    """
    sq=self.global2local(global_pos)
    positions=[sq]
    now=sq
    hints=self.hints[sq]
    while len(hints)==1:
        now=add(now,hints[0][1])
        hints=self.hints[now]
        positions.append(now)
    return positions

def follow_hints_in_rooms(global_pos, rms):
    """given a collection of rooms, find out if they all predict that the path ends up in a certain spot.
    this can be weird - we can actually take the best result out of all rooms
   - cause ones without good hints will just give up on him.

    """
    #~ for rm in rms:
        #~ assert global_pos in rm.orig_allsqs
    allpositions=[]
    for rm in rms:
        positions=follow_hint_in_room(global_pos,rm)
        allpositions.append(positions)
    return allpositions

def follow_reverse(board,global_pos,outdv,origrm,origpos,depth=None):
    """
    follow back, until I hit this room or die.

    this is follow hints back, plus the additional step - even if we run out of hints, if the entrance to the room we are in
    can only end up at one exit, that's as good as a hint - so jump there. (not written yet...)

    follow back to a room that doesn't haev a definite hint - but keep going!
    sometimes a parent room will have multiple options, but they all will connect the same gates (or just this one to one unique source)

    so follow back til you run out, then look at the remaining sols of the room you got to and if all the exits to where you got to came
    from teh same source, continue following that one parent.

    FE you are in room A.  parent room is B.  connected by gate G.  gate g has multiple solutions, but from B they all go out.  in a, they are in/out.
    #so we can conclude that it should actually be an B->A gate, and fix A's solutions accordingly.
    """

    if not depth:
        depth=0
    if global_pos!=origpos and global_pos in origrm.orig_gatesqs:
        #success!
        return global_pos
    if board.orig_alley and global_pos in board.orig_alleytunnel:
        return global_pos
    if board.extra_alley and global_pos in board.orig_extraalleytunnel:
        return global_pos
    gotroom=False
    wdepth=0
    rm=None
    #we are looking for the place we are bound to end up, according to hints.  we can be starting anywhere...
    moved=True
    done=False
    now=global_pos
    ii=0
    while moved:
        ii+=1
        if ii>10000:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            print 'FAAAR back.1'
            break
            #~ if global_pos==now:
                #~ break
        moved=False
        if now!=origpos and now in origrm.orig_gatesqs:
            #always break when hitting an original gsq, unless it is passby
            break
        while len(board.global_hints[now])==1:
            ii+=1
            if ii>10000:
                print 'FAAAR back. 2'
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                break
                if global_pos==now:
                    break
            moved=True
            gb=list(board.global_hints[now])[0]
            now=add(now, gb[0]+2)
            if now in origrm.orig_gatesqs:
                #made it back to an original gsq.  however, if we are not going back into the room then it's not valid anyway.
                for h in board.global_hints[now]:
                    if add(now,h[0]+2) in origrm.orig_sqs:
                        done=True
                        break
                        #only break if the next way brings us back.

                if done:
                    break
                    #~ print 'made it back to a gate, but didnt actually go into the room.  so keep going.'
            #use global hints until you run out.
        if not done:
            rms=board.pos2allrooms(now)
            for rm in rms:
                #~ print 'now is',now
                now2, method=reverse_in_room(now, rm, origrm)
                if now2!=now:
                    #~ print 'reversed in room with method %s'%method
                    moved=True
                    now=now2
                    break
                if now in origrm.orig_gatesqs:
                    #really, still i need to check if the next way actually brings is into the room
                    #(failure would be if it just brings us to an optgate of the room; that is not invalid.)
                    break
        if now in origrm.orig_gatesqs or done:
            break
    #(we may have backed up too far)
    #~ print 'now is in rm.origsqs %s'%(now in origrm.orig_sqs)
    #~ print 'now is in rm.orig_gatesqs %s'%(now in origrm.orig_gatesqs)
    return now

def reverse_in_room(now, rm, origrm=None):
    """we find ourself in a room with many exits.  can we tell which one we came from?"""
    pos=now
    moved=False
    ii=0
    #~ if pos not in rm.orig_allsqs:
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
    while pos in rm._global_hints and len(rm._global_hints[pos])==1:
        if origrm and pos in origrm.orig_gatesqs:
            break
        if pos in rm.orig_gatesqs:
            break
            #this is because sometimes rooms don't have 'IN' or 'OUT' as markers now.  so we may back out too far.
        ii+=1
        if ii>10000:
            print 'FAAAR3 back.'
            #~ import ipdb;ipdb.set_trace()
            break
        moved=True
        hc=list(rm._global_hints[pos])
        if hc[0][0]=='IN' or hc[0][0]=='OUT':
            break
        else:
            pos=add(pos, hc[0][0]+2)
    if pos in rm.orig_gatesqs:
        return pos,'returned to self gatesqs'
    if origrm and pos in origrm.orig_gatesqs:
        return pos,'hit origrm gatesqs.'
    if config.advanced_reverse_in_room:
        sq=rm.global2local(pos)
        crossed_paths=[]
        #paths
        if rm.all_sols and rm.all_sols!='timeout':
            for sol in rm.all_sols:
                got=False
                for sa in sol:
                    #~
                    start,_,_,covered,end=sa
                    if sq in covered:
                        #~ c2=covered[:]
                        c2=(start,)+covered
                        crossed_paths.append(c2)
                        #print 'in covered way'
                        got=True
                        break
                        #hints didn't take us to an exit.  now use the smart way.
                #~ if not got:
                    #~ assert False
                #ever sol crosses the spot once.  we have the paths.
        res='normal'
        trace_back_to_gate=set()
        #~ if rm.hashid=='d6f52b6517368af4ebc5ecb4ab5fd312X018X009':
            #~ if origrm.hashid=='822f107aeea4d8490db65a1ae725c6caX023X012':
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        for cp in crossed_paths:
            got=0
            seen_me=0
            for csq in reversed(cp):
                #~ print csq, rm.local2global(csq),origrm.orig_gatesqs

                if rm.local2global(csq)==pos:
                    #~ if rm.hashid=='d6f52b6517368af4ebc5ecb4ab5fd312X018X009':
                        #~ if origrm.hashid=='822f107aeea4d8490db65a1ae725c6caX023X012':
                            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                    seen_me=1
                    continue
                if not seen_me:
                    continue
                #~ print rm.local2global(csq),origrm.orig_gatesqs
                if rm.local2global(csq) in origrm.orig_gatesqs:
                    trace_back_to_gate.add(csq)
                    got=True
                    break
            if not got:
                trace_back_to_gate.add(cp[0])
                #if we didn't cross any origrm gatesqs on the way back
                #just add the origin of this path.
        if len(trace_back_to_gate)==1:
            cf=rm.local2global(list(trace_back_to_gate)[0])
            if cf!=pos:
                pos=cf
                res='ended up1'
                #~ if pos not in rm.orig_allsqs:
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        #~ ###new code to see if all entrances from here match.  also have to check that this is even a valid real entry here.
    return pos,'normal'

#~ def follow_reverse_to_entering_gate(board,global_pos,global_hints):
    #~ """from global_pos, follow global & room hints backwards until it hits a gate of a room."""
    #~ pos=global_pos
    #~ ii=0
    #~ lastdv=None

            #~ sq=rm.global2global(now)
            #~ while len(
        #~ #if pos in board.gatesq2opt and pos != global_pos:
        #~ if pos != global_pos and relrms:
            #~ relrm=relrms[0]
            #~ if len(board.global_hints[pos])==1:
                #~ indv,outdv=list(board.global_hints[pos])[0]
                #~ if add(pos,indv+2) in relrm.orig_sqs:
                    #~ return pos,indv+2
        #~ if pos not in global_hints or len(global_hints[pos])!=1:
            #~ break
        #~ indv,outdv=list(global_hints[pos])[0]
        #~ #back up one.
        #~ pos=add(pos,indv+2)
        #~ lastdv=(indv+2)%4
        #~ if pos==global_pos:
            #~ assert False
    #~ return pos,lastdv

def follow_reverse_by_hints(global_pos,global_hints):
    pos=global_pos
    ii=0
    while 1:
        if pos not in global_hints or len(global_hints[pos])!=1:
            break
        indv,outdv=list(global_hints[pos])[0]
        #back up one.
        pos=add(pos,indv+2)
        if pos==global_pos:
            #~ assert False
            return pos
    return pos

def make_pararooms(board):
    """do a flow to _envelop,
    then split the big rooms on parallels.
    true parallels are definitely required entries!
    """
    st=time.time()
    pararooms=[]
    done=set()
    fakerows=[r[:] for r in board.rows]
    for pos in board.parasqs:
        fakerows[pos[1]][pos[0]]=1
        #set up parasqs like they are just walls.

    for pos in board.deeptunnels:
        #~ if fakerows[pos[1]][pos[0]]==0:
            #we should already have all these in.
        fakerows[pos[1]][pos[0]]=1

    #don't flow through deeptunnels either.
    #later on, also don't flow through spots that have just one hint!
    for pos in board.orig_open:
        if pos in board.parasqs:
            continue
        if pos in done:
            continue
        flow=floodfill(fakerows,pos)

        #now add back in the parasqs as forced entries
        #and add back in the deeptunnels too.
        room_done=set()
        gates=set()
        gatesqs=set()
        newflow=set()
        #expanding flow to see double-touched gatesqs.
        #and, figure out the gatesqs!
        #~ board.show(flow)
        while 1:
            for sq in flow:
                #newflow will contain controlled parazones - add them and start over.
                if newflow:break
                if sq in room_done:
                    continue
                room_done.add(sq)
                for dv in range(4):
                    nei=add(sq,dv)
                    if nei in flow:
                        continue
                    if nei in board.parasqs:
                        if nei in gatesqs:
                            newflow.add(nei)
                            gatesqs.remove(nei)
                            gates.remove((nei, 1))
                            #if you hit the thing the first time, add to gate. if hit the zone again, remove from gatse and add to flow.
                        else:
                            gates.add((nei, 1))
                            gatesqs.add(nei)
                    elif nei in board.deeptunnels:
                        if nei not in board.parasqs:
                        #~ if nei in gatesqs:
                            newflow.add(nei)
                            #~ gatesqs.remove(nei)
                            #~ gates.remove((nei,1))
                            #~ break
                        #~ gates.add((nei, 1))
                        #~ gatesqs.add(nei)
                    else:
                        if board.isopen(nei):
                        #just another type of gate!
                            gatesqs.add(nei)
                            gates.add((nei,1))
            if newflow:
                flow.update(newflow)
                newflow=set()
            else:
                break
        #also, if there is a completely internal parazone, merge it.
        checked_gsqs=set()
        sq2outside={}#will be used later to decide which ones to merge into the flow and which to leave as gsqs.
        for gsq in gatesqs:
            if gsq in checked_gsqs:
                continue
            has_outside=False
            to_check=set([gsq])
            this_gsq_set=set()
            while to_check:
                th=to_check.pop()
                if th not in sq2outside:
                    sq2outside[th]=False
                if th in this_gsq_set:
                    continue
                this_gsq_set.add(th)
                neis=orth(th)
                for nei in neis:
                    if nei in flow:
                        continue
                    if nei in gatesqs:
                        to_check.add(nei)
                        continue
                    if nei in board.parasqs:
                        to_check.add(nei)
                        continue
                    if board.oob(nei):
                        continue
                    if not board.isopen(nei):
                        continue
                    has_outside=True
                    sq2outside[th]=True
            checked_gsqs.update(this_gsq_set)
            for gsq in this_gsq_set:
                if sq2outside[gsq]:
                    gates.add((gsq,1))
                else:
                    flow.add(gsq)
                    if (gsq,1) in gates:
                        gates.remove((gsq,1))
        #need to reset this.
        done.update(flow)
        sqs=flow
        rm=Room(sqs, gates, kind='pararooms', levelnum=board.levelnum)
        pararooms.append(rm)
    #~ print 'made %d pararooms in %0.4f'%(len(pararooms),time.time()-st)
    return pararooms

NONE=1
OUT=2
IN=3
OUTNONE=4
INNONE=5
INOUT=6
ANY=7
num2res=['error','NONE','OUT','IN','OUTNONE','INNONE','INOUT','ANY']
