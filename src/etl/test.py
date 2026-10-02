import math
import os
import random
import re
import sys
a = [[1,2,3],[4,5,6],[7,8,10]]
print(len(a))
print(len(a[0]))
def diagonalDifference(arr):
    # Write your code here
    l_r_diag_ = 0
    r_l_diag_ = 0
    k = len(arr)-1
    for i in range(len(arr)):
        l_r_diag_ += arr[i][i]
        r_l_diag_ += arr[k][i]
        k-=1
    return abs(l_r_diag_ - r_l_diag_) 
print(diagonalDifference(a))