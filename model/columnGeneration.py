import sys
sys.path.append('./classes')
import copy as copy
from columns import Columns
from graph import Graph
from MP import *
from solveSP import solveSP
from selectOrderSP import selectOrderSP
from helpers import *
import numpy as np
import copy
import time

def columnGeneration(masterProblem, data, graphs, columns, times,
                     initialLowerBound=-float('inf'),
                     epsilon=1e-9, outputPrint = False, partialCG = True,
                     orderStrategy = 'noResourcesSP',
                     partialCG_constructionHeuristic = True,
                     labelExtensionLimits=[],
                     SPSolutionsCount = 1,
                     coverConstraint = '=',
                     removeIllegalColumns = False,
                     optimalityGapLimit=0.005,
                     improvementStepSize=10,
                     improvementThreshold=1e-3,
                     branchOnUpperBound=False,
                     branchAndPriceUpperBound=None,
                     resourceVec = ['TWMin', 'TWMin_g', 'TV'],
                     timeLimit = None
                     ):
    '''Column generation for the rostering problem. Input an Xpress master
    problem object, data, graphs, columns, initial lower bound and model
    configuration. Return feasibility, objective, solution and lower bound.'''

    '''Algorithm setup'''
    # Variables used for storing bounds
    iteration = 0
    upperBounds = {}
    lowerBounds = {0: initialLowerBound}
    calculateLBD = False # Indicates when LBD should be calculated

    # Initialize limits on labels extended in SP for each employee
    extensionLimits = dict.fromkeys(employee for employee in data['Employees'])
    for employee in data['Employees']:
        extensionLimits[employee] = copy.copy(labelExtensionLimits)

    '''Generate columns until no objective improving columns can be found or
    stop criterion terminates algorithm.
    '''
    proceed = True
    while proceed:
        # Update iteration count
        iteration += 1

        # Update total time
        times['Total'] += time.time() - times['refTime']
        times['refTime'] = time.time()
        # Check if time limit is reached while not already terminated
        if timeLimit != None and times['Total'] > timeLimit:
            lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
            if iteration > 1:
                return feasible, MPObjective, MPSolution, lowerBounds[iteration]
            else:
                return False, False, False, lowerBounds[iteration]

        # Solve RMP and store time spent
        start = time.time()
        feasible, MPObjective, MPSolution, MPDuals = solveMP(masterProblem=masterProblem, data=data,
                                                             columns=columns,
                                                             outputPrint = outputPrint)
        stop = time.time()
        times['Column generation']['Solve RMP'] += stop - start

        # Update total time
        times['Total'] += time.time() - times['refTime']
        times['refTime'] = time.time()
        # Check if time limit is reached while not already terminated
        if timeLimit != None and times['Total'] > timeLimit:
            lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
            if iteration > 1:
                return feasible, MPObjective, MPSolution, lowerBounds[iteration]
            else:
                return False, False, False, lowerBounds[iteration]

        # If RMP was infeasible (will only happen in first iteration if
        # it happens at all)...
        if not feasible:
            # ...attempt to generate columns to regain feasibility
            start = time.time()
            success, newRosterlineNumbers = columns.constructionHeuristic_CGartificialVariables(data=data,
                                                                                                graphs=graphs,
                                                                                                trimColumns=False,
                                                                                                printStatus=False, # Must be False. Else, solveMP must be updated to remove some columns after this
                                                                                                epsilon=epsilon,
                                                                                                orderStrategy = orderStrategy,
                                                                                                partialCG_constructionHeuristic = partialCG_constructionHeuristic,
                                                                                                coverConstraint = coverConstraint,
                                                                                                removeIllegalColumns = removeIllegalColumns,
                                                                                                resourceVec = resourceVec)
            stop = time.time()
            times['Column generation']['Construction heuristic'] += stop - start

            # Update total time
            times['Total'] += time.time() - times['refTime']
            times['refTime'] = time.time()
            # Check if time limit is reached while not already terminated
            if timeLimit != None and times['Total'] > timeLimit:
                lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
                if iteration > 1:
                    return feasible, MPObjective, MPSolution, lowerBounds[iteration]
                else:
                    return False, False, False, lowerBounds[iteration]

            # If a feasible set of columns was found, update and resolve the RMP
            if success:
                # Update RMP
                start = time.time()
                updateMP(masterProblem=masterProblem, data=data, columns=columns, newRosterlineNumbers=newRosterlineNumbers)
                stop = time.time()
                times['Column generation']['Update RMP'] += stop - start
                # Solve RMP
                start = time.time()
                feasible, MPObjective, MPSolution, MPDuals = solveMP(masterProblem=masterProblem, data=data,
                                                                     columns=columns,
                                                                     outputPrint = outputPrint)
                stop = time.time()
                times['Column generation']['Solve RMP'] += stop - start
            # Else, the construction heuristic indicates infeasibility
            else:
                lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
                return feasible, MPObjective, MPSolution, lowerBounds[iteration]

        # Update total time
        times['Total'] += time.time() - times['refTime']
        times['refTime'] = time.time()
        # Check if time limit is reached while not already terminated
        if timeLimit != None and times['Total'] > timeLimit:
            lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
            return feasible, MPObjective, MPSolution, lowerBounds[iteration]

        # Update upper bound
        upperBounds[iteration] = MPObjective

        # If Branch-and-price upper bound is given, terminate column generation
        # once objective falls below upper bound
        if (branchOnUpperBound and
            branchAndPriceUpperBound < float('inf') and
            MPObjective < branchAndPriceUpperBound):
            calculateLBD = True
            extensionLimits = dict.fromkeys([employee for employee in data['Employees']], [])
            proceed = False

        # Identify order of solving sub problems if partial CG
        if partialCG:
            start = time.time()
            order = selectOrderSP(data, graphs, MPDuals, epsilon, orderStrategy = orderStrategy)
            stop = time.time()
            times['Column generation']['SP order selection'] += stop - start
        else:
            order = copy.copy(data['Employees'])

        # Solve sub problems in order until a neg. red. cost solution found,
        # or all sub problems if we need LBD
        improvingColumnFound = False
        SPobjectives, SPsolutions = {}, {}
        while (not improvingColumnFound and order) or (calculateLBD and order) or (not partialCG and order):

            # Update total time
            times['Total'] += time.time() - times['refTime']
            times['refTime'] = time.time()
            # Check if time limit is reached while not already terminated
            if timeLimit != None and times['Total'] > timeLimit:
                lowerBounds[iteration] = lowerBounds[max(lowerBounds.keys())]
                return feasible, MPObjective, MPSolution, lowerBounds[iteration]

            employee = order.pop(0)
            start = time.time()
            # Solve the subproblem for the specified employee
            [SPobjectives[employee],
             SPsolutions[employee]] = solveSP(data=data, employee=employee,
                                              graph=graphs[employee],
                                              duals=MPDuals, epsilon=epsilon,
                                              extensionLimits = extensionLimits[employee],
                                              solutions_count = SPSolutionsCount,
                                              resourceVec = resourceVec)
            stop = time.time()
            times['Column generation']['Solve SP'] += stop - start
            # Check whether a solution with negative reduced cost was found...
            if SPobjectives[employee][1] < -epsilon:
                # ...and may be added as a column with improvement potential
                improvingColumnFound = True

        # Calculate LBD if this is required and check stop criterion
        if calculateLBD or (not order and extensionLimits == dict.fromkeys([employee for employee in data['Employees']], [])):
            lowerBounds[iteration] = calculateLowerBound(MPObjective,
                                                         SPobjectives,
                                                         lowerBounds,
                                                         data)
            # Reset parameters on LBD calculations
            calculateLBD = False
            # Reset extension limit if needed
            try:
                extensionLimits = curExtensionLimits
            except:
                pass
            # Check stop cirterion if not already set to terminate:
            if proceed:
                proceed = not(stopCriterion(upperBounds[iteration],
                                            lowerBounds[iteration],
                                            optimalityGapLimit))

        # Check if optimal...
        if not improvingColumnFound:
            proceed = False
            lowerBounds[iteration] = MPObjective

        # ... if not optimal, update columns and problem
        if proceed:
            # Initialize dict of new rosterlines
            newRosterlineNumbers = {}
            for employee in SPsolutions:
                # Initialize list of new rosterlines for employee
                newRosterlineNumbers[employee] = []
                # Generate columns for employee
                newRosterlineNumbers[employee] += columns.addColumns(employee = employee,
                                                                     rosterlines = SPsolutions[employee], data = data)
            # Update RMP
            start = time.time()
            updateMP(masterProblem=masterProblem, data=data, columns=columns, newRosterlineNumbers=newRosterlineNumbers)
            stop = time.time()
            times['Column generation']['Update RMP'] += stop - start

            # Check if improvement in objective function is acceptable
            if not improvementCriterion(upperBounds, iteration,
                                        improvementStepSize,
                                        improvementThreshold):
                # Make sure LBD is calculated in next iteration and set
                # extensionLimit to None to prove optimal SPs
                calculateLBD = True
                curExtensionLimits = copy.deepcopy(extensionLimits)
                extensionLimits = dict.fromkeys([employee for employee in data['Employees']], [])

    # Update total time
    times['Total'] += time.time() - times['refTime']
    times['refTime'] = time.time()

    return feasible, MPObjective, MPSolution, lowerBounds[iteration]
