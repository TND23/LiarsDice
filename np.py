import numpy as np

b = np.array([(2,3), (4,5), (6,7)])
res = b / np.linalg.norm(b,axis=-1)[:,np.newaxis]
# a = sum(i for i,j in b)
# a1 = sum(j for i,j in b)
# ar = np.array([a,a1]).reshape(1,2)
# ar /= ar.sum(axis=1)[:,np.newaxis]
#print(res)
x  = [1,2,3,4,5,6,7,8]
for a,c in x:
    print(a)
    print(c)
# a = np.arange(0,27.,3).reshape(3,3)
# print(a)
# a /=  a.sum(axis=1)[:,np.newaxis]
# print(a)
