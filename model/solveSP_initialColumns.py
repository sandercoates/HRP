import sys
sys.path.append('./classes')
import numpy as np
from resources import Resources
from labelling import labelling


def solveSP_initialColumns(data, employee, graph, extensionLimits = [1],
                           resourceVec = ['TWMin', 'TWMin_g', 'TV']):
    '''Solves SP with only one label extension and no requirement of negative
    solution. Used to generate initial columns for construction heuristic.'''

    # Initialize resources, define included
    resources = Resources(resourceVec)

    # Initialize label extension limit
    extensionLimit = extensionLimits[0]

    # Run labelling
    processed_labels, extension_limited = labelling(resources=resources,
                                                    graph=graph, data=data,
                                                    employee=employee,
                                                    extensionLimit=extensionLimit)

    # Filter away labels that are not in the end node
    candidate_labels = []
    while processed_labels:
        label = processed_labels.pop()
        if label.node.day == data['Days'][-1] + 1:
            candidate_labels.append(label)

    # Sort solution candidate labels based on cost (ascending, lowest first)
    candidate_labels = sorted(candidate_labels, key = lambda label: label.cost)

    # Choose the label with the best cost
    if candidate_labels:
        solution_label = candidate_labels[0]
    else:
        return None, None

    # Format solution
    # Create vector to store solution
    solution = np.zeros(data['Days'][-1], dtype = int) # Numpy way
    # Add shift type on each day to solution
    for node in solution_label.path[1:-1]: # Ignore artificial days (start and end)
        solution[node.day - 1] = node.shiftType
    # Store objective
    objective = solution_label.cost

    return objective, solution
