from dataLoader import dataLoader
from branchAndPrice import branchAndPrice
from solveMIP import solveMIP
from datetime import datetime
import sys

# Extend default recursion limit to allow deeper copying (for larger instances)
sys.setrecursionlimit(10000)

for instance in []:
    data = dataLoader(filename='../instances/'+instance+'.xlsx')

    # Set solution file names
    solutionFilename = instance + '_' + datetime.now().strftime('%Y%m%d_%H%M')
    outputTreePickle = 'branchAndPrice_' + solutionFilename + '.pickle'

    # Solve by branch and price
    branchAndPrice(data=data,
                   outputTreePickle=outputTreePickle,
                   # printStatus=True,
                   # gapLimit = 1e-9,
                   # timeLimit = None, # Time limit in seconds
                   # reducedTreeSize = True, # Reduce size of tree by deleting unnecessary data
                   # resourceVec = ['TWMin', 'TWMin_g', 'TV'], # Resources used in the sub problem
                   # removeIllegalColumns = False, # Remove all illegal columns before solving a problem
                   # coverConstraint = '=', # Cover constraint. = or >=.
                   # partialCG = False, # Only solve SPs until one with neg red cost is found
                   # orderStrategy = 'random', # Strategy for choosing order of solving SP's
                   # partialCG_constructionHeuristic = False, # Only solve SPs until one with neg red cost is found in construction heuristic
                   # constructionHeuristic = 'CGartificialVariables', # Specify what construction heuristic to use
                   # labelExtensionLimits = [], # Increments in SP label extension limit
                   # SPSolutionsCount = 1, # Maximum number of SP solutions returned from one SPPRC iteration
                   # sizeLimit = None, # Limit size of tree
                   # CGOptimalityGapLimit=1e-9, # CG stop criterion optimality gap
                   # CGImprovementStepSize=1, # CG improvement criterion step size
                   # CGImprovementThreshold=1e-9, # CG improvement criterion threshold
                   # branchOnUpperBound=False, # Branch once CG finds objective value below tree upper bound
                   # branchingStrategy = 'xVars'
                   )
