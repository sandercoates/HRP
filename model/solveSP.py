import sys
sys.path.append('./classes')
import numpy as np
from graph import Graph
from resources import Resources
from labelling import labelling

def solveSP(data, employee, graph, duals = None, solutions_count: int = 1,
            epsilon = 1e-9, extensionLimits = [],
            constructionHeuristic = False,
            resourceVec = ['TWMin', 'TWMin_g', 'TV']):
    '''Solve SPPRC sub problem for employee on graph considering data and
    duals.
    '''

    # Initialize resources, define included
    resources = Resources(resourceVec)

    # Initialize label extension limit
    if extensionLimits:
        extensionLimit = extensionLimits[0]
    else:
        extensionLimit = None

    # Update graph according to duals if given
    if duals != None:
        graph.update_costs(duals, data, employee, constructionHeuristic = constructionHeuristic)

    # Increment extensionLimit until a neg. red. cost solution is found, or
    # incrementing extensionLimit has no effect
    proceed = True
    while proceed:
        # Solve by labelling algorithm
        processed_labels, extension_limited = labelling(resources=resources,
                                                        graph=graph, data=data,
                                                        employee=employee,
                                                        extensionLimit=extensionLimit)

        # Filter away labels that are not in the end node or have positive cost
        candidate_labels = []
        while processed_labels:
            label = processed_labels.pop()
            if (label.node.day == data['Days'][-1] + 1) and (label.cost < 1e-2):
                candidate_labels.append(label)
                # If a negative reduced cost solution is found, stop
                if label.cost < -epsilon:
                    proceed = False

        if proceed:
            # If the extensionLimit was limiting in labelling
            if extension_limited:
                # Increase the extension limit
                extensionLimits.pop(0)
                if extensionLimits:
                    extensionLimit = extensionLimits[0]
                else:
                    extensionLimit = None
            else:
                # Otherwise, do not continue. No neg. red. cost solutions found
                proceed = False


	# Sort solution candidate labels based on cost (ascending, lowest first)
    candidate_labels = sorted(candidate_labels, key = lambda label: label.cost)

	# Select solutions_count best solutions (based on lowest cost)
    if solutions_count != None:
        solution_labels = candidate_labels[:solutions_count]
    # Should solutions_count be None, keep all solutions
    else:
        solution_labels = candidate_labels

	# Format solutions
    solutions, reduced_costs = {}, {}
    solution_id = 0
    for label in solution_labels:
    	solution_id += 1
    	solutions[solution_id] = np.zeros(data['Days'][-1], dtype = int) # Numpy way
    	for node in label.path[1:-1]: # Ignore artificial days (start and end)
    		solutions[solution_id][node.day - 1] = node.shiftType
    	reduced_costs[solution_id] = label.cost

    # Return None if no solution was found
    if len(solutions) == 0:
        reduced_costs = None
        solutions = None

    return reduced_costs, solutions
