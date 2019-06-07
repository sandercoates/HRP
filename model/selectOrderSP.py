'''Functions used to select order of solving sub problems'''
import numpy as np
import copy as copy
import time
from solveSP import solveSP

def selectOrderSP(data, graphs, MPDuals, epsilon=1e-9, orderStrategy = 'random', constructionHeuristic = False):
    '''Selects order of solving sub problems based on a given strategy'''

    # Create order list
    order = copy.copy(data['Employees'])
    # Select order based on order strategy
    order = globals()['orderStrategy_%s' % orderStrategy](order = order, data = data,
                                                         graphs = graphs, MPDuals = MPDuals,
                                                         epsilon = epsilon,
                                                         constructionHeuristic = constructionHeuristic)
    return order

def orderStrategy_random(order, data, graphs, MPDuals, epsilon, constructionHeuristic):
    '''Shuffling order of SPs randomly'''

    np.random.shuffle(order)
    return order

def orderStrategy_noResourcesSP(order, data, graphs, MPDuals, epsilon, constructionHeuristic):
    '''Solves all SPs without resources, and selects order based on ascending
    objective value.'''
    
    timeStart = time.time()
    # Preallocate space for solutions
    SPobjectives = dict.fromkeys(e for e in data['Employees'])
    SPsolutions = dict.fromkeys(e for e in data['Employees'])
    objectives = np.zeros(data['nEmployees']) # List of objectives to sort later
    # Solve SP without resources for each employee
    for employee in data['Employees']:
        [SPobjectives[employee],
         SPsolutions[employee]] = solveSP(data=data, employee=employee,
                                          graph=graphs[employee],
                                          duals=MPDuals, epsilon=epsilon,
                                          resourceVec = [],
                                          constructionHeuristic = constructionHeuristic)

        # Add employee to order if solutions were found
        if SPobjectives[employee] != None:
            objectives[employee - 1] = SPobjectives[employee][1]
        # If no solution was found, return None as one of the SPs is infeasible
        else:
            return None

    # Sort order after ascending SP objective value
    order = [x for _,x in sorted(zip(objectives,order))]

    return order
