import sys
sys.path.append('./classes')
from problem import Problem
from tree import Tree
from columns import Columns
from graph import Graph
from helpers import *
import inspect
import time

def branchAndPrice(data,
                   outputTreePickle=None,
                   printStatus=True,
                   gapLimit = 1e-9,
                   timeLimit = None, # Time limit in seconds
                   reducedTreeSize = True, # Reduce size of tree by deleting unnecessary data
                   resourceVec = ['TWMin', 'TWMin_g', 'TV'], # Resources used in the sub problem
                   removeIllegalColumns = False, # Remove all illegal columns before solving a problem
                   coverConstraint = '=', # Cover constraint. = or >=.
                   partialCG = False, # Only solve SPs until one with neg red cost is found
                   orderStrategy = 'random', # Strategy for choosing order of solving SP's
                   partialCG_constructionHeuristic = False, # Only solve SPs until one with neg red cost is found in construction heuristic
                   constructionHeuristic = 'CGartificialVariables', # Specify what construction heuristic to use
                   labelExtensionLimits = [], # Increments in SP label extension limit
                   SPSolutionsCount = 1, # Maximum number of SP solutions returned from one SPPRC iteration
                   sizeLimit = None, # Limit size of tree
                   CGOptimalityGapLimit=1e-9, # CG stop criterion optimality gap
                   CGImprovementStepSize=1, # CG improvement criterion step size
                   CGImprovementThreshold=1e-9, # CG improvement criterion threshold
                   branchOnUpperBound=False, # Branch once CG finds objective value below tree upper bound
                   branchingStrategy = 'xVars'
                   ):
    '''Branch-and-Price algorithm for solving the roster problem. If a tree
    pickle filename is given, branch-and-price continues on the given tree.
    '''

    '''Initializations'''
    # Start time
    refTime = time.time()
    # Start time for initializations
    start = time.time()
    # Set margin for numerical error
    epsilon = 1e-9
    terminate = False
    # Retrieve inputs to branch and price function
    # Array to store configuration
    configuration = {}
    # Retrieve function arguments
    frame = inspect.currentframe()
    arguments, _, _, values = inspect.getargvalues(frame)
    # Save all arguments relevant
    for argument in arguments:
        if argument not in ['data', 'outputTreePickle']:
            configuration[argument] = values[argument]

    # Problem k to be solved
    k = 0
    # Initialize branch-and-bound tree
    tree = Tree(configuration, refTime)
    # Initialize columns and graphs
    graphs = dict.fromkeys(employee for employee in data['Employees'])
    for employee in data['Employees']:
        graphs[employee] = Graph(data=data, employee=employee)
    stop = time.time()
    tree.times['Branch and price']['Initializations'] += stop - start
    start = time.time()
    # Generate initial columns
    columns = Columns(data=data, graphs = graphs,
                      constructionHeuristic = constructionHeuristic,
                      printStatus = printStatus,
                      orderStrategy = orderStrategy,
                      partialCG_constructionHeuristic = partialCG_constructionHeuristic,
                      coverConstraint = coverConstraint,
                      removeIllegalColumns = removeIllegalColumns,
                      resourceVec = resourceVec)
    stop = time.time()
    tree.times['Branch and price']['Construction heuristic'] += stop - start
    start = time.time()
    # Define root problem
    rootProblem = Problem(ID=k, columns=columns, graphs=graphs, data=data,
                          coverConstraint=coverConstraint)
    # Add root problem to tree
    tree.addProblem(problem=rootProblem)
    stop = time.time()
    tree.times['Branch and price']['Initializations'] += stop - start
    tree.times['Total'] += time.time() - tree.times['refTime']
    tree.times['refTime'] = time.time()

    '''Main Loop'''
    while not terminate:
        # Select problem k from unprocessedProblems
        Pk = tree.unprocessedProblems[k]
        # If required and not root problem, remove illegal columns from Pk
        if k > 0 and removeIllegalColumns:
            # Remove from columns object
            removedColumnNumbers = Pk.columns.removeIllegalColumns(data = data)
            # Delete all removed columns from master problem object
            Pk.masterProblem.delVariable(['lambda({},{})'.format(e, k) for e in removedColumnNumbers for k in removedColumnNumbers[e]])
        # Prepare timing for solving problem k
        tree.times['Total'] += time.time() - tree.times['refTime']
        tree.times['refTime'] = time.time()
        # Check if time limit is reached while not already terminated
        if timeLimit != None and tree.times['Total'] > timeLimit:
            if printStatus:
                print('Time limit {:.0f} s reached. Process terminated.'.format(timeLimit))
            savePickle(tree, outputTreePickle)
            # Terminate function
            return
        # Solve problem k
        Pk.solve(data = data, epsilon = epsilon, partialCG = partialCG,
                 orderStrategy = orderStrategy,
                 partialCG_constructionHeuristic = partialCG_constructionHeuristic,
                 labelExtensionLimits=labelExtensionLimits,
                 SPSolutionsCount=SPSolutionsCount,
                 removeIllegalColumns = removeIllegalColumns,
                 CGOptimalityGapLimit=CGOptimalityGapLimit,
                 CGImprovementStepSize=CGImprovementStepSize,
                 CGImprovementThreshold=CGImprovementThreshold,
                 branchOnUpperBound=branchOnUpperBound,
                 treeUpperBound=tree.upperBoundProblem.upperBound,
                 times = tree.times,
                 resourceVec = resourceVec,
                 timeLimit=timeLimit)
        stop = time.time()

        tree.times['Total'] += time.time() - tree.times['refTime']
        tree.times['refTime'] = time.time()
        # Check if time limit is reached while not already terminated
        if timeLimit != None and tree.times['Total'] > timeLimit:
            if Pk.processed:
                # Remove master problem and reduce size
                Pk.masterProblem = None
                Pk.reduceSize(data = data)
                # Move problem k from unprocessedProblems to processedProblems
                tree.processedProblems[k] = tree.unprocessedProblems.pop(k)
            if printStatus:
                print('Time limit {:.0f} s reached. Process terminated.'.format(timeLimit))
            savePickle(tree, outputTreePickle)
            # Terminate function
            return

        # Move problem k from unprocessedProblems to processedProblems
        tree.processedProblems[k] = tree.unprocessedProblems.pop(k)

        # If Pk infeasible, or without potential of improvement
        if not Pk.feasible or Pk.lowerBound > tree.upperBoundProblem.upperBound:
            # Prune node
            Pk.pruned = True
            # Delete master problem in node
            Pk.masterProblem = None

        # Else if the final solution is integer
        elif Pk.integer:
            # Update upper bound if better solution found
            if Pk.upperBound < tree.upperBoundProblem.upperBound:
                tree.upperBoundProblem = Pk
                # Prune all unprocessed problem with lower bound above new upper bound
                tree.pruneOnUpperBound()
            # Prune node (integer)
            Pk.pruned = True
            # Delete master problem in node
            Pk.masterProblem = None

        # Otherwise, update upper bound if Pk had a better integer solution than
        # the current upper bound problem and branch problem
        else:
            if Pk.upperBound and Pk.upperBound < tree.upperBoundProblem.upperBound:
                tree.upperBoundProblem = Pk
                # Prune all unprocessed problem with lower bound above new upper bound
                tree.pruneOnUpperBound()
            start = time.time()
            # Branch the problem
            tree.branch(problem = Pk, branchingStrategy = branchingStrategy, data = data)
            stop = time.time()
            tree.times['Branch and price']['Branch'] += stop - start
            tree.times['Total'] += time.time() - tree.times['refTime']
            tree.times['refTime'] = time.time()

        # Reduce size of problem by removing unnecessary attributes
        Pk.reduceSize(data)

        # Update lower bound and optimality gap
        tree.calculateLowerBound()
        tree.calculateOptimalityGap()

        tree.times['Total'] += time.time() - tree.times['refTime']
        tree.times['refTime'] = time.time()
        # Check termination criterion
        if tree.terminationCriterion(sizeLimit=sizeLimit, gapLimit = gapLimit):
            terminate = True
            tree.complete = True
            savePickle(tree, outputTreePickle)
            # Terminate function
            return

        # Else: update k according to search strategy
        else:
            # If no integer solution found (no UBD): use depth first search
            if tree.upperBoundProblem.upperBound == float('inf'):
                searchStrategy = 'DepthFirst_Up'
            # Else: use best first search
            else:
                searchStrategy = 'BestFirst'
            # Search and store time
            start = time.time()
            k = tree.search(searchStrategy)
            stop = time.time()
            tree.times['Branch and price']['Search'] += stop - start
            tree.times['Total'] += time.time() - tree.times['refTime']
            tree.times['refTime'] = time.time()

            if printStatus:
                nProcessedProblems = len(tree.processedProblems)
                if tree.upperBoundProblem == Pk:
                    print('New upper bound found')
                if tree.upperBoundProblem == Pk or (nProcessedProblems<=10 or
                   (nProcessedProblems<=50 and nProcessedProblems%2 == 0) or
                   nProcessedProblems%10 == 0):
                    printMessage(nProcessedProblems, tree.upperBoundProblem.upperBound,
                                 tree.lowerBound, tree.gap, tree.times['Total'])
