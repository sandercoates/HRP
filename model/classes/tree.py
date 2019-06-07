from problem import Problem
import copy
import time

class Tree():
    '''Class representing the branch-and-bound tree'''

    def __init__(self, configuration = {}, refTime = 0):
        self.unprocessedProblems = {}
        self.processedProblems = {}
        self.complete = False
        # Initialize the number of problems (excluding the expected root node)
        self.n = -1
        # Initialize upper bound problem (dummy with indefinite upper bound)
        self.upperBoundProblem = Problem(upperBound = float('inf'))
        # Initialize lower bound (negative infinite objective value)
        self.lowerBound = -float('inf')
        # Calculate optimality gap
        self.gap = float('inf')
        # Initialize gap history
        self.gapHistory = {0: self.gap}
        # Initialize time spent in tree '{Level: {Code chunk: Time spent in chunk}}'
        self.times = {'refTime': refTime,
                      'Total': 0,
                      'Branch and price': {'Initializations': 0,
                                           'Construction heuristic': 0,
                                           'Solve node': 0,
                                           'Branch': 0,
                                           'Search': 0,
                                           'Other': 0},
                      'Node': {'Column generation': 0,
                               'Other': 0},
                      'Column generation': {'Solve RMP': 0,
                                            'Update RMP': 0,
                                            'Solve SP': 0,
                                            'Construction heuristic': 0,
                                            'SP order selection': 0,
                                            'Other': 0}
                     }
        # Initialize model configuration
        self.configuration = configuration


    def __repr__(self):
        return str(self.unprocessedProblems) + str(self.processedProblems)

    def addProblem(self, problem):
        if problem.processed:
            self.processedProblems[problem.ID] = problem
        else:
            self.unprocessedProblems[problem.ID] = problem
        self.n += 1

    def pruneOnUpperBound(self):
        '''Prunes and marks as processed all unprocessed problems with a lower
        bound above the tree upper bound.'''

        # Only consider cases if a tree upper bound is found
        if self.upperBoundProblem.upperBound < float('inf'):
            # Initialize list of problems to be pruned
            prunedProblems = []
            # Iterate over all unprocessed problems
            for k in self.unprocessedProblems:
                # If the problem has a lower lower bound higher than the tree upper bound...
                if self.unprocessedProblems[k].lowerBound >= self.upperBoundProblem.upperBound:
                    # ...Store problem k for pruning
                    prunedProblems.append(k)

            for k in prunedProblems:
                # Mark problem k as pruned
                self.unprocessedProblems[k].pruned = True
                # Mark problem k as processed
                self.processedProblems[k] = self.unprocessedProblems.pop(k)
                # Delete masterProblem from problem k
                self.processedProblems[k].masterProblem = None

    def branch(self, problem, branchingStrategy, data):
        '''Branches problem into two children nodes according to a given branching strategy'''

        # Obtain master problems, columns and graphs for up- and down-branch
        # according to specified branching strategy
        branchedProblems, branchedColumns, branchedGraphs = getattr(self,
                                                                    'branchingStrategy_%s' % branchingStrategy)(problem = problem, data = data)

        # Iterate over branches
        for b in branchedProblems:
            # Create branched problem
            branchedProblem = Problem(ID = self.n + 1,
                                      masterProblem = branchedProblems[b],
                                      columns = branchedColumns[b],
                                      graphs = branchedGraphs[b],
                                      parent = problem,
                                      branchTag = b)

            # Add branchedProblem as child to problem
            problem.children[b] = branchedProblem

            # Add branchedProblem to tree
            self.addProblem(branchedProblem)

    def branchingStrategy_xVars(self, problem, data):
        '''Branches a problem using branching on x-variables'''

        '''Select which variable to branch on'''
        # Retrieve x solution
        x_solution = problem.xTransform(data = data)

        # Find most fractional x to branch on
        largestFraction = 0 # Variable keeping track of most fractional value
        for e in data['Employees']:
            for d in data['Days']:
                for s in data['ShiftTypes']:
                    # Check fractionality
                    x_fraction = 0.5 - abs(0.5 - x_solution[(e,d,s)])
                    # If largest fractionality...
                    if x_fraction > largestFraction:
                        largestFraction = x_fraction # ... Update largest fractionality value
                        branching_employee = e # ... Update e index
                        branching_day = d # ... Update d index
                        branching_shiftType = s # ... Update s index

        # Locate branching node
        for node in problem.graphs[branching_employee].nodes:
            if node.day == branching_day and node.shiftType == branching_shiftType:
                branchingNode = node
                break

        # Prepare dictionaries for storing branch information
        branchedColumns = dict.fromkeys(b for b in ['down', 'up'])
        branchedGraphs = dict.fromkeys(b for b in ['down', 'up'])
        branchedProblems = dict.fromkeys(b for b in ['down', 'up'])

        # Prepare two copies of the problem for the child nodes (one based on
        # original)
        branchedProblems['down'] = problem.masterProblem.copy()
        branchedProblems['up'] = problem.masterProblem.copy()
        # Remove master problem of problem that was branched
        del problem.masterProblem
        problem.masterProblem = None

        '''Down branch'''
        # Remove all columns in a given node for a given employee
        branchedColumns['down'] = copy.deepcopy(problem.columns)
        removedColumnNumbers = branchedColumns['down'].removeColumnsWithNode(node = branchingNode, employee = branching_employee)

        # Delete all removed columns in the master problem
        branchedProblems['down'].delVariable(['lambda({},{})'.format(branching_employee, k) for k in removedColumnNumbers])

        # Remove node from relevant graph
        branchedGraphs['down'] = copy.deepcopy(problem.graphs)
        branchedGraphs['down'][branching_employee].remove_nodeOnShift(node = branchingNode)

        '''Up branch'''
        #Remove all columns not in a given node for a given employee
        branchedColumns['up'] = copy.deepcopy(problem.columns)
        removedColumnNumbers = branchedColumns['up'].removeColumnsNotInNode(node = branchingNode, employee = branching_employee)

        # Delete all removed columns in the master problem
        branchedProblems['up'].delVariable(['lambda({},{})'.format(branching_employee, k) for k in removedColumnNumbers])

        #Remove all, but a given node on the corresponding day for a given employee
        branchedGraphs['up'] = copy.deepcopy(problem.graphs)
        branchedGraphs['up'][branching_employee].remove_nodesOnSameDay(node = branchingNode)

        return branchedProblems, branchedColumns, branchedGraphs

    def branchingStrategy_multipleXVars(self, problem, data):
        '''Branches a problem using branching on x-variables, and also creates
        and additional branch where the highest non-integer value for each
        employee is fixed to integrity.
        '''

        '''Select which variable to branch on'''
        # Retrieve x solution
        x_solution = problem.xTransform(data = data)

        # Find most fractional x to branch on and highest non-integer value
        # for employees to create additional branch
        largestFraction = 0 # Variable keeping track of most fractional value
        largestValue = dict.fromkeys(e for e in data['Employees'])
        for e in data['Employees']:
            largestValue[e] = {'value': 0, 'day': None, 'shiftType': None}
            for d in data['Days']:
                for s in data['ShiftTypes']:
                    # Check fractionality
                    x_fraction = 0.5 - abs(0.5 - x_solution[(e,d,s)])
                    # If largest non-integer value for employee
                    if (x_solution[(e,d,s)] < 1 and
                        x_solution[(e,d,s)] > largestValue[e]['value']):
                        # Update largest value for employee
                        largestValue[e]['value'] = x_solution[(e,d,s)]
                        largestValue[e]['day'] = d
                        largestValue[e]['shiftType'] = s
                    # If largest fractionality...
                    if x_fraction > largestFraction:
                        largestFraction = x_fraction # ... Update largest fractionality value
                        branching_employee = e # ... Update e index
                        branching_day = d # ... Update d index
                        branching_shiftType = s # ... Update s index
            # Remove employee largest value if no positive non-integer value was found
            if largestValue[e]['value'] == 0:
                largestValue.pop(e)

        # Locate ordinary branching node
        for node in problem.graphs[branching_employee].nodes:
            if node.day == branching_day and node.shiftType == branching_shiftType:
                ordinaryBranchingNode = node
                break

        # Locate branching nodes for additional branch
        additionalBranchingNodes = dict.fromkeys(e for e in largestValue)
        for e in largestValue:
            for node in problem.graphs[e].nodes:
                if node.day == largestValue[e]['day'] and node.shiftType == largestValue[e]['shiftType']:
                    additionalBranchingNodes[e] = node
                    break

        # Prepare dictionaries for storing branch information
        branchedColumns = dict.fromkeys(b for b in ['down', 'up', 'additional'])
        branchedGraphs = dict.fromkeys(b for b in ['down', 'up', 'additional'])
        branchedProblems = dict.fromkeys(b for b in ['down', 'up', 'additional'])

        # Prepare two copies of the problem for the child nodes (one based on
        # original)
        branchedProblems['down'] = problem.masterProblem
        branchedProblems['up'] = problem.masterProblem.copy()
        branchedProblems['additional'] = problem.masterProblem.copy()
        # Remove master problem of problem that was branched
        problem.masterProblem = None

        '''Down branch'''
        # Remove all columns in a given node for a given employee
        branchedColumns['down'] = copy.deepcopy(problem.columns)
        removedColumnNumbers = branchedColumns['down'].removeColumnsWithNode(node = ordinaryBranchingNode, employee = branching_employee)

        # Fixate to zero all removed columns in the master problem
        branchedProblems['down'].delVariable(['lambda({},{})'.format(branching_employee, k) for k in removedColumnNumbers])

        # Remove node from relevant graph
        branchedGraphs['down'] = copy.deepcopy(problem.graphs)
        branchedGraphs['down'][branching_employee].remove_nodeOnShift(node = ordinaryBranchingNode)

        '''Up branch'''
        #Remove all columns not in a given node for a given employee
        branchedColumns['up'] = copy.deepcopy(problem.columns)
        removedColumnNumbers = branchedColumns['up'].removeColumnsNotInNode(node = ordinaryBranchingNode, employee = branching_employee)

        # Fixate to zero all removed columns in the master problem
        branchedProblems['up'].delVariable(['lambda({},{})'.format(branching_employee, k) for k in removedColumnNumbers])

        #Remove all, but a given node on the corresponding day for a given employee
        branchedGraphs['up'] = copy.deepcopy(problem.graphs)
        branchedGraphs['up'][branching_employee].remove_nodesOnSameDay(node = ordinaryBranchingNode)

        '''Additional branch'''
        #Remove all columns not in given nodes for all employees
        branchedColumns['additional'] = copy.deepcopy(problem.columns)
        for e in additionalBranchingNodes:
            removedColumnNumbers = branchedColumns['additional'].removeColumnsNotInNode(node = additionalBranchingNodes[e], employee = e)
            # Fixate to zero all removed columns in the master problem
            branchedProblems['additional'].delVariable(['lambda({},{})'.format(e, k) for k in removedColumnNumbers])

        #Remove all, but a given node on the corresponding day for a given employee
        branchedGraphs['additional'] = copy.deepcopy(problem.graphs)
        for e in additionalBranchingNodes:
            branchedGraphs['additional'][e].remove_nodesOnSameDay(node = additionalBranchingNodes[e])

        return branchedProblems, branchedColumns, branchedGraphs

    def calculateLowerBound(self):
        '''Calculates lower bound in tree by finding the minimum problem
        specific lower bound among all leaves in the tree (unprocessed problems
        and pruned processed problems). Utilize that every leaf problem is
        either unprocessed or processed and pruned when calculating the bound.
        '''

        # Initialize arbitrary large lower bound
        lowerBound = float('inf')

        # Iterate over all unprocessed problems
        for k in self.unprocessedProblems:
            # If the problem has a lower lower bound than the current bound...
            if self.unprocessedProblems[k].lowerBound < lowerBound:
                # ...update the lower bound
                lowerBound = self.unprocessedProblems[k].lowerBound

        # Iterate over all processed problems
        for k in self.processedProblems:
            # If the problem has been pruned and was feasible...
            if (self.processedProblems[k].pruned and
                self.processedProblems[k].feasible):
                # ...check if lower bound needs updating
                if self.processedProblems[k].lowerBound < lowerBound:
                    lowerBound = self.processedProblems[k].lowerBound

        # Return the lowest bound among all tree leaves
        self.lowerBound = lowerBound

    def search(self, searchStrategy='DepthFirst_Up'):
        '''Returns index k of problem to solve next in tree using input search
        strategy.
        '''

        # Call search function for searchStrategy
        k = getattr(self, 'search_%s' % searchStrategy)()

        return k

    def search_DepthFirst_Up(self):
        '''Depth first search in branch-and-bound tree, choosing up branch.
        Returns the index of the right-most unprocessed problem on the highest
        level in the tree. Utilizes that among siblings, right branch has highest
        index.
        '''

        # Initialize highest level found and list of problems on higest level
        hl = 0
        hlProblems = []
        # Iterate over unprocessedProblems and identify highest level problems
        for k in self.unprocessedProblems:
            # If problem k is on a higher level than the highest level found
            if self.unprocessedProblems[k].level > hl:
                # Update the highest level found
                hl = self.unprocessedProblems[k].level
                # Replace the list of problems on the highest level with k
                hlProblems = [k]
            # Or, if problem k is on the same level as the highest level found
            elif self.unprocessedProblems[k].level == hl:
                # Add it to the list of problems on the highest level
                hlProblems.append(k)

        # Find the problem on the highest level with the highest index
        # (Problem furthers to the right in the tree)
        k = max(hlProblems)

        return k

    def search_BestFirst(self):
        '''Returns the problem with the lowest LBD of all unprocessed problems because
        this is the most promising'''

        # Initialize best problem
        bestProblem = None
        # Search through all unprocessed problems
        for k in self.unprocessedProblems:
            # If first iteration: set bestProblem to k
            if bestProblem == None:
                bestProblem = k
            # Else if problem has better or equal LBD than the best previously found, update k
            # Note: 'or equal' ensures up-branch is chosen first for nodes with equal LBD
            elif self.unprocessedProblems[k].lowerBound <= self.unprocessedProblems[bestProblem].lowerBound:
                bestProblem = k
        #Return the ID of the problem with best LBD
        return bestProblem

    def terminationCriterion(self, gapLimit=1e-6, sizeLimit=None):
        '''Termination criterion in branch-and-price algorithm'''

        terminate = False

        # Check optimality gap
        if self.gap < gapLimit:
            terminate = True
        # Check limit on number of nodes in tree
        elif sizeLimit != None and self.n >= sizeLimit:
            terminate = True

        return terminate

    def calculateOptimalityGap(self):
        '''Returns the optimality gap of the tree, as defined by:

            gap = |UBD - LBD|/max(|LBD|, |UBD|)

        If gap is not defined due to indefinite lower bound (denominator),
        set indefinite gap.

        If the gap is updated, the new gap is stored with a time.
        '''

        UBD = self.upperBoundProblem.upperBound
        LBD = self.lowerBound

        prevGap = self.gap

        self.gap = abs(UBD - LBD)/max(abs(LBD), abs(UBD))

        # If gap is NaN (for which gap != gap), set gap to infinite
        if self.gap != self.gap:
            self.gap = float('inf')
        # Update gap if different from prevGap
        elif self.gap != prevGap:
            self.gapHistory[self.times['Total']] = self.gap
