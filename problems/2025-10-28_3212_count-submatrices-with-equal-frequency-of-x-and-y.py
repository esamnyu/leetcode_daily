# LeetCode 3212: Count Submatrices With Equal Frequency of X and Y
# Date: 2025-10-28
# Difficulty: Medium
# Topics: Array, Matrix, Prefix Sum

'''
Given a 2D character matrix grid, where grid[i][j] is either 'X', 'Y', or '.', return the number of submatrices that contain:

grid[0][0]
an equal frequency of 'X' and 'Y'.
at least one 'X'.

 
Example 1:

Input: grid = [["X","Y","."],["Y",".","."]]
Output: 3
Explanation:


Example 2:

Input: grid = [["X","X"],["X","Y"]]
Output: 0
Explanation:
No submatrix has an equal frequency of 'X' and 'Y'.

Example 3:

Input: grid = [[".","."],[".","."]]
Output: 0
Explanation:
No submatrix has at least one 'X'.

 
Constraints:

1 <= grid.length, grid[i].length <= 1000
grid[i][j] is either 'X', 'Y', or '.'.


'''

class Solution:
    def numberOfSubmatrices(self, grid: List[List[str]]) -> int:
        