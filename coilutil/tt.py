import time,random

rows=[]
rowlength=5
for n in range(rowlength):
    row=[]
    for m in range(rowlength):
        row.append(random.choice([0,1]))
    rows.append(row)
    
st=time.time()
res={}
for n in range(100):
    res[n]=[r[:] for r in rows]
    
rr=(time.time()-st)/1000
print '%0.9f per'%(rr)

