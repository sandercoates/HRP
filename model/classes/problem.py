from columnGeneration import columnGeneration
from MP import *
import time
import copy


class Problem():
    '''Class with info on a problem in the branch-and-bound tree.

    Level refers to the level in the branch-and-bound tree, indexed from level
    zero of the root node.
    '''

    def __init__(self, ID=None, parent=None, branchTag=None, masterProblem=None,
                 columns=None, graphs=None, upperBound=None, data=None,
                 coverConstraint='='):
        self.ID = ID
        self.parent = parent
        self.branchTag = branchTag
        # If no parent, node is root problem with level zero (per definition)
        if parent == None:
            self.level = 0
            self.lowerBound = -float('inf')
        # Otherwise, problem is one level below (+1) parent problem and lower bound is
        # the same as parent node before problem is processed
        else:
            self.level = self.parent.level + 1
            self.lowerBound = parent.lowerBound
        self.columns = columns
        # If no masterProblem was given, but data was given, define it (data is
        # required input in this case, and will only be done once in the root node)
        if masterProblem == None and data != None:
            self.masterProblem = defineMP(data=data,
            initialColumns=self.columns,
            outputPrint=False,
            coverConstraint = coverConstraint)
        else:
            self.masterProblem = masterProblem
        self.graphs = graphs
        self.objective = None
        self.processed = False
        self.feasible = True
        self.optimal = False
        # Boolean indicating if the best LP solution is integer feasible
        self.integer = False
        self.upperBound = upperBound
        # The best integer solution
        self.integerSolution = None
        self.pruned = False
        # The best solution
        self.solution = None
        self.startTime = None
        self.stopTime = None
        self.children = {}

    def __repr__(self):
        repr = ('\nProblem ID:\t' + str(self.ID)
             + '\nLevel:\t\t' + str(self.level)
             + '\nObjective:\t' + str(self.objective)
             + '\nProcessed:\t' + str(self.processed)
             + '\nStart time:\t' + str(self.startTime)
             + '\nStop time:\t' + str(self.stopTime)
             + '\nFeasible:\t' + str(self.feasible)
             + '\nOptimal:\t' + str(self.optimal)
             + '\nInteger:\t' + str(self.integer)
             + '\nLower bound:\t' + str(self.lowerBound)
             + '\nUpper bound:\t' + str(self.upperBound)
             + '\nPruned:\t\t' + str(self.pruned)) + '\n'

        # Print parent ID if exists
        if self.parent != None:
            repr += 'Parent ID:\t' + str(self.parent.ID) + '\n'

        return repr

    def reduceSize(self, data=None):
        '''Reduces size of problem after it is processed'''
        # Delete graphs
        self.graphs = None
        # Store integer x-solution if exists
        if self.integerSolution != None:
            self.integerXSolution = self.xTransform(data=data, LP=False)
        # Delete columns
        self.columns = None
        # Delete integerSolution (lambdas)
        self.integerSolution = None
        # Delete solution (lambdas)
        self.solution = None
        # If problem is not processed, delete masterProblem
        if not self.processed:
            self.masterProblem = None

    def solve(self, data, times, epsilon=1e-9, partialCG = True,
              orderStrategy = 'noResourcesSP',
              partialCG_constructionHeuristic = True,
              labelExtensionLimits=[None],
              SPSolutionsCount=1, coverConstraint = '=',
              removeIllegalColumns = False,
              CGOptimalityGapLimit=0.005,
              CGImprovementStepSize=10,
              CGImprovementThreshold=1e-3,
              branchOnUpperBound=False,
              treeUpperBound=None,
              resourceVec = ['TWMin', 'TWMin_g', 'TV'],
              timeLimit=None
              ):
        '''Solves the problem by column generation'''

        # Start timer
        self.startTime = time.time()

        # Solve problem
        [self.feasible,
         self.objective,
         self.solution,
         self.lowerBound] = columnGeneration(masterProblem=self.masterProblem,
                                             data=data,
                                             graphs=self.graphs,
                                             columns=self.columns,
                                             initialLowerBound=self.lowerBound,
                                             epsilon=epsilon,
                                             partialCG = partialCG,
                                             orderStrategy = orderStrategy,
                                             partialCG_constructionHeuristic = partialCG_constructionHeuristic,
                                             labelExtensionLimits=labelExtensionLimits,
                                             SPSolutionsCount=SPSolutionsCount,
                                             coverConstraint = coverConstraint,
                                             removeIllegalColumns = removeIllegalColumns,
                                             optimalityGapLimit=CGOptimalityGapLimit,
                                             improvementStepSize=CGImprovementStepSize,
                                             improvementThreshold=CGImprovementThreshold,
                                             branchOnUpperBound=branchOnUpperBound,
                                             branchAndPriceUpperBound=treeUpperBound,
                                             times = times,
                                             resourceVec = resourceVec,
                                             timeLimit=timeLimit)
        stop = time.time()
        # Store time spent in column generation
        times['Node']['Column generation'] += stop - self.startTime
        times['Column generation']['Other'] = (times['Node']['Column generation']
                                            -  times['Column generation']['Solve RMP']
                                            -  times['Column generation']['Update RMP']
                                            -  times['Column generation']['Solve SP']
                                            -  times['Column generation']['Construction heuristic']
                                            -  times['Column generation']['SP order selection'])

        # Check if time limit is reached while not already terminated
        if timeLimit == None or times['Total'] <= timeLimit:
            # Mark problem as solved
            self.processed = True
            # If the problem was feasible
            if self.feasible:
                # Check if solution is integer
                self.isInteger(data, epsilon)
                # Check if problem was solved to optimality (lower bound = upper bound)
                if self.objective == self.lowerBound:
                    self.optimal = True

        # Stop timer
        self.stopTime = time.time()

        # Calulcate times
        times['Branch and price']['Solve node'] += self.stopTime - self.startTime
        times['Node']['Other'] = (times['Branch and price']['Solve node']
                               - times['Node']['Column generation'])

    def isInteger(self, data, epsilon=1e-9):
        '''Checks if the solution is integer'''

        # Solve integer master problem (note that duals=None for IP)
        [integerFeasible, integerObjective,
         integerSolution, duals] = solveMP(masterProblem=self.masterProblem,
                                           data=data, columns=self.columns,
                                           LP=False)

        # If an integer solution was found...
        if integerFeasible:
            # ...and the integer objective values matches LP objective...
            if abs(integerObjective - self.objective) <= epsilon:
                # ...have found columns for integer optimal solution
                self.integer = True
            # Regardless, store problem upper bound and integer solution
            self.upperBound = integerObjective
            self.integerSolution = integerSolution

    def xTransform(self, data, LP=True):
        '''Transforms solution of weighting (lambda) variables and columns to
        solution assignment (x) variables, based on the LP or IP solution.
        '''

        if LP == True:
            solution = self.solution
        else:
            solution = self.integerSolution

        # Dictionary to store solution
        x = dict.fromkeys([(e,d,s) for e in data['Employees']
                                       for d in data['Days']
                                       for s in data['ShiftTypes']], 0)
        # A matrix and rosterlines set from columns
        A = self.columns.unpackColumns_A(data=data)
        rosterlines = self.columns.unpackColumns_rosterlines(data=data)
        # Calculate assignment variables
        for e in data['Employees']:
          for k in rosterlines[e]:
              for d in data['Days']:
                  for s in data['ShiftTypes']:
                          x[(e,d,s)] += A[(e,k,d,s)] * solution[(e,k)]

        return x
