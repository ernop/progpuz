import os
out=open('hints.html','w')
for n in range(999):
    s='%04d'%n
    out.write('<br>'+str(n))
    for n in range(4,8):
        target='output/%s/hints%d-%s-DONE.png'%(s,n,s)
        
        if not os.path.exists(target):
            continue
        print target
        line='\n<img src=%s>'%(target)
        out.write(line)
out.close()