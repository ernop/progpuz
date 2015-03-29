import pprint,shutil,time,random,traceback,hashlib,traceback,os,copy
try:
    import cPickle
except:
    import pickle as cPickle
from split_utils import *
from admin import boxify,pshow, res2code
from admin import make_room_inouts,general_load_pickle,general_save_pickle
from admin import copysols,copysol
from simpleroom import *
import config


class Room():
    #rooms don't know that much about their parentage...
    #maybe need to define __eq__ for comparisons. x,yoffset, sqs, gates is all they are.
    """2011 - now, rooms are allowed to have reqgates right next to eachother - they both must be pointing inward.

    gates format is sq, 1 for reqgates...?  2 for optgates.  i guess it's the number of exits from the gatesq which aren't in sqs. ()
    sqs are local!  get back to orig (global) pos by using local2global

    #the important thing is self.sqs, self.gates
    after modifying those, do fix_offset and recalc.

    I should do slots for this.  __all__
    """

    #~ __slots__=('orig_sqs', 'orig_gates', 'contained_alley', 'kind', 'levelnum', 'timelimit', 'kind', '_global_hints',\
        #~ '_hints', 'hash_done', 'sources', 'destinations', 'mystart', 'all_sols', 'timeout', 'eversolved', 'usage', 'hints_prepped', 'used_external_hint',\
        #~ '_tunnelsqs', 'product_of_pararoom_merging', 'has_merged', 'gates', 'gatesqs', 'allsqs', 'orig_allsqs', 'orig_gatesqs',\
        #~ 'req_ct', 'opt_ct', 'gsq_ct',  \
        #~ '_color','xoffset','yoffset','width','height','sqs','rows','hashid',\
        #~ 'key','external_hints','parent')
    #~ __slots__=tuple(__slots__)
    #~ __slots__=('orig_sqs',)
    #~ import ipdb;ipdb.set_trace()


    def __init__(self,sqs,gates,levelnum=None, kind=None, timeout=None, usage=None):
        self.orig_sqs=set(sqs)
        self.orig_gates=set(gates)
        self.contained_alley=None

        self.levelnum=levelnum
        self.kind=kind
        self.timelimit=None
        #timelimit will be set when a has_ sol is done.
        if not kind:
            self.kind='default'

        self._global_hints={}
        self._hints={}
        self.hash_done=None
        self.sources=None
        self.destinations=None
        self.mystart=None
        self.all_sols=None
        self.timeout=None
        if timeout:
            self.timeout=timeout
            #not limit.
        self.eversolved=False
        if usage:
            self.usage=usage
        else:
            self.usage=kind
            #usage is the human description of the kind (&lineage)
        self.recalc()
        self.hints_prepped=0
        self.used_external_hint=0
        self._tunnelsqs=set([])
        self.product_of_pararoom_merging=0
        self.has_merged=0
        self._color=None

    def global_hints(self, pos):
        if not self.hints_prepped:
            self.hints_prepped=1
            self.reset_hints()
        return self._global_hints[pos]

    def get_tunnelsqs(self, board):
        if not self._tunnelsqs:
            for g in self.orig_gates:
                if g[1]!=1:
                    continue
                self._tunnelsqs.update(get_tunnelsqs(board.rows, g[0]))
            self._tunnelsqs=set(self._tunnelsqs)
        return self._tunnelsqs


    def hints(self, pos):
        if not self.hints_prepped:
            self.reset_hints()
            self.hints_prepped=1
        return self._hints[pos]

    def remove_hint(self, pos, value):
        """"""
        if pos in config.hintmonpos:
            import ipdb;ipdb.set_trace();print 'ipdb!'
        self._hints[pos].remove(value)
        self.remove_hint(self.local2global(pos), value)

    def remove_global_hint(self, pos, value):
        """"""
        self._global_hints[pos].remove(value)
        self.remove_hint(self.global2local(pos), value)

    def intersect_hint(self, sq, hh):
        """if we have other info suggesting hints at pos are hh, take the intersection."""
        if not self.hints_prepped:
            self.reset_hints()
            self.hints_prepped=1
        #~ self._hints[sq]=self._hints[sq].intersection(hh)
        pos=self.local2global(sq)
        #~ self._global_hints[pos]=self._global_hints[pos].intersection(hh)
        #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        #~ bad=0
        #~ for h in hh:
            #~ if 'IN'==h[0]:
                #~ bad=1
                #~ break
            #~ if 'OUT'==h[1]:
                #~ bad=1
                #~ break
        #~ if bad:
            #~ for h in hh:
                #~ if 'IN'==h[0]:
                    #~ self._global_hints[pos]=[gh for gh in self._global_hints[pos] if gh[1]==h[1]]
                    #~ self._hints[sq]=[lh for lh in self._hints[sq] if lh[1]==h[1]]
                #~ if 'OUT'==h[1]:
                    #~ self._global_hints[pos]=[gh for gh in self._global_hints[pos] if gh[0]==h[0]]
                    #~ self._hints[sq]=[lh for lh in self._hints[sq] if lh[0]==h[0]]
                #~ if h in self._global_hints[pos]:
                    #~ self._global_hints[pos].remove(h)
                    #~ self._hints[sq].remove(h)
        #~ else:
        self._hints[sq]=self._hints[sq].intersection(hh)
        self._global_hints[pos]=self._global_hints[pos].intersection(hh)



    def intersect_enter_hint(self, sq, hh):
        """for sq sq, cancel entries which dont match the entries in hh."""

        if not self.hints_prepped:
            self.reset_hints()
            self.hints_prepped=1
        pos=self.local2global(sq)
        if self.kind=='pararooms':
            from_outside_dvs=[dv for dv in range(4) if add(sq, dv+2) not in self.sqs]
        else:
            from_outside_dvs=[dv for dv in range(4) if add(sq, dv+2) not in self.allsqs]
        okwaysin=[]
        #~ if self.hashid=='bfb08f4204ceecf84767e77869cabce5x009x000':
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        for h in hh:
            if h[0]=='OUT':
                okwaysin.extend(from_outside_dvs)
                continue
            if h[0]=='IN':
                #~ okwaysin.append(h[1])
                okwaysin.extend(from_outside_dvs)
                continue
            okwaysin.append(h[0])
        okwaysin=list(set(okwaysin))
        newh=set([gh for gh in self._global_hints[pos] if gh[0] in okwaysin])
        if not newh and self._global_hints[pos]:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            print 'promoting cause of a conflict between the rooms entry',pos
            return pos
        self._global_hints[pos]=newh
        self._hints[sq]=newh.copy()

    def intersect_exit_hint(self, sq, hh):
        """for sq sq, cancel entries which dont match the entries in hh."""

        if not self.hints_prepped:
            self.reset_hints()
            self.hints_prepped=1
        pos=self.local2global(sq)
        if self.kind=='pararooms':
            to_outside_dvs=[dv for dv in range(4) if add(sq, dv) not in self.sqs]
        else:
            to_outside_dvs=[dv for dv in range(4) if add(sq, dv) not in self.allsqs]
        okwaysout=[]
        #~ if self.hashid=='bfb08f4204ceecf84767e77869cabce5x009x000':
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        for h in hh:
            if h[1]=='OUT':
                okwaysout.extend(to_outside_dvs)
                continue
            if h[0]=='IN':
                okwaysout.append(h[1])
                continue
            okwaysout.append(h[1])
        okwaysout=list(set(okwaysout))
        newh=set([gh for gh in self._global_hints[pos] if gh[1] in okwaysout])
        if not newh and self._global_hints[pos]:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            print 'promoting cause of a conflict between the rooms-exit',pos
            return pos
        self._global_hints[pos]=newh
        self._hints[sq]=newh.copy()

    def intersect_global_hint(pos, gh):
        if not self.hints_prepped:
            self.reset_hints()
            self.hints_prepped=1
        self._global_hints[pos]=self._global_hints[pos].intersection(gh)
        sq=self.global2local(pos)
        self._hints[sq]=self._global_hints[sq].intersection(hh)

    def reset_hints(self):
        """set hints, global hints to the default (physical)

        global hints and hints should never be modified directly.  they should just be modified by
        the remove_global_hint(pos, hint) function.  or the local version.  both of these maintian the other one
        """
        self._global_hints={}
        self._hints={}
        for sq in self.sqs:
            outs=[dv for dv in range(4) if add(sq, dv) in self.allsqs]
            pos=self.local2global(sq)
            self._hints[sq]=set()
            self._global_hints[pos]=set()
            for o in outs:
                for i in outs:
                    if o==i:
                        continue
                    i=(i+2)%4
                    self._global_hints[pos].add((i,o))
                    self._hints[sq].add((i,o))
        for gsq, ns in self.gates:
            outs=[dv for dv in range(4)]
            outs.append('OUT')
            pos=self.local2global(gsq)
            self._hints[gsq]=set()
            self._global_hints[pos]=set()
            for o in outs:
                for i in outs:
                    if o==i:continue
                    if i=='OUT':
                        continue
                    else:
                        i=(i+2)%4
                    self._global_hints[pos].add((i,o))
                    self._hints[gsq].add((i,o))

    def recalc(self):
        """does NOT fix hints!  so watch out for that!"""
        self.fix_offsets()
        self.sqs=set([(pos[0]-self.xoffset,pos[1]-self.yoffset) for pos in self.orig_sqs])
        self.gatesqs=set([(g[0][0]-self.xoffset,g[0][1]-self.yoffset) for g in self.orig_gates])
        self.gates=set([((g[0][0]-self.xoffset,g[0][1]-self.yoffset),g[1]) for g in self.orig_gates])
        self.allsqs=set()
        self.allsqs.update(self.sqs)
        self.allsqs.update(self.gatesqs)
        self.orig_allsqs=set()
        self.orig_allsqs.update([g[0] for g in self.orig_gates])
        self.orig_allsqs.update([sq for sq in self.orig_sqs])
        self.orig_gatesqs=set()
        self.orig_gatesqs.update(g[0] for g in self.orig_gates)
        self.req_ct=len([g for g in self.gates if g[1]==1])
        self.opt_ct=len([g for g in self.gates if g[1]!=1])
        self.gsq_ct=len(self.gates)
        self.initrows()
        #~ self.initrows2()
        self.rehash()
        self.makekey()
        self.external_hints={}
        self._tunnelsqs=set([])

    def initrows2(self):
        row=[1]*self.width
        self.rows=[row[:] for r in range(self.height)]
        for sq in self.allsqs:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            self.rows[sq[1]][sq[0]]=0

    def initrows(self):
        #~ self.initrows2()
        """actually create .rows - before this it's empty, and the room just consists of a list of sqs and gates."""
        self.rows=[]
        for yy in range(self.height):
            row=[]
            for xx in range(self.width):
                if (xx,yy) in self.allsqs:
                    row.append(0)
                #~ elif p in self.gatesqs:
                    #~ row.append(0)
                else:
                    row.append(1)
            self.rows.append(row)

    def has_sol(self,target_gatesq=None,timelimit=None,toplevel=False,absolute=False,use_cache=True,debug=False):
        return self.get_all_sols(timelimit=timelimit,toplevel=toplevel,use_cache=use_cache,getone=True)

    def easy_solve_room(self):
        """
        easily detect if the room has no solutions, or whether it has trivial solutions

        res is [] for no solutions,
        or list of solutions,
        each s is:
            [sg,indv,[path],[covered],end]
        """
        have_res=False
        res=None
        if self.opt_ct==self.gsq_ct:
            if not self.sqs:
                #no sqs, but all reqs; just fill in the reqs!
                have_res=True
                sgs=[]
                for gsq in self.gatesqs:
                    if self.isopt(gsq):
                        sg=(gsq,'skip',(),(), gsq)
                        sgs.append(sg)
                res=all_permutations(sgs)
        elif len(self.gatesqs)==0:
            if self.sqs:
                res=[]
                have_res=True
            else:
                res=[]
                have_res=True
                print 'should never get here!'
        #if not, then break down the subrooms and return their res.
        elif self.opt_ct==0:
            if self.req_ct%2!=0:
                res=[]
                have_res=True
        #dont create internal alleys!
        else:
            for sq in self.sqs:
                neighbors=getopendvs(self.rows,sq)
                if len(neighbors)<2:
                    res=[]
                    have_res=True
                    #~ print 'bad room! has internal alleys at !',sq
                    #~ print self
        return have_res,res

    def get_all_sols(self,timelimit=None,toplevel=False,use_cache=True,getone=False, hints=None, source=None):
        """
        returns all sols.
            """
        global g_allsols_cache, g_hassols_cache
        from simpleroom import g_allsols_cache, g_hassols_cache
        import simpleroom
        if toplevel and len(g_allsols_cache)>30000:print 'clear allsols',len(g_allsols_cache);simpleroom.g_allsols_cache={}
        if toplevel and len(g_hassols_cache)>20000:print 'clear',len(g_hassols_cache);simpleroom.g_hassols_cache={}
        if use_cache:
            if getone:
                if self.key in g_hassols_cache:
                    config.hashit+=1
                    return g_hassols_cache[self.key]
                else:
                    config.hasmiss+=1
                if self.key in g_allsols_cache:
                    res=g_allsols_cache[self.key]
                    #be careful about this.  all_sols is not abstract or pure.
                    #only really return true if the thing really has one.
                    if res and res!='timeout':
                        return True
                    #otherwise pass through
            else:
                #getone is already checked, in has_sol.
                if self.key in g_allsols_cache:
                    config.allhit+=1
                    return copysols(g_allsols_cache[self.key])
                else:
                    config.allmiss+=1
        if toplevel:
            self.set_timeout(timelimit, source=source)
        if time.time()>self.timeout:
            return 'timeout'
        have_res,res=self.easy_solve_room()
        if not have_res:
            res=self.all_breakdown(toplevel=toplevel,use_cache=use_cache,getone=getone)
        if use_cache and not self.used_external_hint:
            if getone:
                if res=='timeout':
                    if toplevel:
                        #now we save timeouts for everything...  and hopefully fix them above.
                        g_hassols_cache[self.key]='timeout'
                    #do not save timeouts unless we are toplevel.  this is so that if an easy room shows up for the
                    #first time as a subroom, it would be stupid to have it be a timeout.
                    #this sucks though because if the same big room frequently comes up as a subroom
                    #it never gets saved as a timeout!  that could be a major problem.
                else:
                    if res:
                        g_hassols_cache[self.key]=True
                    else:
                        g_hassols_cache[self.key]=False
            else:
                if res=='timeout':
                    if toplevel and 0:
                        g_allsols_cache[self.key]='timeout'
                        #never save toplevel timeouts for all sols now.
                elif len(res)<1000:
                    g_allsols_cache[self.key]=copysols(res)
                    #have to do copysols again here - not sure.  which is really too bad.
        return res

    def fix_subroomres(self, su, subroomres):
        """cnoverts them to global"""
        offset_amount=(self.xoffset-su.xoffset,self.yoffset-su.yoffset)
        fixed_subroomreses=[]
        for sr in subroomres:
            fixed_subroomres=[]
            for srgate in sr:
                sstart,sindv,spath,srcovered,send=srgate
                newr=(offset(sstart,offset_amount),sindv,tuple(spath),tuple(offset(srcovered,offset_amount)),offset(send,offset_amount))
                fixed_subroomres.append(newr)
            fixed_subroomreses.append(fixed_subroomres)
        return fixed_subroomreses

    def all_breakdown(self,toplevel=False,use_cache=True,getone=False, debug=False):
        """
        #by this point, the room may just be a virtual one - made of a list of sqs & gates.  we need to actually make a row structure for it.

        if all sols timesout, but we have at least some sols, shouldn't we save at least that has_sol is true?

        """
        todo_gates=self.gates.copy()
        breakdown_solutions=set()
        bat=0
        while todo_gates:
            if time.time()>self.timeout:
                return 'timeout'
            thisgate=todo_gates.pop()
            startpos,ns=thisgate
            self.set(startpos)
            self.gatesqs.remove(startpos)
            self.gates.remove(thisgate)
            dvs=[n[0] for n in [(0,(1,0)),(1,(0,1)),(2,(-1,0)),(3,(0,-1))] if not self.rows[startpos[1]+n[1][1]][startpos[0]+n[1][0]]]

            if ns==1:
                #(if it's a req gate)
                target_blocked=False
                indv=None
                for dv in dvs:
                    if add(startpos,dv) in self.sqs:
                        indv=dv
                        break
                if indv==None:
                    pass
                else:
                    newdvs=[dv for dv in dvs if dv in [indv, (indv+1)%4, (indv-1)%4]]
                    if newdvs!=dvs:
                        dvs=newdvs
                    #removes wrong way dvs totally!
                    #adde the exception - it can occur when a room is reduced to just RR for example.  not sure what to do then.
                for dv in dvs:
                    dest=add(startpos,dv)
                    if dest in self.sqs:
                        if self.rows[dest[1]][dest[0]]==1:
                            target_blocked=True
                            break
            elif ns==2:
                dvs.append('skip')
            bat=0
            for indv in dvs:
                if indv=='skip':
                    su=self.make_subrooms_from_current_state()[0]
                    su.parent=self.hashid
                    res=su.get_all_sols(use_cache=use_cache,getone=getone)
                    if res=='timeout':
                        self.gates.add(thisgate)
                        self.gatesqs.add(startpos)
                        self.unset(startpos)
                        return res
                    if not res:
                        continue
                    if getone and res:
                        self.gates.add(thisgate)
                        self.gatesqs.add(startpos)
                        self.unset(startpos)
                        return True
                    this=(startpos,'skip',(),(),startpos)
                    offset_amount=(self.xoffset-su.xoffset,self.yoffset-su.yoffset)
                    for sr in res:
                        fixed_sr=()
                        for srgate in sr:
                            start,sindv,path,covered,end=srgate
                            newsr=(offset(start,offset_amount),sindv,tuple(path),tuple(offset(covered,offset_amount)),offset(end,offset_amount),)
                            fixed_sr=fixed_sr+(newsr,)
                        fixed_sr=(this,)+fixed_sr
                        breakdown_solutions.add(fixed_sr)
                    continue
                continuations=self.go_until_deadend_with_path(startpos,indv,[])
                if continuations=='timeout':
                    self.gates.add(thisgate)
                    self.gatesqs.add(startpos)
                    self.unset(startpos)
                    return 'timeout'
                for path,covered,stop in continuations:
                    for g in self.gates:
                        if g[0]==stop:
                            endgate=g
                            break
                    self.gatesqs.remove(stop)
                    self.gates.remove(endgate)
                    #I have made my move.  if room is done, return true.
                    #if not done, try to solve my subrooms.

                    self.set_many(covered)
                    subrooms=self.make_subrooms_from_current_state()
                    #it sucks that this makes them all... it should just make them one at a time.  save a lot of work on big rooms.
                    #90% of the time the smallest subroom is illegal
                    #restore things to normal now; i made it out, and now the solution is up to the subrooms.
                    self.gates.add(endgate)
                    self.gatesqs.add(stop)
                    self.unset_many(covered)
                    initial_gate_exit=(startpos,indv,tuple(path),tuple(covered),stop,)
                    partial_solutions=((initial_gate_exit,),)
                    subrooms.sort(key=lambda x:len(x.gatesqs))
                    subrooms_ok=True
                    #actually the permut stuff is slightly off.  we should find all permutations of sols within a room, not just perms of subrooms .
                    if time.time()>self.timeout:
                        self.gates.add(thisgate)
                        self.gatesqs.add(startpos)
                        self.unset(startpos)
                        return 'timeout'
                    subrooms_ok=True
                    subroomreses={}
                    for su in subrooms:
                        if time.time()>self.timeout:
                            self.gates.add(thisgate)
                            self.gatesqs.add(startpos)
                            self.unset(startpos)
                            return 'timeout'
                        subroomres=su.get_all_sols(toplevel=False,use_cache=use_cache,getone=getone)
                        #SHOULD use cache here - just temp
                        if subroomres=='timeout':
                            self.gates.add(thisgate)
                            self.gatesqs.add(startpos)
                            self.unset(startpos)
                            #resetting this stuff IS necessary!
                            return 'timeout'

                            #this is a bit weird.  if one subroom times out it doesn't mean the others won'1!  it's still possible
                            #to get negative solutions from this point on - but no positive.
                        #this res should be put in terms of the outer room, not this guy's room.
                        #su's got absolute x,yoffsets, same as parent.  but sols are coming in su's coord system.  to convert to parent
                        if getone and subroomres:
                            continue
                        if not subroomres:
                            #that is, only if room definitely doesnt have a sol.
                            subrooms_ok=False
                            break
                        subroomreses[su.hashid]=self.fix_subroomres(su, subroomres)
                    if not subrooms_ok:
                        #if this set of subrooms doesn't work just die.  none of the others will work either.
                        continue
                    if getone:
                        self.gates.add(thisgate)
                        self.gatesqs.add(startpos)
                        self.unset(startpos)
                        return True
                    #for each subroom order, choose one solution.  then make one sol out of all the perms of that.
                    if subrooms:
                        aa=self.all_orderings_of_subroomreses(subroomreses)
                        #and here we make all permutations of all the subrooms.
                        including_this_subroom_partials=set()
                        for partial in partial_solutions:
                            for ii,a in enumerate(aa):
                                if ii%128==0 and time.time()>self.timeout:
                                    self.gates.add(thisgate);self.gatesqs.add(startpos);self.unset(startpos);return 'timeout'
                                if a=='timeout':
                                    self.gates.add(thisgate)
                                    self.gatesqs.add(startpos)
                                    self.unset(startpos)
                                    return 'timeout'
                                combined=tuple(partial[:])+tuple(a[:])
                                including_this_subroom_partials.add(combined)
                        partial_solutions=including_this_subroom_partials
                    #now you are done with this first stop/covered, are at another exit, and no subroom has failed.  so, good on ya!
                    if getone:
                        self.gates.add(thisgate)
                        self.gatesqs.add(startpos)
                        self.unset(startpos)
                        return True
                    breakdown_solutions.update(partial_solutions)
                    if breakdown_solutions:
                        g_hassols_cache[self.key]=True
            self.gates.add(thisgate)
            self.gatesqs.add(startpos)
            self.unset(startpos)
        if getone:
            if not breakdown_solutions:
                return False
        return list(breakdown_solutions)

    def check_sol(self, sol):
        covered_pos=set()
        for sa in sol:
            start,_,_,covered,_=sa
            covered_pos.update(covered)
            covered_pos.add(start)
        if len(covered_pos)!=len(self.orig_allsqs):
            return False
        return True

    def all_orderings_of_subroomreses(self, srr):
        """nasty"""
        #choose one sol from each room.  then use permutations_with_repeats.
        scs=all_permutations_of_sol_choices(srr)
        #scs is a list of dicts.  each dict is hashid -> chosen sol for this time.
        halfscs=len(scs)/2
        for ii,sc in enumerate(scs):
            if ii%32==0:
                if ii<halfscs and time.time()>self.timeout:
                    print 'aato',
                    yield 'timeout'
            #one sc is hashid->chosen sol.
            sol_part_counts={}
            for hashid,chosen_sol in sc.items():
                sol_part_counts[hashid]=len(chosen_sol)
            orderings=permutations_with_repeats(sol_part_counts)
            for o in orderings:
                #orderings is a list of ways to hit the subrooms
                counts={}
                thisres=()
                for hit in o:
                    dep=counts.get(hit,0)
                    thisres=thisres+(tuple(sc[hit][dep]),)
                    counts[hit]=dep+1
                yield thisres

    def go_until_deadend_with_path(self,startpos,indv,already_covered,already_path=None):
        """returns a list of (the place you stopped at, the squares covered to get there.)"""
        if time.time()>self.timeout:
            return 'timeout'
        if not already_path:
            already_path=[]
        endpos,covered,dvs,path=self.multimove_path(startpos,indv)
        total_covered=already_covered[:]
        total_covered.extend(covered)
        total_path=already_path[:]
        total_path.extend(path)
        res=[]
        okgates=set()
        for g in self.gates:
            okgates.add(g[0])

        skip_this=0
        #~ print okgates
        #~ for ii,og in enumerate(okgates):
            #~ for jj, oog in enumerate(okgates):
                #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                #~ if dist(og, oog)==1:

                    #~ skip_this=1
                    #~ break
            #~ if skip_this:
                #~ break
        #~ if skip_this:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            #~ print self.kind
        if endpos in self.gatesqs:
            #done!
            #if it's in a wrong gatesq, don't even bother adding it.
            bad=False
            #~ res.append([total_path,total_covered,endpos])
            if 1:
                #~ print 'passed kind',self.kind
                for c in total_covered:
                    for o in orth(c):
                        if o in okgates:
                            continue
                        if self.rows[o[1]][o[0]]==0:
                            nei=orth(o)
                            nc=0
                            for n in nei:
                                if self.rows[n[1]][n[0]]==0:
                                    nc+=1
                            if nc<2:
                                #~ print self
                                #~ import ipdb;ipdb.set_trace();print 'has alley!'
                                #~ if self.kind=='pararooms':
                                    #~ print self
                                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                                bad=True
                                break
                    if bad:break
            if bad:
                #print 'skip.'
                #~ if len(self.allsqs)>35:
                    #~ print self
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
                pass
            else:
                res.append([total_path,total_covered,endpos])
        elif not dvs:
            #you blockaded yourself, not at an exit! oopsy
            #or, you violated a hint.  no dvs either.
            pass
        else:
            #stopped with two choices, but not at a gate.  go on.
            for dv in dvs:
                thisres=self.go_until_deadend_with_path(endpos,dv,total_covered,total_path)
                if thisres=='timeout':
                    self.unset_many(covered)
                    return 'timeout'
                res.extend(thisres)
        self.unset_many(covered)
        return res

    def obeys_enter_hint(self, sq, dv, src):
        """i am entering sq by dv dv, is it legal according to self.external_hints (which are poshints)"""
        pos=self.local2global(sq)
        if pos in self.external_hints:
            eh=self.external_hints[pos]
            if not eh:
                return True
            for e in eh:
                if e[0]==dv:
                    return True
            self.used_external_hint=1
            return False
        else:
            return True

    def obeys_exit_hint(self, sq, dv, src):
        """i am leaving sq in dv dv, is it legal according to self.external_hints (which are poshints)"""
        #~ return True
        pos=self.local2global(sq)
        if pos in self.external_hints:
            eh=self.external_hints[pos]
            if not eh:
                return True
            for e in eh:
                if e[1]==dv:
                    return True
            self.used_external_hint=1
            return False

        else:
            return True


    def fastmove(self,sq,dv):
        """go in a straight line.  return last position, plus all squares covered.  at the end, current position is also included in list of covereds."""
        next=add(sq,dv)
        covered=[]
        res=True
        while self.rows[next[1]][next[0]]==0:
            if not self.obeys_exit_hint(sq, dv, 'fm'):
                return sq, covered, False
            sq=next
            covered.append(sq)
            next=add(sq,dv)
            if sq in self.gatesqs:
                if not self.obeys_enter_hint(sq, dv, 'fme'):
                    res=False
                break
        return sq,covered, res

    def multimove_path(self,sq,dv):
        """move til you got a choice.  then return where you at, what you covered, and next dvs.
        returns you with sq and history already set."""
        multicover=[]
        path=[]
        dvs=None
        while 1:
            if not self.obeys_exit_hint(sq, dv,'mm'):
                break
            path.append(dv)
            sq,covered, was_ok=self.fastmove(sq,dv)
            multicover.extend(covered)
            self.set_many(covered)
            if not was_ok:
                break
            if sq in self.gatesqs:
                dvs=[]
                break
            #~ dvs=[n for n in [0,1,2,3] if self.isopen(add(sq,n))]
            dvs=[]
            if self.rows[sq[1]][sq[0]+1]==0:
                dvs.append(0)
            if self.rows[sq[1]+1][sq[0]]==0:
                dvs.append(1)
            if self.rows[sq[1]][sq[0]-1]==0:
                dvs.append(2)
            if self.rows[sq[1]-1][sq[0]]==0:
                dvs.append(3)
            #if there are multiple choices next...
            if len(dvs)!=1:
                break
            dv=dvs[0]
        return sq,multicover,dvs,path

    #~ def make_leftover_subrooms2(self,externalrows,externalendpos,include_bad=False):


    def make_leftover_subrooms(self,externalrows,externalendpos):
        """assume you are in a pristine state; based on the given external rows, return subrooms of self minus external

        so, make internal rows reflect externalrows, then call (make from current state), then unset everything again.
        also, don't return a room that touches the endpos - from the subroommaker POV, endpos will
        just be a normal filled in square, though, so send it along so the orth call can trigger a fail
        it hits it.
        ."""
        #~ oldrows=[r[:] for r in self.rows]
        restore={}
        for sq in self.allsqs:
            ori=self.local2global(sq)
            if externalrows[ori[1]][ori[0]] !=self.rows[sq[1]][sq[0]]:

                restore[sq]=self.rows[sq[1]][sq[0]]
                self.rows[sq[1]][sq[0]]=externalrows[ori[1]][ori[0]]
        endpos=(externalendpos[0]-self.xoffset,externalendpos[1]-self.yoffset)
        subrooms=self.make_subrooms_from_current_state(endpos=endpos)
        for sq, v in restore.items():
            self.rows[sq[1]][sq[0]]=v
        #restore!
        #~ if self.rows!=oldrows:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        #~ self.rows=oldrows
        return subrooms

    def make_subrooms_from_current_state(self,endpos=None,include_bad=False):
        """examine the current state of the room; make subrooms out of it.
        usually this is called after doing one possible gate entry & exit; that might have split the board.
        #hm, gate entry & exit should at least remember if you saw open squares on either side - if just on one side, don't even need to call this.

        uses current rows, opt, req, xoffset, yoffset.  doesn't modify sqs, gates, gatesqs.

        it might be a good idea to make this into a generator?  hmm...
        """
        st=time.time()
        subrooms=[]

        killer=None
        if not include_bad:
            killer=endpos

        remaining=[]
        x,y=len(self.rows[0]),len(self.rows)
        for yy in range(y):
            for xx in range(x):
                if self.rows[yy][xx]==0:
                    remaining.append((xx,yy))
        remaining=set(remaining)
        while remaining:
            pos=remaining.pop()
            sqs=set()
            tocheck=set([pos])
            res=True
            while tocheck:
                this=tocheck.pop()
                #~ done.add(this)
                sqs.add(this)
                for pos in [(this[0]+1,this[1]),(this[0]-1,this[1]),(this[0],this[1]+1),(this[0],this[1]-1),]:
                    if pos in sqs:
                        continue
                    if self.rows[pos[1]][pos[0]]==0:
                        tocheck.add(pos)
                    if pos ==killer:
                        res=False
                #it's stupid to break, cause we aren't ust looking for one subroom.  we might as well
                #keep flooding, so we can eliminate more sqs later.
            gates=set()
            remaining=remaining.difference(sqs)
            if not res:
                continue
            #prepare GLOBAL sqs & gates.
            for sq in sqs:
                if self.isopt(sq):
                    gates.add((self.local2global(sq),2))
                elif self.isreq(sq):
                    gates.add((self.local2global(sq),1))
            sqs=[(s[0]+self.xoffset,s[1]+self.yoffset) for s in sqs]
            for g in gates:
                sqs.remove(g[0])
            subroom=Room(sqs, gates, usage=self.kind+'-subroom',kind='subroom',timeout=self.timeout, levelnum=self.levelnum)
            subrooms.append(subroom)
        #~ print 'mk subrooms took %0.6f'%(time.time()-st)
        return subrooms

    def modify_hints_based_on_allsols(self):
        """called manually when setting up initial room sols
        not called as part of it, because otherwise all the subrooms would do it and that would be useless.

        if solved, then setup hints.  at the end up that back to self.hints
        it just looks at the remaining sols and updates the room's _global_hints and _hints.
        nothing is cancelled, just bookkeeping.
        """
        #~ if self.hashid=='92580481c330e7057171d5f5b0f5ba84x003x006':
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
        if self.all_sols is None or self.all_sols=='timeout':
            #should restore all hints!
            #untested, or timeout so we know nothing
            self.reset_hints()
            return
        if self.all_sols==[]:
            #has no sol.  so start/end must be here.
            self.reset_hints()
            return
        hints={}
        for sq in self.sqs:
            hints[sq]=set()
        for gsq in self.gatesqs:
            hints[gsq]=set()
        for s in self.all_sols:
            for sg in s:
                start,sindv,path,covered,end=sg
                covered=('IN',)+(start,)+covered+('OUT',)
                if start==end:
                    hints[start].add(('OUT','OUT'))
                else:
                    for ii,sq in enumerate(covered):
                        if sq=='IN':
                            continue
                        if sq=='OUT':
                            continue
                        indv=makevec2(covered[ii-1],covered[ii])
                        outdv=makevec2(covered[ii],covered[ii+1])
                        hints[sq].add((indv,outdv))

        for sq in self.sqs:
            #~ print self.hints(sq)
            #~ print hints[sq]
            #~ print self._hints[sq]
            bad=self.intersect_hint(sq, hints[sq])
            #~ if len(self.all_sols)==1:
                #~ if len(self._hints[sq])!=1:
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            if bad:return 1
        for gsq in self.gatesqs:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            bad=self.intersect_enter_hint(gsq, hints[gsq])
            if bad:return bad
            #should return the actual bad sq - it may be better!
            bad=self.intersect_exit_hint(gsq, hints[gsq])
            if bad:return bad
            #~ if len(hints[gsq])==1:
                #~ if len(self._hints[gsq])!=1:
                    #~ import ipdb;ipdb.set_trace();print 'ipdb!'


    def adopt_global_hints(self,board):
        """adjusts a rooms' global hints, based on the board's global hints?

        we should also check if the sols are legal or not now! wtf.
        """
        global_hints={}
        for sq in self.allsqs:
            self.intersect_hint(sq, board.global_hints[self.local2global(sq)])
        return
        #~ for pos,hints in self.raw_global_hints.items():
            #~ bad=False
            #~ for il in board.ilrooms:
                #~ if pos in il.orig_gatesqs:
                    #~ bad=True
            #~ if bad:
                #~ continue
            #not sure if this is necessary.  if i have hints, it should be ok.
            #~ orighints=hints
            #~ newhints=set()
            #~ for hint in hints:
                #~ if hint[0]=='IN':
                    #~ opendvs=board.getopendv_loc(pos)
                    #~ indvs=[(dv+2)%4 for dv in opendvs if dv!=hint[1]]
                    #~ for indv in indvs:
                        #~ newhints.add((indv,hint[1]))
                #~ elif hint[1]=='OUT':
                    #~ if hint[0]=='OUT':
                        #~ indvs=[n for n in [0,1,2,3] if add(pos,(n+2)%4) not in self.orig_allsqs and board.isopen(add(pos,(n+2)%4))]
                        #~ outdvs=[n for n in [0,1,2,3] if add(pos,n) not in self.orig_allsqs and board.isopen(add(pos,n))]
                        #~ for i in indvs:
                            #~ for o in outdvs:
                                #~ if (i+2)%4==o:
                                    #~ continue
                                #~ newhints.add((i,o))
                    #~ else:
                        #~ opendvs=board.getopendv_loc(pos)
                        #~ outdvs=[dv for dv in opendvs if dv != (hint[0]+2)%4]
                        #~ for outdv in outdvs:
                            #~ newhints.add((hint[0],outdv))
                #~ else:
                    #~ newhints.add(hint)
            #~ global_hints[pos]=newhints
        #~ self.global_hints=global_hints

    def set_timeout(self, timelimit, source):
        #~ if self.timeout:
            #~ return
        if timelimit:
            self.timeout=time.time()+timelimit
            #~ print 'manual tl',timelimit
        else:
            if source=='solve-all':
                pos_timelimit=getattr(config,self.kind+'_all_timelimit')
            elif source=='solve-all-fast':
                pos_timelimit=0.0001
            elif source=='solve-all-final':
                pos_timelimit=getattr(config,self.kind+'_final_timelimit')
            else:
                pos_timelimit=getattr(config,self.kind+'_timelimit')
            #~ print 'using timelimit.',pos_timelimit,self.hashid
            self.timeout=time.time()+pos_timelimit

    def pos2dvs(self,pos):
        return [n for n in [0,1,2,3] if self.isopen(add(pos,n))]

    def isopen(self,pos):
        return self.rows[pos[1]][pos[0]]==0

    def set(self,pos):
        self.rows[pos[1]][pos[0]]=2

    def set_many(self,many):
        for m in many:
            self.set(m)

    def unset(self,pos):
        self.rows[pos[1]][pos[0]]=0

    def unset_many(self,many):
        for m in many:
            self.unset(m)

    def rehash(self):
        #hash of a room is globally unique.
        key=str(self.orig_sqs)+str(self.orig_gatesqs)
        self.hashid=hashlib.md5(key).hexdigest()+'x%03dx%03d'%(self.xoffset,self.yoffset)
        #last thing added to stop two rooms from hashing to the same value...

    def fix_offsets(self):
        #be careful here - the only thing that's guaranteed right is orig_gates and orig_sqs.
        allsqs=set()
        allsqs.update([g[0] for g in self.orig_gates])
        allsqs.update([sq for sq in self.orig_sqs])
        miny=min(p[1] for p in allsqs)
        minx=min(p[0] for p in allsqs)
        maxy=max(p[1] for p in allsqs)
        maxx=max(p[0] for p in allsqs)

        self.xoffset=minx-1
        self.yoffset=miny-1

        #the width and height, including filled borders.
        self.width=maxx-minx+3
        self.height=maxy-miny+3

    def remove_poss(self, sqs=None, gates=None, gatesqs=None):
        if sqs:
            self.orig_sqs=self.orig_sqs.difference(set(sqs))
        if gates:
            self.orig_gates=self.orig_gates.difference(set(gates))
        if gatesqs:
            self.orig_gates=set([g for g in self.orig_gates if g[0] not in gatesqs])
        self.recalc()
        self.reset_hints()

    def add_poss(self, sqs=None, gates=None):
        """
        adding squares - they should be global!
        """
        if sqs:
            self.orig_sqs.update(set(sqs))
        if gates:
            self.orig_gates.update(set(gates))
        self.recalc()
        self.reset_hints()

    def isreq(self, sq):
        if sq not in self.gatesqs:
            return False
        if self.opt_ct==0:
            return True
        for g in self.gates:
            if g[0]==sq and g[1]==1:
                return True
        return False

    def check_tails(self):
        for ro in self.rows:
            if 2 in ro:
                return False
        return True

    def isopt(self,sq):
        if sq not in self.gatesqs:
            return False
        if self.req_ct==0:
            return True
        for g in self.gates:
            if g[0]==sq and g[1]!=1:
                return True
        return False

    def makekey(self):
        self.key=str(sorted(self.sqs))+str(sorted(self.gates))

    def global2local(self, pos):
        return (pos[0]-self.xoffset, pos[1]-self.yoffset)

    def local2global(self,pos):
        return (pos[0]+self.xoffset,pos[1]+self.yoffset)

    def make_connections(self):
        """prepare the sources, destinations set (of pos) for a room
        not sure what this is for now, not used.
        """
        return
        destinations={}
        sources={}
        for gsq in self.gatesqs:
            destinations[self.local2global(gsq)]=set()
            sources[self.local2global(gsq)]=set()
        if rm.all_sols=='timeout':
            return
        for sol in self.all_sols:
            for sa in sol:
                start,indv,path,covered,end=sa
                destinations[self.local2global(start)].add((self.local2global(end),tuple(path)))
                sources[self.local2global(end)].add((self.local2global(start),tuple(path)))
        self.sources=sources
        self.destinations=destinations

    @property
    def color(self):
        if not self._color:
            hsh=self.hashid
            #~ import ipdb;ipdb.set_trace()
            self._color=(int(hsh[:2],16),int(hsh[2:4],16),int(hsh[4:6],16))
        #so that it's easy to see later!
        return self._color

    def show(self,pos=None):
        poslist=pos
        if type(pos)==tuple :
            poslist=[pos]
            if type(pos[0])==tuple:
                poslist=[]
                for p in pos:
                    poslist.append(p)
        res=self.__repr__(poslist)
        print res

    @property
    def sa(self):
        self.show()
        """show all current sols"""
        if self.all_sols=='timeout':
            print 'timout.'
            return
        for ii,s in enumerate(self.all_sols):
            print 'SOL#:',ii
            for sg in s:
                start,indv,path,_,_=sg
                print start,'==>',path
            print ''

    @property
    def ss(self):
        self.save_all_sols()

    def __repr__(self,poslist=None):
        solstring=''
        if self.all_sols==None:
            solstring='not solved'
        elif self.all_sols==[]:
            solstring='no sols'
        elif self.all_sols=='timeout':
            solstring='timeout'
        else:
            solstring='has %d sols remaining'%len(self.all_sols)
        res='ROOM %s sqs=%d gates=%d %s\n'%(self.usage, len(self.sqs),len(self.gatesqs), solstring)
        if not poslist:
            poslist=[]
        for yy in range(len(self.rows)):
            row=''
            for xx in range(len(self.rows[0])):
                p=(xx,yy)
                if p in poslist:
                    row+='X'
                elif self.isopen(p):
                    if p in self.gatesqs:
                        if self.isopt(p):
                            row+='*'
                        elif self.isreq(p):
                            row+='R'
                    else:
                        row+='_'
                else:
                    try:
                        row+=str(self.rows[yy][xx])
                    except:
                        row+='1'
            res+=row+"\n"
        rcount,ocount=0,0
        for s,v in sorted(self.gates):
            #~ res+=str(s)
            if v==1:
                rcount+=1
            else:
                ocount+=1
        res+='R:%d, O:%d\n'%(rcount,ocount)
        return res

    def sh(self, extra_text=None):
        if not extra_text:extra_text=''
        fname='%s-hints-%s'%(self.hashid,extra_text)
        imgtext=fname+'-'+extra_text
        hintdict={}
        inouts={}

        for pos,hints in getattr(self,'_hints',{}).items():
            ins,outs=set(),set()
            for h in hints:
                #~ print h
                if h[0]=='IN':
                    continue
                if h[1]=='OUT':
                    continue
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
            #~ code=res2code(res)
            if len(ins)==1 and len(outs)==1:
                inouts[pos]=str(h[0])+str(h[1])
            #~ else:
                #~ hintdict[pos]=code

        imgtext+='undetermined %06d determined %06d'%(len(hintdict),len(inouts))
        pshow(rows=self.rows,fname=fname,imgtext=imgtext,inouts=inouts,worktype=self.levelnum)

    def remove_sol(self,s):
        self.all_sols.remove(s)
        if self.hashid==config.mon_hashid:
            import ipdb;ipdb.set_trace()
            print 'removing sol from room...'
        #~ if len(self.all_sols)==0:
            #~ import ipdb;ipdb.set_trace();print 'ipdb!'
            #~ print 'removed all sols!/'

    def ssh(self, board):
        """save subroom hints"""
        old_ghints=self._global_hints.copy()
        done_roomkeys=set()
        for sq in self.orig_allsqs:
            rms=board.pos2allrooms(sq)
            for rm in rms:
                if rm in done_roomkeys:
                    continue
                done_roomkeys.add(rm.key)
                if rm._global_hints:
                    for gp,rhs in rm._global_hints.items():
                        bad=[]
                        if gp not in self.global_hints:
                            continue
                        if rhs!=self.global_hints[gp]:
                            for gh in self.global_hints[gp]:
                                if gh not in rhs:
                                    bad.append(gh)

        self.sgh('with subroom contrib.')
        self.global_hints=old_ghints


    def sgh(self, extrafn=None):
        if not extrafn:
            extrafn=''
        fname='%s-ghints%s'%(self.hashid, extrafn)
        imgtext=fname
        hintdict={}
        inouts={}

        for pos,hints in self._global_hints.items():
            ins,outs=set(),set()
            pos=self.global2local(pos)
            for h in hints:
                #~ print h
                if h[0]=='IN':
                    continue
                if h[1]=='OUT':
                    continue
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
            #~ code=res2code(res)
            if len(ins)==1 and len(outs)==1:
                inouts[pos]=str(h[0])+str(h[1])
            #~ else:
                #~ hintdict[pos]=code
        imgtext+='undetermined %06d determined %06d'%(len(hintdict),len(inouts))
        pshow(rows=self.rows,fname=fname,imgtext=imgtext,inouts=inouts,worktype=self.levelnum)

    def check_gates_gatesqs(self):
        try:
            assert sorted(list([g[0] for g in self.gates]))==sorted(self.gatesqs)
        except:
            print 'gates',sorted(list(self.gates))
            print 'gatesqs',sorted(self.gatesqs)
            sys.exit()

    def make_gate_dict(self):
        special_dict={}
        if not self.gate_possibilities:
            return None
        possibility2color={}
        possibility2color[ANY]=(230,230,230)
        possibility2color[NONE]=(0,0,240)
        possibility2color[INOUT]=(130,130,0)
        possibility2color[INNONE]=(0,255,200)
        possibility2color[OUT]=(255,0,0)
        possibility2color[IN]=(0,255,0)
        possibility2color[OUTNONE]=(255,0,200)
        for gsq,possibility in self.gate_possibilities.items():
            special_dict[gsq]=possibility2color[possibility]
        return special_dict

    def save_gate_possibilities(self,method=None):

        special_dict=self.make_gate_dict()
        if not special_dict:
            return
        if not method:
            method=''
        fname='gate_possibilities%s%s'%(self.hashid,method)
        worktype=self.levelnum

        imgtext='forced gates'
        pshow(rows=self.rows,fname=fname,imgtext=imgtext,worktype=worktype,special_dict=special_dict)

    def save_all_sols(self,text=None,overwrite=False):
        if self.all_sols=='timeout':
            return
        for ii,sol in enumerate(self.all_sols):
            if text:
                imgtext=text
            else:
                imgtext=''
                text=''
            imgtext+='sol %02d'%(ii)
            fname='%s%s-sol%02d%s'%(self.kind,self.hashid,ii,text)
            self.save_sol(sol,imgtext=imgtext,fname=fname,overwrite=overwrite)

    def save_sol(self,sol,fname,imgtext=None,overwrite=False):
        inouts=make_room_inouts(self,sol)
        if not imgtext:
            imgtext=''
        for sa in sol:
            imgtext+='\n'+str(sa[0])
        worktype=self.levelnum
        pshow(rows=self.rows,fname=fname,overwrite=overwrite,imgtext=imgtext,inouts=inouts,worktype=worktype)

    @property
    def hh(self):
        pprint.pprint(self._hints)

    @property
    def gh(self):
        pprint.pprint(self._global_hints)

    def unclean(self):
        for r in self.rows:
            if 2 in r:
                return True
        return False

