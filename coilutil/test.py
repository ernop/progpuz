import time
a=set([130400,132089123,1302339])
b=set(range(10000000))
st=time.time()
ct=10000
for n in range(ct):
    res=b.isdisjoint(a)
print '%0.7f'%(time.time()-st)

ct=10000
for n in range(ct):
    int=b.intersection(a)
print '%0.7f'%(time.time()-st)