levelnum=258
import cPickle
illegalrooms=[]
for ii in [0,1]:
        if len(illegalrooms)>ii:
            iroom=illegalrooms[ii]    
        else:
            iroom=None
        would='illegals/illegal%05d-%d.pickle'%(int(levelnum),ii)
        print 'SAVING illegal! to',would
        cPickle.dump(iroom,open(would,'w'))