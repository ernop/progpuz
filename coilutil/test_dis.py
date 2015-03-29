import dis

def add(pos,n):
    if (n%4)==0:
        return pos[0]+1,pos[1]
    if (n%4)==1:
        return pos[0],pos[1]+1
    if (n%4)==2:
        return pos[0]-1,pos[1]
    return pos[0],pos[1]-1

def orthgen(pos):
    for n in range(4):
        yield add(pos,n)
        
def orth(pos):
    res=[]
    for n in range(4):
        res.append(add(pos,n))
    return res
        
pos=(10,4)

dis.dis(orthgen)
dis.disassemble(orthgen)

#~ print range(40)