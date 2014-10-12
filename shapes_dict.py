from shapes import PENTOS

def set2dict(s,ii):
    return {sq:ii for sq in s} 

DICT_PENTOS={}
ii=97
for k,v in PENTOS.items():
    DICT_PENTOS[k]=set2dict(v, k.lower())
    ii+=1

PENTOS=DICT_PENTOS
F=DICT_PENTOS['F']
I=DICT_PENTOS['I']
L=DICT_PENTOS['L']
N=DICT_PENTOS['N']
P=DICT_PENTOS['P']
T=DICT_PENTOS['T']
U=DICT_PENTOS['U']
V=DICT_PENTOS['V']
W=DICT_PENTOS['W']
X=DICT_PENTOS['X']
Y=DICT_PENTOS['Y']
Z=DICT_PENTOS['Z']

#for ii,p in enumerate(PENTOS):
    #dp={spot:ii for spot in p}
    #DICT_PENTOS.append(dp)