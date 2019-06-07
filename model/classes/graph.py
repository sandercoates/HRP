from node import Node

class Graph:
    '''Directed graph represented by nodes (dependent on Node class), arc costs
    stored in dictionary indexed by origin-destination tuple. Implementation
    for SPPRC'''

    def __init__(self, data, employee):
        '''Start with empty graph'''
        # Represented by array of nodes...
        self.nodes = []
        # ...and dictionary of (arc) costs
        self.costs = {}

        '''Find shift types that can be assigned to the employee, given the
        skill level of the employee and requirement of the shift type.
        '''
        # Initialize list of shift types that may be assigned
        EmployeeShiftTypes = []
        # Iterate over working shift types
        for shiftType in data['ShiftTypesWorking']:
            # Iterate over the skill qualifications of the shift type
            for requiredSkill in data['SkillsShiftType'][shiftType]:
                # If the qualification is amongst the employee's
                if requiredSkill in data['SkillsEmployee'][employee]:
                    # Add the shift type to the list and continue to next shift
                    EmployeeShiftTypes.append(shiftType)
        # Add off shifts that can be worked by all employees
        EmployeeShiftTypes += [s for s in data['ShiftTypesOff']]

        '''Add start node'''
        name = 1
        initial_node = Node(name = name, day = 0, shiftType = 0)
        self.add_node(initial_node)

        '''Add rest of graph'''
        # Initialize list for storing nodes of previos day
        prevNodes = [initial_node]
        # Create nodes other than start and end nodes, add arcs
        for day in data['Days']:
            curNodes = []
            for shiftType in EmployeeShiftTypes:
                name += 1
                curNode = Node(name = name, day = day, shiftType = shiftType)
                curNodes.append(curNode)
                # Add arcs from previous day nodes if conditions satisfied
                for prevNode in prevNodes:
                    # Add cost of working shift to arc
                    arc_cost = data['C'][(employee, curNode.day, curNode.shiftType)]
                    # Disregard all but cost of working for artificial origin
                    # or destination
                    if prevNode.shiftType != 0 and curNode.shiftType != 0:
                        # Required rest
                        if (prevNode.shiftType in data['FollowingShiftsIllegal'] and
                            curNode.shiftType in data['FollowingShiftsIllegal'][prevNode.shiftType]):
                            continue
                        # Add cost of reduced rest to arc
                        if (prevNode.shiftType in data['FollowingShiftsPenalty']
                            and curNode.shiftType in
                            data['FollowingShiftsPenalty'][prevNode.shiftType]):
                            arc_cost += data['C_R']
                        # Both or none weekend days working
                        if (curNode.day in data['DaysOnWeekday']['SUN'] and
                              ((prevNode.shiftType in data['ShiftTypesWorking'] and
                                curNode.shiftType in data['ShiftTypesOff']) or
                              (prevNode.shiftType in data['ShiftTypesOff'] and
                               curNode.shiftType in data['ShiftTypesWorking']))):
                                continue
                        # No Friday night shift before free weekend
                        if (curNode.day in data['DaysOnWeekday']['SAT'] and
                              prevNode.shiftType in data['ShiftTypesWorking'] and
                              data['T_E'][prevNode.shiftType] > data['H'] and
                              curNode.shiftType in data['ShiftTypesOff']):
                              continue
                        # Two day illegal patterns
                        # Ensure shift types are working shifts and may be in pattern
                        if (employee in data['PatternsIllegal'] and
                            prevNode.shiftType in data['ShiftTypesWorking'] and
                            curNode.shiftType in data['ShiftTypesWorking']):
                            illegalPatternFound = False
                            prevGroup = None # Group of previos shift type
                            curGroup = None # Group of current shift type
                            for pat in data['PatternsIllegal'][employee]:
                                if (data['PatternDuration'][(employee,pat)] == 2 and
                                    prevNode.day in data['PatternDays'][(employee, pat)]):
                                    # If not already done, identify shift groups assigned
                                    if prevGroup == None:
                                        for shiftGroup in data['ShiftTypesGroup']:
                                            if (prevNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                prevGroup = shiftGroup
                                            if (curNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                curGroup = shiftGroup
                                    # Check if illegal pattern is found
                                    if (data['M'][(employee, pat, 1, prevGroup)] == 1 and
                                        data['M'][(employee, pat, 2, curGroup)] == 1):
                                        illegalPatternFound = True
                                        break
                            # Do not create arc if an illegal pattern was found
                            if illegalPatternFound:
                                continue
                        # Two day rewarded patterns
                        # Ensure shift types are working shifts and may be in pattern
                        if (employee in data['PatternsRewarded'] and
                            prevNode.shiftType in data['ShiftTypesWorking'] and
                            curNode.shiftType in data['ShiftTypesWorking']):
                            prevGroup = None # Group of previos shift type
                            curGroup = None # Group of current shift type
                            for pat in data['PatternsRewarded'][employee]:
                                if (data['PatternDuration'][(employee,pat)] == 2 and
                                    prevNode.day in data['PatternDays'][(employee, pat)]):
                                    # If not already done, identify shift groups assigned
                                    if prevGroup == None:
                                        for shiftGroup in data['ShiftTypesGroup']:
                                            if (prevNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                prevGroup = shiftGroup
                                            if (curNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                curGroup = shiftGroup
                                    # Check if rewarded/penalized pattern is found
                                    if (data['M'][(employee, pat, 1, prevGroup)] == 1 and
                                        data['M'][(employee, pat, 2, curGroup)] == 1):
                                        # Change arc cost
                                        arc_cost -= data['R'][(employee, pat)]
                                        # Assume there are no identical rewarded patterns
                                        break
                        # Two day penalized patterns
                        # Ensure shift types are working shifts and may be in pattern
                        if (employee in data['PatternsPenalized'] and
                              prevNode.shiftType in data['ShiftTypesWorking'] and
                              curNode.shiftType in data['ShiftTypesWorking']):
                            prevGroup = None # Group of previos shift type
                            curGroup = None # Group of current shift type
                            for pat in data['PatternsPenalized'][employee]:
                                if (data['PatternDuration'][(employee,pat)] == 2 and
                                    prevNode.day in data['PatternDays'][(employee, pat)]):
                                    # If not already done, identify shift groups assigned
                                    if prevGroup == None:
                                        for shiftGroup in data['ShiftTypesGroup']:
                                            if (prevNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                prevGroup = shiftGroup
                                            if (curNode.shiftType in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                curGroup = shiftGroup
                                    # Check if rewarded/penalized pattern is found
                                    if (data['M'][(employee, pat, 1, prevGroup)] == 1 and
                                        data['M'][(employee, pat, 2, curGroup)] == 1):
                                        # Change arc cost
                                        arc_cost += data['P'][(employee, pat)]
                                        # Assume there are no identical penalized patterns
                                        break

                    self.add_arc(origin=prevNode, destination=curNode, cost=arc_cost)
            prevNodes = curNodes

        # Create end node, add arcs
        node = Node(name = name + 1, day = data['Days'][-1] + 1, shiftType = 0)
        # Add node to graph
        self.add_node(node)
        # Add arcs from previous day nodes to end node
        for prevNode in prevNodes:
            # Add arc to graph
            self.add_arc(origin=prevNode, destination=node)

    def __repr__(self):
        return str(self.nodes)

    def add_node(self, node: Node):
        '''Add node (and neighbors) to graph. Ignore if node already exists'''
        if node not in self.nodes:
            self.nodes.append(node)
            # Recursively add neighbors
            for neighbor in node.neighbors:
                self.add_node(neighbor)
                # Add default costs
                self.costs[(node, neighbor)] = 0

    def add_arc(self, origin: Node, destination: Node, cost: float = None):
        '''Add arc to graph (change neighborhoods in graph)'''
        # Add origin/destination to graph if not present
        if origin not in self.nodes:
            self.add_node(origin)
        if destination not in self.nodes:
            self.add_node(destination)
        # Add destination to origin's neighborhood
        if destination not in origin.neighbors:
            origin.neighbors.append(destination)
        # Add cost to graph, no input default is zero
        if cost == None:
            cost = 0
        self.costs[(origin, destination)] = cost

    def remove_arc(self, origin: Node, destination: Node):
        '''Remove arc from graph (change neighborhoods in graph)'''
        # Ensure origin is in graph (do nothing if not)
        if origin not in self.nodes:
            return
        # Ensure destination is in origin neighborhood (do nothing if not)
        if destination not in origin.neighbors:
            return
        # Remove destination from origin neighborhood
        origin.neighbors.remove(destination)
        # Remove cost from graph
        self.costs.pop((origin, destination))

    def remove_node(self, node: Node, delete_object=False):
        '''Remove node from graph (all references to node), and object if
        specified.
        Alternative implementation is by defining incoming neighbors for
        all nodes
        '''
        # Ensure node is in graph (do nothing if not)
        if node not in self.nodes:
            return
        # Remove all arcs to node
        for origin in self.nodes: # Iterate over all nodes in graph
            try:
                origin.neighbors.remove(node) # Remove node if in neighborhood
                self.costs.pop((origin, node))
            except:
                pass # Do nothing if not
        # Remove all arc costs from node
        for neighbor in node.neighbors:
            self.costs.pop((node, neighbor))
        # Remove node from graph
        self.nodes.remove(node)
        # Delete object if specified in input
        if delete_object:
            del node

    def remove_nodeOnShift(self, node: Node, delete_object = False):
        '''Removes node in graph on the same day and shift types as node. This is
        necessary because one can input a node not in the graph, but with the
        same day and shiftType as the branching node'''

        for nodeTest in self.nodes:
            if nodeTest.day == node.day and nodeTest.shiftType == node.shiftType:
                node_remove = nodeTest
                break
        self.remove_node(node = node_remove)

    def remove_nodesOnSameDay(self, node: Node, delete_object = False):
        '''Remove all nodes on the same day as node from graph
        (except the node itself))'''
        nodes_remove = []
        for node_remove in self.nodes:
            if node_remove.day == node.day and node_remove.shiftType != node.shiftType:
                nodes_remove.append(node_remove)
        while nodes_remove:
            node_remove = nodes_remove.pop()
            self.remove_node(node = node_remove)

    '''Hereunder all functions regarding costs.

    Costs are updated based on dual variables by the functions:

        def update_dual_name(name,
                             day,
                             prev_shift_type,
                             cur_shift_type,
                             data):
            dual = 0
            # ...
            return dual

    Allowed dual variables are MaxConsecDaysWorking, MaxConsecDaysWorkingGroup,
    MinConsecDaysWorking, MinConsecDaysWorkingGroup, MaxReducedRest,
    MinWeekendsOff, StrictDaysOff, StrictDayOff1, StrictDayOff2, WorkLoad_plus,
    WorkLoad_minus, RewardedPatterns, PenalizedPatterns, IllegalPatterns.
    '''

    def update_arc_cost(self, origin: Node, destination: Node, cost):
        '''Update the cost associated with the arc from origin to destination'''
        # Ensure origin is in graph (do nothing if not)
        if origin not in self.nodes:
            return
        # Ensure destination is in origin neighborhood (do nothing if not)
        if destination not in origin.neighbors:
            return
        # Update cost
        self.costs[(origin, destination)] = cost

    def update_costs(self, dual_variables, data, employee,
                     constructionHeuristic = False):
        '''Update all costs in the graph based on the input dual variables'''
        # Iterate over all arcs in the graph
        for origin in self.nodes:
            for destination in origin.neighbors:
                day = destination.day
                # Update costs if not on arcs going into end node
                if day != data['Days'][-1] + 1:
                    prev_shift_type = origin.shiftType
                    cur_shift_type = destination.shiftType
                    cost = 0
                    # If not constructionHeuristic: add costs from objective function
                    if not constructionHeuristic:
                        # Add cost of working shift type
                        cost += data['C'][(employee, day, cur_shift_type)]
                        # Add cost of reduced rest
                        if ((prev_shift_type in data['FollowingShiftsPenalty']) and
                            (cur_shift_type in
                            data['FollowingShiftsPenalty'][prev_shift_type])):
                            cost += data['C_R']
                        # Add cost of two-day rewarded patterns
                        # Ensure shift types are working shifts and may be in pattern
                        if (employee in data['PatternsRewarded'] and
                            prev_shift_type in data['ShiftTypesWorking'] and
                            cur_shift_type in data['ShiftTypesWorking']):
                            prevGroup = None # Group of previos shift type
                            curGroup = None # Group of current shift type
                            for pat in data['PatternsRewarded'][employee]:
                                if (data['PatternDuration'][(employee,pat)] == 2 and
                                    day in data['PatternDays'][(employee, pat)]):
                                    # If not already done, identify shift groups assigned
                                    if prevGroup == None:
                                        for shiftGroup in data['ShiftTypesGroup']:
                                            if (prev_shift_type in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                prevGroup = shiftGroup
                                            if (cur_shift_type in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                curGroup = shiftGroup
                                    # Check if rewarded/penalized pattern is found
                                    if (data['M'][(employee, pat, 1, prevGroup)] == 1 and
                                        data['M'][(employee, pat, 2, curGroup)] == 1):
                                        # Change arc cost
                                        cost -= data['R'][(employee, pat)]
                                        # Assume there are no identical rewarded patterns
                                        break
                        # Add cost of two-day penalized patterns
                        # Ensure shift types are working shifts and may be in pattern
                        if (employee in data['PatternsPenalized'] and
                              prev_shift_type in data['ShiftTypesWorking'] and
                              cur_shift_type in data['ShiftTypesWorking']):
                            prevGroup = None # Group of previos shift type
                            curGroup = None # Group of current shift type
                            for pat in data['PatternsPenalized'][employee]:
                                if (data['PatternDuration'][(employee,pat)] == 2 and
                                    day in data['PatternDays'][(employee, pat)]):
                                    # If not already done, identify shift groups assigned
                                    if prevGroup == None:
                                        for shiftGroup in data['ShiftTypesGroup']:
                                            if (prev_shift_type in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                prevGroup = shiftGroup
                                            if (cur_shift_type in
                                                data['ShiftTypesGroup'][shiftGroup]):
                                                curGroup = shiftGroup
                                    # Check if rewarded/penalized pattern is found
                                    if (data['M'][(employee, pat, 1, prevGroup)] == 1 and
                                        data['M'][(employee, pat, 2, curGroup)] == 1):
                                        # Change arc cost
                                        cost += data['P'][(employee, pat)]
                                        # Assume there are no identical penalized patterns
                                        break
                    # Add dual varibale objective function terms
                    for v in dual_variables:
                        dual_variable = dual_variables[v]
                        cost += getattr(self, 'update_dual_%s' % v)(dual_variable,
                                                                    day,
                                                                    prev_shift_type,
                                                                    cur_shift_type,
                                                                    data,
                                                                    employee)
                    self.update_arc_cost(origin, destination, cost)

    def update_dual_pi(self, pi, day, prev_shift_type, cur_shift_type, data,
                       employee):
        '''Demand coverage'''
        # See the thesis for mathematical details
        if cur_shift_type in data['ShiftTypesWorking']:
            return -pi[(day, cur_shift_type)]
        return 0

    def update_dual_omega(self, omega, day, prev_shift_type, cur_shift_type,
                          data, employee):
        '''Convexity'''
        # See the thesis for mathematical details
        dual = 0
        if day == data['Days'][0]:
            dual -= omega[employee]
        return dual

    def update_dual_alpha_W(self, alpha_W, day, prev_shift_type, cur_shift_type,
                            data, employee):
        '''Maximum consecutive days working'''
        # See the thesis for mathematical details
        dual = 0
        for d in data['Days']:
            if d <= data['Days'][-1]-data['Nmax']:
                if ((day in range(d, d + data['Nmax'] + 1)) and
                    (cur_shift_type in data['ShiftTypesWorking'])):
                    dual -= alpha_W[(employee, d)]
        return dual

    def update_dual_alpha(self, alpha, day, prev_shift_type, cur_shift_type,
                          data, employee):
        '''MaxConsecDaysWorkingGroup'''
        # See the thesis for mathematical details
        dual = 0
        for g in data['ShiftGroups']:
            for d in data['Days']:
                if d <= data['Days'][-1] - data['NmaxGroup'][g]:
                    if (day in range(d, d + data['NmaxGroup'][g] + 1)
                        and cur_shift_type in data['ShiftTypesGroup'][g]):
                        dual -= alpha[(employee, d, g)]
        return dual

    def update_dual_gamma(self, gamma, day, prev_shift_type, cur_shift_type,
                          data, employee):
        '''MaxReducedRest'''
        # See the thesis for mathematical details
        dual = 0
        for d in data['Days']:
            if d <= data['Days'][-1]-data['D_R']+1:
                if (day in range(d, d + data['D_R']) and
                    prev_shift_type in data['FollowingShiftsPenalty'] and
                    cur_shift_type in data['FollowingShiftsPenalty'][prev_shift_type]):
                    dual -= gamma[(employee, d)]
        return dual

    def update_dual_epsilon_0(self, epsilon_0, day, prev_shift_type,
                              cur_shift_type, data, employee):
        '''StrictDaysOff'''
        # See the thesis for mathematical details
        for d in data['Days']:
            if day == d and cur_shift_type in data['ShiftTypesOff']:
                return epsilon_0[(employee, day)]
        return 0


    def update_dual_epsilon_1(self, epsilon_1, day, prev_shift_type,
                              cur_shift_type, data, employee):
        '''StrictDaysOff1'''
        # See the thesis for mathematical details
        dual = 0
        for d in data['Days']:
            if d in range(2, data['Days'][-1]):
                if (day == d-1 and
                    cur_shift_type in data['StrictDayOff1']):
                    for s2 in data['StrictDayOff1'][cur_shift_type]:
                        dual -= epsilon_1[(employee, d, cur_shift_type, s2)]
                if day == d+1:
                    for s1 in data['StrictDayOff1']:
                        if cur_shift_type in data['StrictDayOff1'][s1]:
                            dual -= epsilon_1[(employee, d, s1, cur_shift_type)]
        return dual

    def update_dual_epsilon_2(self, epsilon_2, day, prev_shift_type,
                              cur_shift_type, data, employee):
        '''StrictDaysOff2'''
        # See the thesis for mathematical details
        dual = 0
        for d in data['Days']:
            if d in range(2, data['Days'][-1] - 1):
                if (day == d-1 and
                    cur_shift_type in data['StrictDayOff2']):
                    for s2 in data['StrictDayOff2'][cur_shift_type]:
                        dual -= epsilon_2[(employee, d, cur_shift_type, s2)]
                if day == d+2:
                    for s1 in data['StrictDayOff2']:
                        if cur_shift_type in data['StrictDayOff2'][s1]:
                            dual -= epsilon_2[(employee, d, s1, cur_shift_type)]
        return dual

    def update_dual_zeta(self, zeta, day, prev_shift_type, cur_shift_type,
                         data, employee):
        '''Workload'''
        # See the thesis for mathematical details
        for d in data['NormPeriodStartDays']:
            if day in range(d, d + data['N_N']):
                if cur_shift_type in data['ShiftTypesWorking']:
                    return -data['T'][cur_shift_type] * zeta[(employee, d)]
                else:
                    return 0

    def update_dual_theta_R(self, theta_R, day, prev_shift_type, cur_shift_type,
                            data, employee):
        '''RewardedPatterns'''
        # See the thesis for mathematical details
        dual = 0
        if employee in data['PatternsRewarded']:
            for p in data['PatternsRewarded'][employee]:
                if data['PatternDuration'][(employee,p)] > 2:
                    for dd in data['WeekdaysStartPattern'][(employee, p)]:
                        for d in data['DaysOnWeekday'][dd]:
                            if d <= data['Days'][-1] - data['PatternDuration'][(employee, p)] + 1:
                                if day - d + 1 in range(1, data['PatternDuration'][(employee, p)] + 1):
                                    for g in data['ShiftGroups']:
                                        if data['M'][(employee, p, day - d + 1, g)] == 1:
                                            if cur_shift_type in data['ShiftTypesGroup'][g]:
                                                dual -= theta_R[(employee, p, d, day - d + 1)]
        return dual

    def update_dual_theta_P(self, theta_P, day, prev_shift_type, cur_shift_type,
                            data, employee):
        '''PenalizedPatterns'''
        # See the thesis for mathematical details
        dual = 0
        if employee in data['PatternsPenalized']:
            for p in data['PatternsPenalized'][employee]:
                if data['PatternDuration'][(employee,p)] > 2:
                    for dd in data['WeekdaysStartPattern'][(employee, p)]:
                        for d in data['DaysOnWeekday'][dd]:
                            if d <= data['Days'][-1] - data['PatternDuration'][(employee, p)] + 1:
                                if day - d + 1 in range(1, data['PatternDuration'][(employee, p)] + 1):
                                    for g in data['ShiftGroups']:
                                        if data['M'][(employee, p, day - d + 1, g)] == 1:
                                            if cur_shift_type in data['ShiftTypesGroup'][g]:
                                                dual -= theta_P[(employee, p, d)]
        return dual

    def update_dual_theta_I(self, theta_I, day, prev_shift_type, cur_shift_type,
                            data, employee):
        '''IllegalPatterns'''
        # See the thesis for mathematical details
        dual = 0
        if employee in data['PatternsIllegal']:
            for p in data['PatternsIllegal'][employee]:
                if data['PatternDuration'][(employee,p)] > 2:
                    for dd in data['WeekdaysStartPattern'][(employee, p)]:
                        for d in data['DaysOnWeekday'][dd]:
                            if d <= data['Days'][-1] - data['PatternDuration'][(employee, p)] + 1:
                                if day - d + 1 in range(1, data['PatternDuration'][(employee, p)] + 1):
                                    for g in data['ShiftGroups']:
                                        if data['M'][(employee, p, day - d + 1, g)] == 1:
                                            if cur_shift_type in data['ShiftTypesGroup'][g]:
                                                dual -= theta_I[(employee, p, d)]
        return dual
