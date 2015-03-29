import os
out=open("test.html",'w')
out.write('<body bgcolor=#343434>')
for i in os.listdir('Images7'):
    out.write('\n<br><img src=Images7/%s>'%(i))

out.close()