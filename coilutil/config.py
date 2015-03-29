#hmm how about this for a hint:  when doing get all continuations
#in reqrooms, you can't exit a reqgate that is an even number of gates away from you
#so you can't go next door.  but can skip 1 3 5 etc.

levelnum=0
levelnum='0053a'
levelnum=None
#~ levelnum=-19
#levelnum=0
one_sol=True
#one_sol=False
one_level=True
one_level=False
do_sol=0
do_one_hint=1
#this just checks the solpath as we go if we have the solpath file. should be no problem
check_all_sol_paths=0
load_hints=0
#this skips all nonsol starts.
force_all_sol_paths=1

no_save_when_check_all_sol=1
#~ do_sol=1
#PRUNING
debug_fork=0
debug_illegal4=0
use_illegal_4=0
check_hints=0
prune=1
better_prune=1
bump_prune=1
use_hash=0
really_mark_solved=1
prune_starts=0
#~ prune_starts=1
important_starts_first=1
timeout_starts_before=1
setup_initial_illegal=1
monitor_active=0
save_backtracks_every=1
save_backtracks_every=5000
save_hints_every=1
save_hints_every=10000000
save_bumps=0
save_trans_bumps=0
profile=0
hintmonpos=[(15,18)]
hintmonpos=[]
advanced_reverse_in_room=1

#options which may break stuff
skip_predetermined=1 #dont do getil4 when you are obeying a hint.
no_propagate_pararooms=0 #actually it's ok
skip_hints_within_illegal=01 #unknown whether this is really a problem or not!
skip_hints_on_ilsqs=1 #this at 1 should almost definitely cause problems.
skip_parent_hints_on_ilsqs=1 #0 seems ok, but not sure.
skip_hints_in_later_prune=1 #at 0 this should be bad too.
skip_prune_in_orig_illegal=1 #in normal prune
skip_remove_based_on_roomls=1 #this is dangerous at 0
skip_hintchecks_while_in_orig_illegal=1
disable_hints_in_starting_reqrm=1

do_target=0
targetx, targety, targetdv=10, 9, 3
if do_target:
    really_mark_solved=0
if not one_sol:
    really_mark_solved=0
forkmonx=26
forkmony=35
forkmonpos=(forkmonx,forkmony)
forkmonpos=None

monitor_changecount_number=3461
monitor_changecount_number=None
monitor_start=0
#~ monitor_start=1
mhintpos=None
#~ mhintpos=(31,28)
mon_hashid=None
mon_hashid='393c9c26df81bdb03d7930443e835aca,007,003'

#TIMING
LO=0.1
SH=.1
VLO=3

#CACHING
load_initial_illegal=0
load_allsols_pickle=0
load_hassols_pickle=0
load_global_hints_pickle=0
use_start_cache=0

pararooms_all_timelimit=LO
reqrooms_all_timelimit=LO
optrooms_all_timelimit=LO

#~ pararooms_final_timelimit=VLO
#~ reqrooms_final_timelimit=VLO
#~ optrooms_final_timelimit=VLO

#these are for get illegal
pararooms_timelimit=SH
reqrooms_timelimit=SH
optrooms_timelimit=SH
subroom_timelimit=SH
#DEBUGGING

#~ one_sol=1

forkmon_maxcuropen=60
forkmon_maxcuropen=None

have_reached_forkmon=None
multimovemonpos=None
prune_monitor_pos=(20,22)
prune_monitor_pos=None

targetpos=(targetx,targety)
target=(targetpos, targetdv)
monitored_start=target

know_target=0
known_target=(5,6)
known_dv=None
#~ badkey='[(2, 2), (2, 3), (3, 2), (3, 3)][((1, 3), 2), ((2, 1), 2), ((3, 4), 2), ((4, 2), 1)]'
badkey=None

check_cache_quality=0
do_ipdb=0

#RECORD KEEPING
one_level=0
save_valuable_sols=1
save_valuable_sols_minvalue=840
save_unsolved_counts=0
save_unsolved_every=1000
randomly_save_hints=0
save_backtracks=0

do_best_seen=1
abs_do_best_seen=0
scale=15
toshow_fields='submit one_sol \
mark_solved use_hash initial_check_rm_timelimit \
do_ipdb load_hassols_pickle load_allsols_pickle \
prune better_prune'.split()

toshow_fields=['one_level','skip_predetermined','use_illegal_4','prune','better_prune','bump_prune','check_hints','SH','LO',]

#GENERAL
live=False
submit=1
savestats=1
debug=False


#CALCULATED
if levelnum is None:
    live=True
    submit=True
else:
    live=False

if not live:
    submit=False

if levelnum==0:
    use_start_cache=0
    #~ save_unsolved_counts=0

if do_target or do_sol:
    debug_fork=0
    use_start_cache=0
    one_sol=1
    do_ipdb=1
    abs_do_best_seen=0
    save_unsolved_counts=0
    save_backtracks=1
    monitor_start=1
    target=(targetpos, targetdv)
    save_backtracks_every=1
    do_target=1

if do_sol:
    monitor_start=0
    one_level=0
    do_target=0

if profile:
    do_best_seen=0
    one_level=True
    use_start_cache=0
    do_ipdb=0
    save_unsolved_counts=0
    one_sol=1

if monitor_start:
    do_ipdb=1

if know_target:
    targetpos=known_target
    targetdv=known_dv

load_allsols_pickle=0
if levelnum<0 and levelnum is not None:
    one_sol=0
    one_level=1
    load_initial_illegal=0
    load_allsols_pickle=0
    load_hassols_pickle=0
    load_global_hints_pickle=0
    save_backtracks_every=1
    if do_target:
        debug_illegal4=1
        debug_fork=1
    use_start_cache=0

#FINAL CHANGES
#~ target=(targetpos,targetdv)
if do_target:
    really_mark_solved=0
mark_solved=really_mark_solved
do_ipdb=1
ZONE=0
#~ ZONE=1
btcount=0
hashit, hasmiss, allhit, allmiss=0,0,0,0
if levelnum is not None:
    try:
        int(levelnum)
        n=int(levelnum)
        b=''
    except:
        n=int(levelnum[:-1])
        b=levelnum[-1]
    levelnum='%04d%s'%(n,b)


#~ save_unsolved_counts=1
save_donestarts=1

#~ import ipdb;ipdb.set_trace()
#~ print 'one sol is:',one_sol

monitor_promotion=0
