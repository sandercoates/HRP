'''Helper functions'''
import pickle

def savePickle(tree, outputTreePickle=None):
    '''Save tree to pickle file, first removing unnecessary data'''
    if outputTreePickle != None:
        # Remove reference time
        del tree.times['refTime']
        # Calculate times not accounted for
        tree.times['Branch and price']['Other'] = (tree.times['Total']
                                                -  tree.times['Branch and price']['Initializations']
                                                -  tree.times['Branch and price']['Construction heuristic']
                                                -  tree.times['Branch and price']['Solve node']
                                                -  tree.times['Branch and price']['Branch']
                                                -  tree.times['Branch and price']['Search'])
        # Reduce size of all unprocessed problems
        for k in tree.unprocessedProblems:
            tree.unprocessedProblems[k].reduceSize()
        # Calculate time that is unaccounted for
        with open(outputTreePickle[:-7]+'.pickle', 'wb') as f:
             pickle.dump(tree, f)

def printColumnReducedCosts(MPSolution, MPDuals, columns, graphs, data):
    '''Print weighting variables and respective reduced costs, based on
    MP solution, dual variables, columns and graphs.
    '''

    # Update graph for all employees according to dual variables
    for employee in data['Employees']:
        graphs[employee].update_costs(MPDuals, data, employee)

    # Iterate over all columns
    for column in columns.columns:
        employee = column.employee
        rosterlineNumber = column.rosterlineNumber
        print(MPSolution[(employee, rosterlineNumber)], column.reducedCost(graphs[employee], data))

def calculateLowerBound(MPObjective, SPobjectives, lowerBounds, data):
    '''Calculates LBD based on an MPObjective and SPobjectives for each sub problem'''
    LBD = MPObjective
    for employee in data['Employees']:
        LBD += SPobjectives[employee][1]

    return max(LBD, lowerBounds[max(lowerBounds.keys(), key=(lambda k: lowerBounds[k]))])

def improvementCriterion(upperBounds, iteration, improvementStepSize, improvementThreshold):
    '''Function to check if there is enough improvement in CG objective function.
    Returns true if improvement is good enough.
    '''
    # Check if UBD has improved since start and iteration is larger that step size (must be satisfied)
    if upperBounds[1] == upperBounds[iteration] or iteration <= improvementStepSize:
        return True

    # Calculate marginal improvement
    marginalImprovement = abs((upperBounds[iteration] - upperBounds[iteration-improvementStepSize])
                                / upperBounds[iteration-improvementStepSize])

    # Check marginal improvement against threshold
    if marginalImprovement >= improvementThreshold:
        return True
    else:
        return False

def stopCriterion(UBD, LBD, optimalityGapLimit):
    '''CG stop criterion based on gap bedween UBD and LBD'''
    optimalityGap = abs((UBD - LBD)/LBD)
    if optimalityGap <= optimalityGapLimit:
        return True
    else:
        return False

def labelsInNode(labels, label, size=None):
    '''Moves all labels that are in the same node as the specified label to a
    list of labels in node. If size is specified, the list of labels in the node
    is shortened to contain only the size best (lowest cost) labels.
    '''

    # Initialize list of labels in node
    labels_in_node = [label]
    # Iterate over all given labels
    length = len(labels)
    for i in range(length):
        # Remove a the first label from the list of labels
        candidate = labels.pop(0)
        # If the label is in the node, add it to labelsInNode
        if candidate.node == label.node:
            labels_in_node.append(candidate)
        # Otherwise, add it back to labels (at end of list)
        else:
            labels.append(candidate)

    # If size is specified, sort and reduce the size of labels_in_node
    if size != None:
        labels_in_node = sorted(labels_in_node, key = lambda label: label.cost)
        labels_in_node = labels_in_node[:size]

    return labels, labels_in_node

def printMessage(nProcessedProblems, UBD, LBD, gap, time):
    '''Prints message based on branch and price progress.'''
    
    message = 'Processed nodes: %d' % nProcessedProblems
    message += ',\tUBD: '
    message += '%.2f' % UBD
    message += ',\tLBD: '
    message += '%.2f' % LBD
    message += ',\tGap: '
    message += '%.2f' % (gap * 100)
    message += '%'
    message += ',\tTotal time: %.2f' % time
    print(message)
