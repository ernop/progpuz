##an alley is just a small illegalroom........?

import cPickle,os,types,pprint

from split_utils import *
from simpleroom import *
from admin import *

class Board:
    def __init__(self,config,rows=None,levelnum='',setup=True, onestep=False):
        self.levelnum=levelnum
        self.setup=setup
        self.onestep=onestep
        self.__dict__.update(config.__dict__)
        self.config=config
        self.rows=rows
        self.reset()
        self.setup_origalleys()
        self.roomkinds=['optrooms','pararooms','reqrooms',]#'ohintrooms','rhintrooms','phintrooms',]
        #~ self.roomkinds.remove('pararooms')
        #~ self.roomkinds=['reqrooms',]#'ohintrooms','rhintrooms','phintrooms',]
        #~ self.optrooms=divide_rows_into_rooms(self.rows,'optrooms', levelnum=self.levelnum)
        #~ self.reqrooms=divide_rows_into_rooms(self.rows,'reqrooms', levelnum=self.levelnum)
        #_envelop
        #~ self.parasqs=getparasqs(self)
        #~ self.pararooms=make_pararooms(self)
        self.changecount=1
        #~ self.mkpos2rooms()
        #~ while 1:
            #~ changed=self.fix_enveloped_pararooms()
            #~ if not changed:break
            #~ print 'merged %d pararooms now there are %d'%(changed, len(self.pararooms))
        self.mkpos2rooms()
        boardinit(self ,levelnum)
        self.orig_global_hints=self.get_orig_global_hints()
        self.global_hints=self.orig_global_hints.copy()
        self.setup_counts()
        self.bumps=[]
        self.loaded_hints=0
        if config.check_hints:
            if config.load_hints:
                hint_fn='hintpickles/%s-hints.pickle'%self.levelnum
                res=general_load_pickle(hint_fn)
                if res:
                    self.global_hints=res['hints']
                    self.original_illegal_rooms=res['oir']
                    #~ import ipdb;ipdb.set_trace();print 'in ipdb.'
                    #~ print 'loaded',len(self.global_hints),'il:',len(self.original_illegal_rooms)
                    #~ import time
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                    #~ time.sleep(2)
                    self.loaded_hints=1
            if not self.loaded_hints:
                self.hint_solve()
            if config.load_hints and not self.loaded_hints:
                hint_fn='hintpickles/%s-hints.pickle'%self.levelnum
                res=general_save_pickle(hint_fn, {'hints':self.global_hints, 'oir':self.original_illegal_rooms})
        #~ save_sq_hintcounts(self)#image
        #~ self.original_illegal_rooms=[il for il in self.original_illegal_rooms if il.orig_gatesqs]
        #~ self.merge_alleys_into_illegals()
        #bumps is a list of [[astart, aend],[bstart,bend]] where all the astuff has to happen before the bstuff
        #due to bump interactions between the two paths.
        #~ self.find_bumps()
        #~ save_rm_solcounts(self)#image
        #it's done automatically after save all rooms, now.
        #deals with the list of illegal rooms - the logic about combining / intersecting them, etc.
        #now we should have self.illegalrooms with rooms, with metadata.
        if config.monitor_start and config.monitored_start not in self.starts:
            sys.exit()
        #~ self.prune_starts_which_are_inside_solved_rooms()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        #~ self.remove_superior_illegals()
        #~ self.save_illegalroom_images()
        #~ self.setup_important_starts()
        #~ self.remove_impossible_starts()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        #~ self.setup_timeout_starts()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        self.setup_origalleys()
        #~ self.merge_alleys_into_illegals()
        #~ self.check_hint_sanity()

    def check_hint_sanity(self):
        il_allsqs=set()
        for il in self.original_illegal_rooms:
            il_allsqs.update(il.orig_allsqs)
        il_allsqs.update(self.orig_alleytunnel)
        il_allsqs.update(self.orig_extraalleytunnel)
        for kind in self.roomkinds:
            for rm in getattr(self, kind, []):
                if not rm.orig_allsqs.isdisjoint(il_allsqs):
                    continue
                if rm.all_sols and rm.all_sols!='timeout':
                    if len(rm.all_sols)==1:
                        for sq in rm.orig_sqs:
                            if len(self.global_hints[sq])!=1:
                                import ipdb;ipdb.set_trace();print 'ipdb!'
                                #~ print self.global_hints[sq]
                                #~ print 'bad sol length.'
                        #if a rm has only one sol, then the way in to the exsqs has to be all the same.

                        for gsq in rm.orig_gatesqs:
                            waysin=[gh[0] for gh in self.global_hints[gsq]]
                            waysin=list(set(waysin))
                            waysout=[gh[1] for gh in self.global_hints[gsq]]
                            waysout=list(set(waysout))
                            skippable=False
                            for sa in rm.all_sols[0]:
                                if sa[0]==rm.global2local(gsq) and sa[1]=='skip':
                                    wo2=[(dv+2)%4 for dv in waysout]
                                    if sorted(wo2)==sorted(waysin):
                                        #~ print 'skippable'
                                        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                                        skippable=True
                            if skippable:
                                continue
                            if len(waysout)>1 and len(waysin)>1:
                                import ipdb;ipdb.set_trace();print 'ipdb!'
                                #~ print 'bad ways in.'

    def find_bumps(self):
        """bumps are when a determine path hits another determined path.  might be useful for determining
        order & precendence

        also if a<-b and b<-c then a<-c!  not tested.
        """
        #~ print 'find bumps.'
        if not config.bump_prune:
            return
        forced_paths={}
        #forced_paths is a dict of starting pos to list of all pos til last determined pos
        done=set()
        for pos in self.global_hints:
            if pos in done:
                continue
            done.add(pos)
            fp=get_ordered_forced_path(pos, self.global_hints)
            if not fp:
                continue
            done.update(fp)
            forced_paths[fp[0]]=fp
        #bumps is a dict of pathhead -> list of other pathheads it bumps into!
        bumps={}
        self.forced_paths=forced_paths
        for start, fp in forced_paths.items():
            bumps[start]=[]
            for n in range(1,len(fp)):
                thispos=fp[n]
                lastpos=fp[n-1]
                prev_dv=makevec(lastpos, thispos)
                would=add(thispos, prev_dv)
                if n==len(fp)-1 or would==fp[n+1]:
                    continue
                    #we didn't change directions, or we are done.
                if self.rows[would[1]][would[0]]:
                #normal bump
                    continue
                if len(self.global_hints[would])!=1:
                    #would hit a pos that is not determined yet, so skip.
                    continue
                #bumped into the path at would!
                #~ import ipdb;ipdb.set_trace();print 'ipd  b!'
                otherhead=find_pos_in_dict_to_list(would, forced_paths)
                if otherhead==start:
                    continue
                    #dont both recording self bumps.
                self.actual_bumps.add(thispos)
                bumps[start].append(otherhead)
        special_dict={}
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        a2bbumps=[]
        for r,g in bumps.items():
            if not g:
                continue
            #~ special_dict[k]='green'
            #~ for ohead in v:
                #~ special_dict[ohead]='red'
            #~ fname='bumps%s%s'%(str(k),str(v))
            #~ pshow(overwrite=True,rows=self.rows,special_dict=special_dict,worktype='%s'%self.levelnum,fname=fname)
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'

            a2bbumps.append((r,g[0]))
            red=[r, forced_paths[r][-1]]
            green=[g[0], forced_paths[g[0]][-1]]
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            if config.save_bumps:
                save_global_hints(self, red=red, green=green,extra_text='bump')
        #first do green, then do red!  green must come before red!
        transbumps=[]
        first=1
        got=1
        while got:
            #~ first=0
            #~ print 'got %d trnsbmp'%got
            #~ if not first:
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            first=0
            got=0
            for ii,bump in enumerate(a2bbumps):
                r,g=bump
                for jj,obump in enumerate(a2bbumps):
                    #~ print ii,jj
                    if bump==obump:continue
                    sr,sg=obump
                    if r==sg:
                        newbump=(sr,g,)
                        if newbump not in transbumps and newbump not in a2bbumps:
                            transbumps.append(newbump)
                            got+=1
                            if config.save_trans_bumps:
                                green=[g, forced_paths[g][-1]]
                                red=[r, forced_paths[r][-1]]
                                blue=[sr, forced_paths[sr][-1]]
                                yellow=[]
                                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                                #green => red => blue ORDER
                                save_global_hints(self, red=red, green=green, blue=blue, yellow=yellow, extra_text='trans_bump', force=True)
            a2bbumps.extend(transbumps)
        self.bumps=a2bbumps
        if 0 and self.actual_bumps:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            save_global_hints(self, self.global_hints, yellow=self.actual_bumps, force=1, extra_text='%04drealbumps'%len(self.actual_bumps))


    def fix_enveloped_pararooms(self):
        """if there is a pararoom that only touches one other pararoom, let the other one take it over."""
        badrooms=[]
        newpararooms=[]
        changed=0
        for rm in self.pararooms:
            if rm.has_merged:
                continue
            rm.has_merged=1
            cansee=[]
            for gsq in rm.orig_gatesqs:
                other=self.pos2rooms[gsq].get('pararooms',[])
                for o in other:
                    if o not in cansee and o!=rm:
                        cansee.append(o)
            if len(cansee)==1:
                other=cansee[0]
                newother=copy.deepcopy(other)
                #~ print newother
                newother.orig_gatesqs=[gsq for gsq in other.orig_gatesqs if gsq not in rm.orig_allsqs]
                newother.orig_gates=[g for g in other.orig_gates if g[0] not in rm.orig_allsqs]
                newother.add_poss(rm.orig_allsqs)
                newother.product_of_pararoom_merging=1
                newpararooms.append(newother)
                badrooms.append(rm)
                badrooms.append(other)
                changed+=1
        for rm in badrooms:
            #~ rm.has_merged=1
            pass
            #~ self.pararooms.remove(rm)
        self.pararooms.extend(newpararooms)
        return changed

    def hint_solve(self):
        self.passed_through_once=0
        lastchangecount=0
        ii=0
        #~ print '\n','='*100,'Starting!'
        self.changed_hints=None
        self.just_promoted_to_illegal=0
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        while self.changecount>lastchangecount or self.just_promoted_to_illegal:
            #~ if self.just_promoted_to_illegal==1:
                #~ print '='*50,'redoing it cause promoted to illegal.'
            self.runno=ii
            if ii>0:
                self.changed_hints=set()
                done=set()
                if self.just_promoted_to_illegal:
                    self.changed_hints.update(self.global_hints.keys())
                else:
                    for k,v in self.global_hints.items():
                        if k in done:
                            continue
                        if self.prior_hints[k]!=v:
                            self.changed_hints.add(k)
                            forced_path=get_forced_path(k, self.global_hints)
                            done.update(forced_path)
                            self.changed_hints.update(forced_path)
                        #if we find a spot that's changed, get the whole forced path

                #~ print '%d changed hints'%len(self.changed_hints)
            #~ print 'copy...',
            self.prior_hints=self.global_hints.copy()
            #~ print 'done'

            ii+=1
            s=''
            #~ print '\n','='*100,ii,s
            lastchangecount=self.changecount
            solved_one=self.solve_all_rooms()
            self.just_promoted_to_illegal=0
            if config.check_hints:
                if solved_one or self.just_promoted_to_illegal:
                    #~ print 'mgh'
                    self.find_bumps()
                    self.make_global_hints(ii)
                    #~ self.save_illegalroom_images()
                #~ else:
                    #~ print 'not solve one., skipping hints.'

            #~ if self.final and lastchangecount!=self.changecount:
            #~ if lastchangecount+500>self.changecount and not self.final:

        #~ print '\n','='*100,'done %d loops.'%ii
        save_global_hints(self,self.global_hints,'DONE-loop%02d-%04d'%(ii,self.changecount),force=True)

    def solve_all_rooms(self):
        source='solve-all'
        solved_one=False
        import simpleroom
        for kind in self.roomkinds:
            #~ print '\n'+kind,
            kc=kind[0]
            rmlist=getattr(self,kind,[])
            rmlist.sort(key=lambda x:(len(x.gatesqs),len(x.sqs)))
            consecutive=0
            for ii,rm in enumerate(rmlist):
                changed_sqs=[]
                if self.runno>0:
                    changed_sqs=rm.orig_allsqs.intersection(self.changed_hints)
                    if not changed_sqs:
                    #~ if rm.orig_allsqs.isdisjoint(self.changed_hints):
                        #~ print 's',
                        #this may kill some of the pruning... so we should include forced paths from
                        #hints in changed hints too... shouldn't be too much work.
                        continue
                if rm.all_sols is None or rm.all_sols=='timeout':
                    rm.adopt_global_hints(self)
                    #~ print "\n%s%d/%d"%(kc, ii,len(rmlist)),
                    has_cache=rm.key in simpleroom.g_allsols_cache
                    #~ print 'cache:%s'%str(has_cache)[0],
                    #~ print '%03d gsq %03d sq '%(len(rm.gatesqs),len(rm.sqs),),
                    rm.external_hints=self.global_hints
                    rm.all_sols=rm.get_all_sols(toplevel=True, source=source)
                    rm.external_hints={}
                    #~ if changed_sqs:
                        #~ print 'changed %d'%len(changed_sqs),
                    if consecutive>10:
                        source='solve-all-fast'
                    if rm.all_sols =='timeout':
                        #~ print 'timeout',
                        consecutive+=1
                    elif rm.all_sols:
                        consecutive=0
                        source='solve-all'
                        #~ print 'got %d'%len(rm.all_sols),
                        solved_one=1
                        bad=rm.modify_hints_based_on_allsols()
                        if bad:
                            res=self.promote_to_illegal(bad)
                            if res:return False
                if rm.all_sols:
                    res=rm.has_sol(toplevel=1)
                else:
                    res=False
                if res:
                    if res=='timeout':
                        self.timeout_sqs.update(set(rm.orig_allsqs))
                    #res can be real or timeout, either way not def. illegal
                    continue
                elif len(rm.orig_allsqs)==self.curopen:
                    continue
                else:
                    if rm not in self.original_illegal_rooms:
                        self.addorig(rm)
                        #~ print '\ngot illegal room',rm.hashid,'\n',rm,
        for kind in self.roomkinds:
            #this solves a bug!  where, two optrooms within an illegal room will come update
            #with an illegal hint, and if it is put into global already it will be bad.  so put it in
            #afterwards.  then we can more accurately detect when the illegal hint happens
            #and won't propagate it to a room which we would then incorrectly think is unsolvable.
            for rm in getattr(self, kind, []):
                #~ if rm.hashid=='1d70048c28acc547d8990181d0baaab1x020x006':
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                if rm.all_sols:
                    bad=rm.modify_hints_based_on_allsols()
                    if bad:
                        res=self.promote_to_illegal(bad)
                        if res:return False
                    self.adopt_room_hints(rm)
        return solved_one

    def eval_bumps(self):
        #~ print 'hbump',
        done=set()
        #~ self.sh()
        for pos in self.global_hints:
            if pos in done:continue
            outs=[]
            for gh in self.global_hints[pos]:
                if gh[1] not in outs:
                    outs.append(gh[1])
            if len(outs)==1:
                forced_path=get_children(pos, self.global_hints)
                if forced_path is False:
                    res=self.promote_to_illegal(pos)
                    if res:return False
                if forced_path:
                    for n in range(2, len(forced_path)):
                        twoago=makevec(forced_path[n-2], forced_path[n-1])
                        lastdv=makevec(forced_path[n-1],forced_path[n])
                        if forced_path[n] in done:
                            break
                        if twoago!=lastdv:
                            bump=add(forced_path[n-1], twoago)
                            if bump in forced_path[n-1:]:
                                #~ import ipdb;ipdb.set_trace()
                                #~ print 'bumped child!!! wtf'
                                res=self.promote_to_illegal(forced_path[n-1])
                                if res:
                                    return False
                    done.update(forced_path)
        #~ print 'hbok!',
        return True

    def make_global_hints(self, loopct):
        """"""
        self.lastchangecount=0
        #~ print 'make global'
        while self.changecount>self.lastchangecount:
            save_global_hints(self,self.global_hints,'%04d-outer'%(self.changecount))
            #~ print 'hint implications'
            self.lastchangecount=self.changecount
            self.remove_global_hints_based_on_roomsols()
            self.inner_changecount=self.changecount-1
            #comparing GLOBAL TO GLOBAL
            while self.changecount>self.inner_changecount:
                #~ print 'remove impossible',self.changecount,
                save_global_hints(self,self.global_hints,'%04d-inner'%(self.changecount))
                self.inner_changecount=self.changecount
                passed=self.remove_impossible_hints_from_global()
                if not passed:
                    #~ print 'not pass.'
                    self.changecount=self.lastchangecount+1
                    break
                #~ print 'ok',self.changecount,
                #~ print 'hbumps',self.changecount,
                self.eval_bumps()
                #~ print 'ok',self.changecount,
            if not passed:
                break
            save_global_hints(self,self.global_hints,'%04d-implications-done'%(self.changecount))
            self.find_bumps()
            self.eval_bumps()

            for kind in self.roomkinds:
                #~ print 'global hints %s'%kind
                if config.no_propagate_pararooms and kind=='pararooms':continue
                #~ if kind=='optrooms':continue
                rooms=getattr(self,kind,[])
                for ii,rm in enumerate(rooms):
                    if not rm.all_sols or rm.all_sols=='timeout':
                        continue
                    #~ if ii%1000==0:print 'pruning %s %d/%d cc: %d'%(kind, ii, len(rooms)-1, self.changecount)
                    origsols=len(rm.all_sols)
                    pruned=0
                    if config.prune:
                        debug=False
                        pruned=prune_room_sols(rm,self.global_hints,self,debug=debug)
                        if pruned is False:
                            return False
                        #removes sols that contradict global hints.
                    if pruned:
                        #~ print 'p:%d==>%d'%(origsols,len(rm.all_sols)),#,rm.hashid
                        self.changecount+=1
                        bad=rm.modify_hints_based_on_allsols()
                    origsols=len(rm.all_sols)
                    better_pruned=0
                    if config.better_prune:
                        better_pruned=better_prune_sols(rm,self.global_hints,self)
                        #removes sols that are internally inconsistent (can't enter before you leave)
                        if better_pruned:
                            #~ print 'b:%d==>%d'%(origsols,len(rm.all_sols)),
                            self.changecount+=1
                            bad=rm.modify_hints_based_on_allsols()
                            if bad:
                                res=self.promote_to_illegal(bad)
                                if res:return False
                        if better_pruned is False:
                            return False
                    origsols=len(rm.all_sols)

            save_global_hints(self,self.global_hints,'%04d-kind-%s-done'%(self.changecount,kind))
            bump_pruned=0
            if config.bump_prune:
                #~ print 'bump',
                bump_pruned=bump_prune_sols(self)
                #~ print 'ret',bump_pruned,
                if bump_pruned:
                    #~ print 'bumppr:%d==%d'%(origsols, len(rm.all_sols)),
                    self.changecount+=1
                    bad=rm.modify_hints_based_on_allsols()
                    if bad:
                        res=self.promote_to_illegal(bad)
                        if res:return False
                if bump_pruned is False:
                    return False
            save_global_hints(self,self.global_hints,'%04d-pruned'%(self.changecount))
        save_global_hints(self,self.global_hints,'loop%02d-%04d'%(loopct,self.changecount),force=True)
        self.eval_bumps()

    def promote_to_illegal(self,pos=None, path=None):
        """
        if some illegal stuff happened, promote the room.

        if the new room is the same as the old, we need to expand more.
        this should only happen within a tunnel or a gatesq.  if not, bug.  and it will always(?)
        involve creating a new illegalroom from the rooms at the end of that tunnel,
        reqrooms only, too.
        """
        #~ self.sh()
        if config.monitor_promotion:
            import ipdb;ipdb.set_trace()
        reqrm=None
        ins=[]
        if pos:
            parts=set([pos])
        elif path:
            parts=set(path)
        for pos in parts:
            allrooms=self.pos2allrooms(pos)
            for rm in allrooms:
                if not rm.kind=='reqrooms':
                    continue
                if rm not in ins:
                    ins.append(rm)
        for pos in parts:
            if isreqtunnel(self.rows, pos):
                tunnelsqs, ends=get_tunnelsqs_ends(self.rows, pos)
                for e in ends:
                    other_reqrm=self.pos2rooms[e].get('reqrooms',[])
                    if other_reqrm:other_reqrm=other_reqrm[0]
                    if other_reqrm not in ins:
                        ins.append(other_reqrm)
        #~ print 'promoting',parts
        reqrm=mkroom(rows=self.rows, pos=None, method='merge', extras={'rooms':ins})
        for il in self.original_illegal_rooms:
            if il.hashid==reqrm.hashid:
                #~ print 'not, cause reqrm is a copy of illegal'
                #~ self.clear_all_hints()
                return False
        if reqrm in self.original_illegal_rooms:
            #~ print 'not, cause reqrm is already illegal'
            #~ self.clear_all_hints()
            return False
        self.changecount+=1
        #~ print reqrm
        for il in self.original_illegal_rooms:
            if il.kind=='merge':
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                reqrm=mkroom(rows=self.rows, pos=None, method='merge', extras={'rooms':[reqrm, il]})
                self.original_illegal_rooms.remove(il)
        if reqrm not in self.original_illegal_rooms:
            self.addorig(reqrm)
                #~ #commented out to save level 34...
        #~ print 'oir has %d'%len(self.original_illegal_rooms)
        if len(self.original_illegal_rooms)>1000:
            import ipdb;ipdb.set_trace()
        #~ self.ilrooms=newil
        #if there are two pararooms that touch based on
        ii=0
        self.sh()
        #~ print 'RESTORING ALL HINT!'
        #necessary so we don't end on a promotion.
        self.just_promoted_to_illegal=1
        self.clear_all_hints()
        self.actual_bumps=set()
        self.bumps=[]
        return True

    def clear_all_hints(self):
        self.global_hints=self.orig_global_hints.copy()
        for kind in self.roomkinds:
            rmlist=getattr(self,kind,[])
            for rm in rmlist:
                rm.reset_hints()
                rm.all_sols=None

    def remove_impossible_hints_from_global(self):
        """relates every global sq to it's neighbors.  and removes hints that contradict.
        for example if i have an out hint going R, but R square has no in hint from me, remove my out hint.

        if we remove all hints, there is a problem, and we do promote_to_illegal"""
        il_allsqs=set()
        for il in self.original_illegal_rooms:
            il_allsqs.update(il.orig_allsqs)
        if self.orig_alley:
            il_allsqs.add(self.orig_alley)
        if self.extra_alley:
            il_allsqs.add(self.extra_alley)
        for ii,pos in enumerate(self.global_hints):
            if config.skip_hints_on_ilsqs and pos in il_allsqs:
                continue
            ghints=self.global_hints[pos]
            badpos=False
            myouts=set()
            myins=set()
            for gh in ghints:
                myins.add(gh[0])
                myouts.add(gh[1])
            if not myins or not myouts:
                #~ print 'unreachable position',pos,'promoting to illegal'
                res=self.promote_to_illegal(pos)
                if res:return False
            for n in [0,1,2,3]:
                if n not in myins:
                    cant_be_parent=add(pos,n+2)
                    if config.skip_parent_hints_on_ilsqs and cant_be_parent in il_allsqs:
                        continue
                    if self.isopen(cant_be_parent):
                        new_parent_hints=set([h for h in self.global_hints[cant_be_parent] if h[1]!=n])
                        #parent can't point to here, either.
                        if new_parent_hints!=self.global_hints[cant_be_parent]:
                            if not new_parent_hints:
                                #~ print 'last hint gone for',cant_be_parent
                                res=self.promote_to_illegal(cant_be_parent)
                                if res:return False
                            self.set_hints(cant_be_parent, new_parent_hints)
                            save_global_hints(self,self.global_hints,'%04d-%s\ncant be parent'%(self.changecount,str(cant_be_parent)))
                            self.changecount+=1
                if n not in myouts:
                    cant_be_child=add(pos,n)
                    if config.skip_parent_hints_on_ilsqs and cant_be_child in il_allsqs:
                        continue
                    if self.isopen(cant_be_child):
                        new_child_hints=set([h for h in self.global_hints[cant_be_child] if h[0]!=n])
                        if new_child_hints!=self.global_hints[cant_be_child]:
                            if not new_child_hints:
                                #~ print 'last hint gone for',cant_be_child
                                res=self.promote_to_illegal(cant_be_child)
                                if res:return False
                            self.set_hints(cant_be_child, new_child_hints)
                            save_global_hints(self,self.global_hints,'%04d-%s\ncant be child'%(self.changecount,str(cant_be_child)))
                            self.changecount+=1

            if len(myins)==1:
                myin=list(myins)[0]
                myparent=add(pos,myin+2)
                if config.skip_parent_hints_on_ilsqs and myparent in il_allsqs:
                    continue
                new_parent_hints=set([h for h in self.global_hints[myparent] if h[1]==myin])
                if new_parent_hints!=self.global_hints[myparent]:
                    #~ if pos==pmp or myparent==pmp:
                        #~ print 'CC',self.changecount,self.global_hints[pmp]
                    if not new_parent_hints:
                        #~ print 'last hint gone for:',myparent
                        res=self.promote_to_illegal(myparent)
                        if res:return False
                    self.set_hints(myparent, new_parent_hints)
                    save_global_hints(self,self.global_hints,'%04d-%s\nhas only one child, me %s'%(self.changecount,str(myparent),str(pos)))
                    self.changecount+=1
                    #~ continue
            if len(myouts)==1:
                myout=list(myouts)[0]
                #~ myouts.add(myout)
                mychild=add(pos,myout)
                if config.skip_parent_hints_on_ilsqs and mychild in il_allsqs:
                    continue
                new_child_hints=set([h for h in self.global_hints[mychild] if h[0]==myout])
                if new_child_hints!=self.global_hints[mychild]:
                    if not new_child_hints:
                        #~ print 'last hint gone for',mychild
                        res=self.promote_to_illegal(mychild)
                        if res:return False
                    self.set_hints(mychild, new_child_hints)
                    save_global_hints(self,self.global_hints,'%04d-%s\nhas only one parent, me %s'%(self.changecount,str(mychild),str(pos)))
                    self.changecount+=1
                    #~ continue

        #finally, do a check for loops within global hints..  if we find one, promote the loopzone -reqrooms to illegal.
        checked=set()

        for ii, pos in enumerate(self.global_hints):
            if pos in checked:
                continue
            if config.skip_hints_in_later_prune:
                if pos in il_allsqs:
                    continue
            now=pos
            gh=self.global_hints[pos]
            badpos=False
            seen=set()
            seen.add(pos)
            while len(gh)==1:
                now=add(now, list(gh)[0][1])
                if now in seen:
                    badpos=True
                    break
                seen.add(now)
                gh=self.global_hints[now]
            checked.update(seen)
            if badpos:
                res=self.promote_to_illegal(pos=None, path=seen)
                if res:return False

        #and now do a check that no path hits it's child.
        #i.e. you can't bump into a place you haven't gotten yet.


        return True

    def remove_global_hints_based_on_roomsols(self):
        """self explanatory - basic stuff."""
        changes=0
        ###making
        ils_allqs=set()
        for il in self.original_illegal_rooms:
            ils_allqs.update(il.orig_allsqs)
        for kind in self.roomkinds:
            for ii,rm in enumerate(getattr(self,kind,[])):
                if rm.all_sols and config.skip_remove_based_on_roomls and rm.all_sols!='timeout':
                    if not rm.orig_allsqs.isdisjoint(ils_allqs):
                        continue
                    for pos in rm._global_hints:
                        rmhints=rm._global_hints[pos]
                        ghints=self.global_hints[pos]
                        if rmhints!=ghints:
                            combo=ghints.intersection(rmhints)
                            if combo!=ghints:
                                #~ if ii%100==0:
                                    #~ print ii,'removing global possible inouts: %d==>%d'%(len(ghints),len(combo))
                                self.changecount+=1
                                self.set_hints(pos, combo)


    def merge_alleys_into_illegals(self):
        """#oftimes a pararoom will recapture the same meaning as an alley.
        #so if we have an alley, expand it out and test merge it with a pararoom (other room?) it meets
        #an alley is a subset of a room if: the complete set of flow paths to every square on the board, everything
        #single flow path passes through the pararoom.  it is unfortunate that if we merge it into a room
        but then start in the room, but dont refind the room as illegal, it fails."""
        if self.orig_alley and len(self.original_illegal_rooms):
            alleys=[self.orig_alley]
            if self.extra_alley:
                alleys.append(self.extra_alley)
            for alley in alleys:
                merged=False
                tilmeet={}
                for ii,il in enumerate(self.original_illegal_rooms):
                    tilmeet[ii]=floodfill_with_blocks(self.rows,alley,il.orig_allsqs)
                    #this does not shortcircuit when hitting a block
                minsqs={}
                bestii=None
                merge_sqs={}
                for ii,sqs in tilmeet.items():
                    if not minsqs or len(sqs)<minsqs[bestii]:
                        bestii=ii
                        minsqs[ii]=len(sqs)
                        merge_sqs[ii]=sqs
                        #~ bestsqs[ii]=sqs
                for ii, il in enumerate(self.original_illegal_rooms):
                    if ii==bestii:
                        merged=True
                        self.original_illegal_rooms[ii].add_poss(merge_sqs[ii])
                        self.original_illegal_rooms[ii].contained_alley=alley
                        #adjusted to the way we now keep all illegal rooms from the beginning
                        #just keep them all and merge the alley when appropriate. (if alley merged is less than whole board)
                #find the gates that touched, and make them into sqs too.
                for gsq in self.original_illegal_rooms[bestii].orig_gatesqs:
                    ct=0
                    for o in orth(gsq):
                        if o in self.original_illegal_rooms[bestii].orig_sqs:
                            #dont want to kill double squares.  just detect gates that now touch 2 interior spaces.
                            ct+=1
                    if ct>1:
                        #make this a normal square, not a gate.
                        self.original_illegal_rooms[bestii].add_poss(sqs=set([gsq]))
                        self.original_illegal_rooms[bestii].remove_poss(gatesqs=set([gsq]))
                if alley==self.orig_alley:
                    #~ print 'merged orig alley'
                    if not merged:
                        continue
                        #this should never happen
                    self.orig_alley=None
                elif alley==self.extra_alley:
                    #~ print 'merged extra alley.'
                    if not merged:
                            continue
                            #this should never happen
                    self.extra_alley=None

    def remove_superior_illegals(self):
        """if an il is totally superior to another then just remove it from origs, unless it has an alley!"""
        bads=[]
        for target in self.original_illegal_rooms:
            for other in self.original_illegal_rooms:
                if target.hashid==other.hashid:continue
                if target.kind=='merge':
                    #don't ever remove a merge room.
                    continue
                if target.orig_allsqs>other.orig_allsqs:
                    if not target.contained_alley:
                        #do NOT remove an ilroom which contains an alley!  then we would totally lose track of that alley and be fucked!
                        bads.append(target)
        for il in bads:
            #somehow dups are in here.
            if il in self.original_illegal_rooms:
                self.original_illegal_rooms.remove(il)
                #~ print 'removing superior il from originals.',il
        return None

    def get_orig_global_hints(self):
        """the basic global hints - everything allowed."""
        orig_global_hints={}
        for pos in self.orig_open:
            outs=self.getopendv_loc(pos)
            orig_global_hints[pos]=set()
            for o in outs:
                for i in outs:
                    if o==i:
                        continue
                    i=(i+2)%4
                    orig_global_hints[pos].add((i,o))
        return orig_global_hints



    def prune_starts_which_are_inside_solved_rooms(self):
        """a start is never required to be in a genuinely solved room; at worst it can be required to be in a gatesq

        but be careful!  if a start is a gatesq for ANY room, it may be needed!
        """
        if not config.prune_starts:
            return
        badsqs=set()
        oksqs=set()
        for kind in self.roomkinds:
            rlist=getattr(self,kind,[])
            for rm in rlist:
                res=rm.has_sol(toplevel=True)
                #has_sol checks rooms are provably abd.  and it can tmieout. cases like taht don't mean you shouldn't start there.
                #so this can cause problems.  has_sol should return 'timeout' not true!
                if res and res!='timeout' and res != 'bigroom-timeout' and res != 'deadend':
                    badsqs.update(rm.orig_sqs)
                    oksqs.update(rm.orig_gatesqs)
        oldlen=len(self.starts)
        self.starts=[st for st in self.starts if (st[0] not in badsqs) or (st[0] in oksqs)]
        #~ print '===========removing: %dbadstarts!'%(oldlen-len(self.starts))
        self.starts=self.starts.difference(badstarts)
        self.donestarts.update(badstarts)

    def enter_tunnel(self,pos):
        """returns:
        endpos,newcovered,exit_dv=board.enter_tunnel(next)
        and brings the person to the last deeptunnel sq - not the reqgate sq!  so that the spilt checking will work on the last step.
        """
        return self.tunnelcache[pos]


    def save_starts(self):
        fname='%s-starts'%self.levelnum
        special_dict={}
        for sq in self.starts:
            special_dict[sq[0]]=(200,150,100)
        pshow(overwrite=True,rows=self.rows,special_dict=special_dict,worktype='%s'%self.levelnum,fname=fname)

    def addorig(self, il):
        if self.orig_alley:
            if self.orig_alley in il.orig_allsqs:
                self.orig_alley=None
        if self.extra_alley:
            if self.orig_alley in il.orig_allsqs:
                self.orig_alley=None
        #~ if not len(il.orig_gatesqs):
            #~ print 'skipping gateless il add.'
            #~ return
        self.original_illegal_rooms.append(il)
        self.remove_superior_illegals()

    def intersect_hints(self, pos, hints):
        if pos in config.hintmonpos:
            import ipdb;ipdb.set_trace();print 'ipdb!'
        self.global_hints[pos]=self.global_hints[pos].intersection(hints)

    def adopt_room_hints(self, rm):
        """some weird stuff about pararooms.  they do get solved, and they do get pruned. but we don't adopt
        hitns back to them.  so we can tell when one of them becomes illegal, but nothing propagates out from them
        because starting positions can mess that info up too easily."""
        if config.no_propagate_pararooms and rm.kind=='pararooms':
            return
        if config.skip_hints_within_illegal:
            for il in self.original_illegal_rooms:
                if not il.orig_allsqs.isdisjoint(rm.orig_allsqs):
                    return
                #dno't adopt hints from subrooms of illegals.
        for pos in rm._global_hints:
            self.intersect_hints(pos, rm._global_hints[pos])

    def oob(self,pos):
        return oob(self.config,pos)

    def get_vsqs(self,sq):
        res=[sq]
        up=add(sq,3)
        while not self.oob(up) and self.isopen(up):
            res.append(up)
            up=add(up,3)
        down=add(sq,1)
        while not self.oob(down) and self.isopen(down):
            res.append(down)
            down=add(down,1)
        return res

    def get_hsqs(self,sq):
        res=[sq]
        right=add(sq,0)
        while not self.oob(right) and self.isopen(right):
            res.append(right)
            right=add(right,0)
        left=add(sq,2)
        while not self.oob(left) and self.isopen(left):
            res.append(left)
            left=add(left,2)
        return res

    def sq_of_solved_room(self, pos):
        rms=self.pos2allrooms(pos)
        for rm in rms:
            if pos not in rm.orig_sqs:
                continue
            if rm.all_sols and rm.all_sols!='timeout':
                return True
            so=rm.has_sol(toplevel=1)
            if so and so!='timeout':
                return True
            if rm.eversolved:
                return True
        return False

    def mkpos2rooms(self):
        """2011
        just make pos2 a list of related rooms.  gates are included."""
        #~ print 'mkpos2rooms'
        res={}
        for op in self.orig_open:
            res[op]={}
        for kind in self.roomkinds:
            rms=getattr(self,kind,[])
            for rm in rms:
                for pos in rm.orig_allsqs:
                    if kind in res[pos]:
                        res[pos][kind].append(rm)
                    else:
                        res[pos][kind]=[rm]
        self.pos2rooms=res

    def save_illegalroom_images(self,original=False):
        rmlist=self.original_illegal_rooms
        label='original-illegals'
        #~ else:
            #~ rmlist=self.original_illegal_rooms
            #~ label='merged-illegals'
        for ii,iroom in enumerate(rmlist):
            #~ print '\n========surviving illegalroom:'
            #~ print iroom
            if not self.loaded_illegals:
                if original:
                    lineage=iroom.hashid[:4]
                else:
                    try:
                        getattr(iroom,'p1')
                        lineage=iroom.p1[:4]+'-'+iroom.p2[:4]
                    except:
                        lineage='xxx'
                fname='%s-%s-%s-%s-sqs%d gates%d'%(self.levelnum,label,lineage,iroom.kind,len(iroom.sqs),len(iroom.gatesqs))
                special_dict={}
                for isq in iroom.orig_sqs:
                    special_dict[isq]=(140,140,20)
                for gsq,exitkind in iroom.gates:
                    if exitkind==1:
                        color=(140,140,220)
                    else:
                        color=(140,240,220)
                    special_dict[iroom.local2global(gsq)]=color
                imgtext=iroom.kind+'\n'+iroom.hashid[:6]
                pshow(rows=self.rows,special_dict=special_dict,worktype=self.levelnum,fname=fname,imgtext=imgtext)
                pshow(rows=self.rows,special_dict=special_dict,worktype='allhints',fname=fname,imgtext=imgtext)

        #~ if not original:
            #~ for ii in [0,1]:
                #~ if len(self.original_illegal_rooms)>ii:
                    #~ iroom=self.original_illegal_rooms[ii]
                #~ else:
                    #~ iroom=None
                #~ would='illegals/illegal%s-%d.pickle'%(self.levelnum,ii)
                #~ print 'SAVING illegal! to',would
                #~ cPickle.dump(iroom,open(would,'w'))
            #~ if not self.loaded_illegals:
                #~ if not self.ilrooms:
                    #~ would='illegals/%s-none'%self.levelnum
                    #~ open(would,'w')
            #~ would='illegals/timeouts%s.pickle'%(self.levelnum)
            #~ cPickle.dump(self.timeout_sqs,open(would,'w'))

    def isopen(self,loc):
        return not self.rows[loc[1]][loc[0]]

    def countopen(self):
        opencount=0
        closedcount=0
        for r in self.rows:
            for e in r:
                if e==0:
                    opencount+=1
                elif e==1:
                    closedcount+=1
        return opencount

    def getopen_open(self):
        opensq={}
        for loc in fullboard(self.config):
            res=[x for x in self.borders[loc] if self.isopen(x) and self.isopen(loc)]
            if res:
                opensq[loc]=res
        return opensq

    def getopen(self):
        return set([x for x in fullboard(self.config) if self.isopen(x)])

    def getopen_open_dvs(self):
        opensq={}
        for loc in innerboard(self.config):
            res=[dv for dv in [0,1,2,3] if self.isopen(add(loc,dv)) and self.isopen(loc)]
            if res:
                opensq[loc]=res
        return opensq

    def getopen_closed_dvs(self):
        opensq={}
        for loc in innerboard(self.config):
            res=[dv for dv in [0,1,2,3] if not self.isopen(add(loc,dv)) and self.isopen(loc)]
            if res:
                opensq[loc]=res
        return opensq

    def getopen_loc(self,loc):
        return [x for x in self.borders[loc] if self.isopen(x)]

    def getopendv_loc(self,loc):
        return [dv for dv in [0,1,2,3] if self.isopen(add(loc,dv))]

    def count_open(self):
        realopen=0
        for r in self.rows:
            for c in r:
                if c==0:
                    realopen+=1
        return realopen

    def getclosed_loc(self,loc):
        return [x for x in borders[loc] if not self.isopen(x)]

    def getstarts(self,all=False):
        starts=set()
        for loc in self.orig_open_open:
            for openpos in self.orig_open_open[loc]:
                this_start=loc,makevec(loc,openpos)
                starts.add(this_start)
        if config.monitor_start and config.monitored_start not in starts:
            import ipdb;ipdb.set_trace()
            #~ print 'x'
            sys.exit()
        if not all and self.config.do_target:
            starts=set([s for s in starts if s==self.config.target])
        if config.monitor_start and config.monitored_start not in starts:
            import ipdb;ipdb.set_trace()
            #~ print 'x'
            sys.exit()
        #~ print 'raw made %d starts'%(len(starts))
        if config.do_target:
            if config.target not in starts:
                #~ print 'not in'
                import ipdb;ipdb.set_trace()
        return starts

    def remove_cached_starts(self):
        if config.use_start_cache:
            #~ print 'loading from cache'
            from admin import load_done
            self.donestarts=set(load_done(self.levelnum))
            #~ print 'loaded donestarts:',len(self.donestarts)
            for st in self.donestarts:
                if st in self.starts:
                    self.starts.remove(st)
        #~ else:
            #~ print 'not using solved_start cache'

    def remove_deeptunnel_starts(self):
        return
        badstarts=set()
        for st in self.starts:
            if isdeeptunnel(self.rows,st[0]):
                badstarts.add(st)
        self.donestarts.update(badstarts)
        self.starts=self.starts.difference(badstarts)
        #~ print 'removed %d dt starts; left:'%len(self.donestarts),len(self.starts)
        if not self.starts:
            #~ print 'no starts left.'
            import ipdb;ipdb.set_trace()

    def remove_impossible_starts(self):
        has_disjoint_illegals=0
        ilsqs=set()
        for il in self.original_illegal_rooms:
            ii=il.orig_allsqs.copy()
            if il.kind=='pararooms':
                for n in il.orig_gatesqs:
                    ii.update(orth(n))
                #use extended orig+all instead
            if ilsqs and ii.isdisjoint(ilsqs):
                has_disjoint_illegals=1
            ilsqs.update(ii)
                #have to include near spaces to pararoom gsqs, cause they can make the room not illegal too
                #cause of my messed up pararoom def.
            #not rigorous but should always work if original illegal rooms is sensible.
        if has_disjoint_illegals:
            #there can still be problem starts.  for example if A sup B intersect, and C is disjoint.  exterior points in A
            #will not be removed by this.
            oldst=len(self.starts)
            self.starts=[s for s in self.starts if s[0] in ilsqs]
            #~ print 'has disjoin illegals so removed other starts %d ==> %d'%(oldst, len(self.starts))

    def setup_important_starts(self):
        self.important_starts=set()
        if self.orig_alley:
            for n in [0,1,2,3]:
                would=add(self.orig_alley,n)
                if not isopen(self.rows,would):
                    continue
                self.important_starts.add((self.orig_alley,n))
        if self.extra_alley:
            for n in [0,1,2,3]:
                would=add(self.extra_alley,n)
                if not isopen(self.rows,would):
                    continue
                self.important_starts.add((self.extra_alley,n))
        for il in self.original_illegal_rooms:
            for sq in il.orig_allsqs:
                for n in [0,1,2,3]:
                    would=add(sq,n)
                    if not isopen(self.rows,would):
                        continue
                    self.important_starts.add((sq,n))
        #~ print 'made %d important starts!'%(len(self.important_starts))
        #~ print 'made %d more timeout starts!'%(len(self.important_starts))

    def setup_timeout_starts(self):
        self.timeout_starts=set()
        for sq in self.timeout_sqs:
            for n in [0,1,2,3]:
                would=add(sq,n)
                if not isopen(self.rows,would):
                    continue
                self.timeout_starts.add((sq,n))

    def set(self,pos):
        self.rows[pos[1]][pos[0]]=1
        self.curopen-=1

    def set_many(self,many):
        for pos in many:
            self.rows[pos[1]][pos[0]]=1
        self.curopen-=len(many)
        if self.curopen<self.thisst_best_curopen:
            self.thisst_best_curopen=self.curopen
            self.thisst_best_sol=self.sol[:]

    def unset(self,pos):
        self.rows[pos[1]][pos[0]]=0
        self.curopen+=1

    def unset_many(self,many):
        for pos in many:
            self.rows[pos[1]][pos[0]]=0
        self.curopen+=len(many)

    def choose_one(self):
        if config.do_target:
            if config.target in self.starts:
                self.starts.remove(config.target)
            #~ else:
                #~ print 'not a start for some reason!'
            return config.target
        if 0 and config.important_starts_first:
            while self.important_starts:
                this=self.important_starts.pop()
                if this in self.donestarts:
                    continue
                if not self.isopen(this[0]):
                    continue
                if not self.isopen(add(this[0],this[1])):
                    continue
                if this not in self.starts:
                    pass
                    #~ continue
                else:
                    self.starts.remove(this)
                #~ print  'i',
                return this
            #~ print ' ',
        if 0 and config.timeout_starts_before:
            while self.timeout_starts:
                this=self.timeout_starts.pop()
                if this in self.donestarts:
                    continue
                if not self.isopen(this[0]):
                    continue
                if not self.isopen(add(this[0],this[1])):
                    continue
                if this not in self.starts:
                    continue
                self.starts.remove(this)
                #~ print 't',
                #~ print 'doing timeout start',this
                return this
        if config.do_target:
            self.starts=[]
            return (config.targetpos,config.targetdv)
        if not config.important_starts_first:
            tried=set()
            while 1:
                usest=self.starts.pop()
                if usest in self.important_starts:
                    tried.add(usest)
                    continue
                else:
                    self.starts.update(tried)
                    break
            #~ print 'xi',
        else:
            usest=self.starts.pop()
        return usest

    def ch(self, pos=None):
        #~ print 'CH:',getattr(self,'changecount','no changecount yet.')
        if config.mhintpos:
            #~ print self.global_hints[config.mhintpos]
            if not self.global_hints[config.mhintpos]:
                import ipdb;ipdb.set_trace()
        if config.mhintpos ==pos:
            import ipdb;ipdb.set_trace()
            #~ print 'messing with my hint'

    def set_hints(self, pos, newhints):
        if pos in config.hintmonpos:
            import ipdb;ipdb.set_trace();print 'ipdb!'
        self.global_hints[pos]=newhints

    def si(self):
        if not self.air:
            #~ print 'NO ILLEGAL ROOM ATm.'
            pass
        else:
            #~ print 'ILL:'
            self.show(self.air)

    def srh(self, rm):
        save_global_hints(self,rm=rm, force=1)

    def sh(self, extra_text=None):
        if not extra_text:
            extra_text=''
        save_global_hints(self, extra_text=extra_text, force=1)
    @property
    def sg(self):
        self.show(self.glob)

    def reset(self):
        self.air=None
        self.airstore=[]
        self.alleystore=[]
        self.best_curopen=None
        self.best_sol=None
        self.borders=mkborders(config)
        self.curopen=None
        self.donestarts=set()
        self.endpos=None
        self.glob=set()
        self.globstore=[]
        self.now=(0,0)
        self.packcheck=set()
        self.solvetime=None
        self.sol=[]
        self.sol_starts={}
        self.startpos=None
        self.thisst_best_curopen=None
        self.thisst_best_sol=[]
        self.vergstore=[]
        self.cur_sol=None
        self.orig_rows=self.rows[:]
        self.orig_open=self.getopen()
        self.orig_open_open=self.getopen_open()
        self.orig_open_count=self.countopen()
        self.orig_closed=[x for x in fullboard(self.config) if not self.isopen(x)]
        self.orig_open_open_dvs=self.getopen_open_dvs()
        self.orig_open_closed_dvs=self.getopen_closed_dvs()
        self.curopen=len(self.orig_open)
        self.orig_open_count=self.curopen
        self.maxopen=self.curopen
        self.deeptunnels=set()
        self.actual_bumps=set()
        #all_solpaths
        sp='solpaths/%s.pickle'%self.levelnum
        if not os.path.isfile(sp) and config.check_all_sol_paths:
            #~ print 'no complete sols'
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            self.all_solpaths={}
            #will save it instead.
            self.loaded_all_solpaths=False
        else:
            self.all_solpaths=general_load_pickle(sp)
            self.loaded_all_solpaths=True
            #if we loaded all solpaths, severely disable saving of stuff
            #cause most of the time it won't matter.

        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        for pos in self.orig_open:
            if isdeeptunnel(self.rows,pos):
                self.deeptunnels.add(pos)
        #STARTS
        self.starts=self.getstarts()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        self.remove_cached_starts()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        self.remove_deeptunnel_starts()
        if config.monitor_start and config.monitored_start not in self.starts:
            import ipdb;ipdb.set_trace();print 'missing start.'
        self.timeout_sqs=set()
        self.ilrooms=[]
        self.loaded_illegals=False
        self.original_illegal_rooms=[]
        self.ever_covered=set()
        #sqs which have been covered & are within a completely solved room. these starts can never be required starts.
        self.badstart_positions_len=0
        self.alldone=0
        self.restore_later_hints={}

    def newstart(self):
        self.begintime=time.time()
        self.depth=0
        self.thisst=time.time()
        self.curopen=self.orig_open_count
        self.thisst_best_curopen=self.curopen
        self.sol=[]
        self.alley=self.orig_alley
        self.alleytunnel=self.orig_alleytunnel
        self.alleytunnelends=self.orig_alleytunnelends
        self.air=None
        self.vergr=[]
        self.vergl=[]
        pos,dv=self.choose_one()
        #keep going til u get a sol start
        if config.check_all_sol_paths and config.force_all_sol_paths and self.all_solpaths:
            while 1:
                if (pos, dv) in self.all_solpaths:
                    #~ print 'chose sol start.'
                    break
                if not self.starts:
                    break
                #~ print 's',
                pos, dv=self.choose_one()
        self.start=(pos,dv)
        self.startpos=pos
        self.startdv=dv
        self.glob=mkglob(self.allneighbors,self,pos)
        self.sawr=[[add(pos,dv+1)]]
        self.sawl=[[add(pos,dv-1)]]
        self.in_sol_start=0
        if self.isopen(add(pos,dv+2)):
            self.back=[add(pos,dv+2)]
        else:
            self.back=None
        if (pos, dv) in self.all_solpaths :
            self.cur_sol=self.all_solpaths[(pos, dv)]
            self.cur_sol.reverse()
            #~ print 'set cur sol len %d'%(len(self.cur_sol))
            #put it backwards so we can cut off the tail as we go.
            self.in_sol_start=1
        return pos, dv

    def setup_origalleys(self):
        """look for alleys in the initial board setup; not very common."""
        alleys=[]
        for pos in innerboard(config):
            if isalley(self,pos):
                alleys.append(pos)
        if len(alleys)>=2:
            #~ print "TWO ALLEYS!!!"
            self.extra_alley=alleys[1]
            self.orig_extraalleytunnel,self.orig_extraalleytunnelends=get_tunnelsqs_ends(self.rows,alleys[1])
        else:
            self.extra_alley=None
            self.orig_extraalleytunnel,self.orig_extraalleytunnelends=[],[]
        if alleys:
            self.orig_alley=alleys[0]
            self.orig_alleytunnel,self.orig_alleytunnelends=get_tunnelsqs_ends(self.rows,alleys[0])
        else:
            self.orig_alley=None
            self.orig_alleytunnel,self.orig_alleytunnelends=[],[]
        #~ print 'setup alley initial alley:',self.orig_alley
        if self.orig_alley and self.extra_alley:
            self.starts=[s for s in self.starts if s[0] ==self.orig_alley or s[0]==self.extra_alley]

    def pos2allrooms(self, pos, all=True,sqs=False, gates=False):
        """utility func. to get all related rooms to a global pos"""
        if sqs or gates:
            all=False
        rms=[]
        for rmlist in self.pos2rooms.get(pos,{}).values():
            for rm in rmlist:
                if all:
                    if pos in rm.orig_allsqs:
                        rms.append(rm)
                elif sqs:
                    if pos in rm.orig_sqs:
                        rms.append(rm)
                elif gates:
                    if pos in rm.orig_gatesqs:
                        rms.append(rm)
        return rms



    def setup_counts(self):
            self.counts={}
            self.counts['alley']={'nobt':0,'bt':0,}
            for k in self.roomkinds:
                self.counts[k]={'not_illegal':0,'illegal':0,'illegal_but_intersect':0,'timeout':0,}
            self.counts['pararooms-subroom']={'not_illegal':0,'illegal':0,'illegal_i':0,'timeout':0,}
            self.counts['reqrooms-subroom']={'not_illegal':0,'illegal':0,'illegal_i':0,'timeout':0,}
            self.counts['optrooms-subroom']={'not_illegal':0,'illegal':0,'illegal_i':0,'timeout':0,}
            self.counts['vhint']={'bt':0,'notenough':0,'ok':0}

    def showstats(self, force=None):
        #~ print "CACHE STATS"
        for k,v in sorted(self.counts.items()):
            res='\n'
            res+='%s==>  '%k
            ok=False
            for kk,vv in v.items():
                res+='\t%s-----%s'%(kk,str(vv))
                if vv>0:
                    ok=True
            if ok:
                print res,
        from simpleroom import g_allsols_cache, g_hassols_cache
        global g_allsols_cache,g_hassols_cache
        #~ print '\ncaches all:%s (%0.6f) has:%s (%0.6f)'%(len(g_allsols_cache),1.0*config.allhit/(config.allhit+config.allmiss+1),len(g_hassols_cache),1.0*config.hashit/(config.hashit+config.hasmiss+1))

    def show(self,specials={},now=None, rows=None):
        """specials is :
        dict of pos => char
        list
        tuple
        controls the display of the board."""
        if rows:
            userows=rows
        else:
            userows=self.rows
        conv={}
        if type(specials) is types.InstanceType:
            res={}
            for sq in specials.orig_sqs:
                res[sq]='X'
            for gatesq in specials.gatesqs:
                for gate in specials.gates:
                    if gate[0]==gatesq:
                        reqopt=gate[1]
                        break
                if reqopt==1:
                    res[specials.local2global(gatesq)]='R'
                else:
                    res[specials.local2global(gatesq)]='*'
            specials=res
        elif type(specials) is tuple:
            specials={specials:'X'}
        elif type(specials) is list:
            rev={}
            for pos in specials:
                rev[pos]='X'
            specials=rev
        elif type(specials) is set:
            rev={}
            for s in specials:
                rev[s]='X'
            specials=rev
        elif type(specials) is dict:
            rev={}
            for k,v in specials.items():
                rev[v]=k
            specials=conv
        for yy,r in enumerate(userows):
            l=''
            for xx,val in enumerate(r):
                if now and (xx,yy)==now:
                    l+='N'
                elif (xx,yy) in specials:
                    l+=specials[(xx,yy)]
                elif (xx,yy) in self.orig_closed:
                    l+="1"
                    continue

                elif val==0:
                    l+='_'
                elif val==1:
                    l+='2'
            print l
        realopen=self.count_open()
        if realopen!=self.curopen:
            import ipdb;ipdb.set_trace()
            sys.exit()
