from column import Column
from MP_artificialVariables import *
from solveSP_initialColumns import solveSP_initialColumns
from selectOrderSP import selectOrderSP
from solveSP import solveSP
from solveMIP import solveMIP
import copy as copy
import numpy as np
import time

class Columns:
    '''Representation of all restricted master problem columns in the rostering
    problem of Pedersen and Coates (2019) along with associated functions to
    change the set of columns.
    '''

    def __init__(self, data, graphs = None, constructionHeuristic = 'CGartificialVariables',
                 printStatus = False, orderStrategy = 'noResourcesSP',
                 partialCG_constructionHeuristic = True,
                 coverConstraint = '=', removeIllegalColumns = False,
                 resourceVec = ['TWMin', 'TWMin_g', 'TV']):
        # Initialize empty list of columns and no rosterline numbers
        self.columns = []
        self.rosterlineNumbers = None

        # Run construction heuristic to generate initial columns
        getattr(self, 'constructionHeuristic_%s' % constructionHeuristic)(data = data,
                      graphs = graphs, printStatus = printStatus, trimColumns = False,
                      orderStrategy = orderStrategy,
                      partialCG_constructionHeuristic = partialCG_constructionHeuristic,
                      coverConstraint = coverConstraint, removeIllegalColumns = removeIllegalColumns,
                      resourceVec = resourceVec)

    def __repr__(self):
        return str(self.columns)

    def addColumn(self, column: Column):
        '''Adds the column to the list of columns'''

        self.columns.append(column)

    def addColumns(self, employee, rosterlines, data):
        '''Adds columns corresponding to the rosterlines for the given employee
        to the list of columns.
        '''

        rosterlineNumber = self.rosterlineNumbers[employee]
        newRosterlineNumbers = []
        for solution_id in rosterlines:
            rosterlineNumber += 1
            self.addColumn(Column(rosterline=rosterlines[solution_id],
                                  employee=employee,
                                  rosterlineNumber=rosterlineNumber,
                                  data=data))
            newRosterlineNumbers.append(rosterlineNumber)
        self.rosterlineNumbers[employee] = rosterlineNumber
        return newRosterlineNumbers

    def removeColumn(self, column: Column):
        '''Removes the given column from the list of columns'''

        # If the column is among the columns...
        if column in self.columns:
            # ...remove it
            self.columns.remove(column)

    def removeColumnsWithNode(self, node, employee):
        '''Removes all columns associated with the graph node for an employee'''

        # Initialize list of columns to be removed
        removeColumns = []
        # Initialize list of column numbers that are removed
        removedColumnNumbers = []
        # Iterate over all columns...
        for column in self.columns:
            # If the column is associated with the employee in question...
            if column.employee == employee:
                # ...and the column is associated with the node in question...
                if column.A[(column.employee, column.rosterlineNumber,
                             node.day, node.shiftType)] == 1:
                    # Add the column to the list of columns to be removed
                    removeColumns.append(column)
                    removedColumnNumbers.append(column.rosterlineNumber)
        # Iteratively remove the indicated columns
        for column in removeColumns:
            self.removeColumn(column = column)

        return removedColumnNumbers

    def removeColumnsNotInNode(self, node, employee):
        '''Removes all columns not associated with the graph node for an employee'''

        # Initialize list of columns to be removed
        removeColumns = []
        # Initialize list of column numbers that are removed
        removedColumnNumbers = []
        # Iterate over all columns...
        for column in self.columns:
            # If the column is associated with the employee in question...
            if column.employee == employee:
                # ...and the column is not associated with the node in question...
                if not column.A[(column.employee, column.rosterlineNumber,
                                 node.day, node.shiftType)] == 1:
                    # Add the column to the list of columns to be removed
                    removeColumns.append(column)
                    removedColumnNumbers.append(column.rosterlineNumber)
        # Iteratively remove the indicated columns
        for column in removeColumns:
            self.removeColumn(column = column)

        return removedColumnNumbers

    def removeIllegalColumns(self, data):
        '''Removes illegal columns by checking master problem constraints'''
        # Initialize list of columns to be removed
        removeColumns = []
        # Initialize list of column numbers that are removed
        removedColumnNumbers = {}
        # Iterate over all columns
        for column in self.columns:
            # Check feasibility of column
            column.checkMasterFeasible(data = data)
            # Add the column to the list of columns to be removed if infeasible
            if not column.feasible:
                removeColumns.append(column)
                if column.employee in removedColumnNumbers:
                    removedColumnNumbers[column.employee].append(column.rosterlineNumber)
                else:
                    removedColumnNumbers[column.employee] = [column.rosterlineNumber]
        # Iteratively remove the indicated columns
        for column in removeColumns:
            self.removeColumn(column = column)

        return removedColumnNumbers

    def unpackColumns(self, data, newRosterlineNumbers=None):
        '''Retrieves key parameters from columns, if newRosterlineNumbers is
        given, only those columns associated with this dictionary of employee
        keys and rosterlinenumber values are returned'''

        # Initialize parameters
        if newRosterlineNumbers == None:
            rosterlines = dict.fromkeys([e for e in data['Employees']],[])
        else:
            rosterlines = dict.fromkeys([e for e in newRosterlineNumbers],[])
        CK = {}
        A = {}
        A_W = {}
        A_O = {}
        A_g = {}
        V = {}
        D = {}

        # Iterate through columns and update parameters
        for column in self.columns:
            # Only consider newRosterlineNumbers if given as input
            if (newRosterlineNumbers == None or
                (column.employee in newRosterlineNumbers and
                 column.rosterlineNumber in newRosterlineNumbers[column.employee])):
                rosterlines[column.employee] = rosterlines[column.employee] + [column.rosterlineNumber]
                CK[(column.employee,column.rosterlineNumber)] = column.cost
                A.update(column.A)
                A_W.update(column.A_W)
                A_O.update(column.A_O)
                A_g.update(column.A_g)
                V.update(column.V)
                D.update(column.D)

        return rosterlines, CK, A, A_W, A_O, A_g, V, D

    def unpackColumns_A(self, data):
        '''Retrieves A matrix from columns'''

        # Initialize
        A = {}

        # Iterate through columns and update
        for column in self.columns:
            A.update(column.A)

        return A

    def unpackColumns_rosterlines(self, data):
        '''Retrieves rosterlines set from columns'''

        # Initialize
        rosterlines = dict.fromkeys([e for e in data['Employees']],[])

        # Iterate through columns and update
        for column in self.columns:
            rosterlines[column.employee] = rosterlines[column.employee] + [column.rosterlineNumber]

        return rosterlines

    def constructionHeuristic_CGartificialVariables(self, data, graphs,
                                                    trimColumns=False,
                                                    printStatus=False,
                                                    epsilon=1e-9,
                                                    orderStrategy = 'noResourcesSP',
                                                    partialCG_constructionHeuristic = True,
                                                    coverConstraint = '=',
                                                    removeIllegalColumns = False,
                                                    resourceVec = ['TWMin', 'TWMin_g', 'TV']):
        '''Column generation with artificial variables to create initial columns.
        If trimColumns is set to True, keep only the columns that are in the
        solution of the artificial problem'''

        # Assume construction heuristic is not able to construct columns to
        # ensure feasibility of original problem (artificial objective > 0)
        success = False

        if printStatus:
            print('Construction heuristic started (CG artificial vairables)')
        # Save start time in construction heuristic
        startTime = time.time()


        '''Algorithm setup'''
        # Variables used for storing bounds
        iteration = 0
        # Dictionary to store new rosterline numbers created
        newRosterlineNumbers = dict.fromkeys(e for e in data['Employees'])
        for e in data['Employees']:
            newRosterlineNumbers[e] = []

        # Set limit on number of labels extended in each node and increment
        labelExtensionLimits = [1] # 1 is typically sufficient for this case
        # Initialize limits on labels extended in SP for each employee
        extensionLimits = dict.fromkeys(employee for employee in data['Employees'])
        for employee in data['Employees']:
            extensionLimits[employee] = copy.copy(labelExtensionLimits)

        improvingColumnFound = True # Start as true for optimality check to work

        # Make a copy of the graphs
        graphs_constructionHeuristic = copy.deepcopy(graphs)

        '''If an employee does not have any columns, construct initial columns by given method'''
        # Assume initially all employees have columns
        generateInitialColumns = False
        # If no columns exist: generate initial columns
        if not self.columns:
            generateInitialColumns = True
            # Make dictionary marking employees not having columns
            employeeColumns = dict.fromkeys((e for e in data['Employees']), False)
        # Else if columns are deleted, check that all employees have columns
        else:
            # Initially, assume no employees have columns
            employeeColumns = dict.fromkeys((e for e in data['Employees']), False)
            # Go through all columns and update employeeColumns
            for column in self.columns:
                employeeColumns[column.employee] = True
            # If an employee without columns exists: generate new columns
            for employee in data['Employees']:
                if not employeeColumns[employee]:
                    generateInitialColumns = True
                    break
        if generateInitialColumns:

            # Generate initial columns by solving SP without any duals, but with real costs
            SPobjectives, SPsolutions = {}, {}
            for employee in data['Employees']:
                if not employeeColumns[employee]:
                    [SPobjectives[employee],
                     SPsolutions[employee]] = solveSP_initialColumns(data=data, employee=employee,
                                                                     graph=graphs_constructionHeuristic[employee],
                                                                     extensionLimits = extensionLimits[employee],
                                                                     resourceVec = resourceVec)

                    # Check feasibility of problem. If no solutions returned...
                    if SPobjectives[employee] == None:
                        # ...problem is infeasible
                        return success, newRosterlineNumbers


            # Add columns to self
            if self.rosterlineNumbers == None:
                for employee in SPsolutions:
                    self.addColumn(column = Column(SPsolutions[employee], employee, 1, data))
                self.rosterlineNumbers = dict.fromkeys((e for e in SPsolutions),1)
                newRosterlineNumbers = dict.fromkeys(e for e in SPsolutions)
                for e in SPsolutions:
                    newRosterlineNumbers[e] = [1]
            else:
                for employee in SPsolutions:
                    rosterlineNumber = self.rosterlineNumbers[employee] + 1
                    self.addColumn(column = Column(SPsolutions[employee], employee,
                                                   rosterlineNumber, data))
                    self.rosterlineNumbers[employee] = rosterlineNumber
                    newRosterlineNumbers[employee] += [rosterlineNumber]

        '''Define master problem with artificial variables'''
        masterProblem_artVars = defineMP_artificialVariables(data = data,
                                                             initialColumns = self,
                                                             coverConstraint = coverConstraint)

        '''Generate columns until no objective improving columns can be found'''
        optimal = False
        while not optimal:
            # Update iteration count
            iteration += 1

            # Solve RMP with artificial variables
            feasible, MPObjective, MPSolution, MPDuals = solveMP_artificialVariables(masterProblem_artVars = masterProblem_artVars,
                                                                                     data=data,
                                                                                     columns=self,
                                                                                     outputPrint=False)

            # If zero solution, columns are feasible and can be used as initial columns
            if MPObjective <= epsilon:
                optimal = True
                success = True
            # Else, if all SPs have been solved and all reduced costs are 0...
            elif not improvingColumnFound:
                # ... no feasible solution exists and the generation can terminate
                optimal = True
            # Else, generate more columns
            else:
                # Identify order of solving sub problems if partialCG
                if partialCG_constructionHeuristic:
                    order = selectOrderSP(data, graphs_constructionHeuristic,
                                          MPDuals, epsilon, orderStrategy = orderStrategy,
                                          constructionHeuristic = True)
                else:
                    order = copy.copy(data['Employees'])

                # If no order was found, at least one employee has infeasible
                # SP and hence the problem is infeasible
                if order == None:
                    return success, newRosterlineNumbers

                # Solve sub problems in order until a neg. red. cost solution found
                improvingColumnFound = False
                SPobjective, SPsolutions = {}, {}
                while (not improvingColumnFound and order) or (not partialCG_constructionHeuristic and order):
                    employee = order.pop(0)
                    [SPobjective[employee],
                     SPsolutions[employee]] = solveSP(data=data, employee=employee,
                                                      graph=graphs_constructionHeuristic[employee],
                                                      duals=MPDuals, extensionLimits = extensionLimits[employee],
                                                      constructionHeuristic = True, resourceVec = resourceVec,
                                                      solutions_count = None)
                    # If no solution was found, one of the SPs is infeasible and
                    # thus the original problem
                    if SPobjective[employee] == None:
                        return success, newRosterlineNumbers
                    # Indicate whether a potentially improving column is found
                    elif SPobjective[employee][1] < -epsilon:
                        improvingColumnFound = True

                # Update columns
                # Initialize dict of new rosterlines
                newRosterlineNumbers_artVars = {}
                for employee in SPsolutions:
                    # Initialize list of new rosterlines for employee
                    newRosterlineNumbers_artVars[employee] = []
                    # Update columns and newRosterlineNumbers dictinaries
                    numbers = self.addColumns(employee = employee,
                                       rosterlines = SPsolutions[employee], data = data)
                    newRosterlineNumbers[employee] += numbers
                    newRosterlineNumbers_artVars[employee] += copy.deepcopy(numbers)

                # Update RMP
                updateMP_artificialVariables(masterProblem_artVars=masterProblem_artVars,
                                             data=data, columns=self, newRosterlineNumbers_artVars=newRosterlineNumbers_artVars)

        '''Only keep columns present in optimal solution'''
        if trimColumns:
            removeColumnList = []
            for column in self.columns:
                if MPSolution[(column.employee, column.rosterlineNumber)] <= epsilon:
                    removeColumnList += [column]
                    if column.rosterlineNumber in newRosterlineNumbers[column.employee]:
                        newRosterlineNumbers[column.employee].remove(column.rosterlineNumber)
            for column in removeColumnList:
                self.removeColumn(column)

        '''Remove indexes of newRosterlineNumbers without any new rosterlines'''
        for employee in data['Employees']:
            if newRosterlineNumbers[employee] == []:
                del newRosterlineNumbers[employee]

        # Store time spent in construction heuristic
        timeConstructionHeuristic = time.time() - startTime
        # Print complete
        if printStatus:
            print('Construction heuristic complete')
            print('Time spent in construciton heuristic:', timeConstructionHeuristic)

        # Return boolean indicating whether solution implies original problem
        # is feasible or not
        return success, newRosterlineNumbers

    def constructionHeuristic_MIPheuristic(self, data, graphs,
                                                    trimColumns=False,
                                                    printStatus=False,
                                                    epsilon=1e-9,
                                                    orderStrategy = 'noResourcesSP',
                                                    partialCG_constructionHeuristic = True,
                                                    coverConstraint = '=',
                                                    removeIllegalColumns = False,
                                                    resourceVec = ['TWMin', 'TWMin_g', 'TV']):
        '''Returns the best feasible solution found with the MIP heuristic solver in
        xpress'''
        # Print status
        if printStatus:
            print('Construction heuristic started (MIP heuristic)')
        # Save start time in construction heuristic
        startTime = time.time()

        # Solve MIP heuristic
        completed, feasible, objective, lowerBound, solution, computationTime = solveMIP(data = data, outputPrint = False,
                                                 problemName = 'MIP_heuristic',
                                                 heuristicOnly = True,
                                                 coverConstraint = coverConstraint)
        # Rosterline numbers (0 for each employee, is updated when columns are added)
        self.rosterlineNumbers = dict.fromkeys((e for e in data['Employees']),0)
        # Transform solution to columns if feasible
        if feasible:
            for employee in data['Employees']:
                # Find rosterline for the employe
                rosterline = []
                # Iterate over days
                for day in data['Days']:
                    # Identify shift type with weith 1 (minus numerical error)
                    for shiftType in data['ShiftTypes']:
                        if solution['x'][(employee, day, shiftType)] > 0.99:
                            rosterline.append(shiftType)
                            break
                # Create rosterline dictionary for the employee
                rosterlines = {1: rosterline}
                self.addColumns(employee = employee, rosterlines = rosterlines, data = data)

        # Store time spent in construction heuristic
        timeConstructionHeuristic = time.time() - startTime
        # Print complete
        if printStatus:
            print('Construction heuristic complete')
            print('Time spent in construciton heuristic:', timeConstructionHeuristic)
