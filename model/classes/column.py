class Column:
    '''Representation of a restricted master problem column in the rostering
    problem of Pedersen and Coates (2019).
    '''

    def __init__(self, rosterline, employee, rosterlineNumber, data):
        # Fundamental attributes:
        self.rosterline = rosterline
        self.employee = employee
        self.rosterlineNumber = rosterlineNumber

        # Derived attributes:
        A, A_W, A_O, A_g, V, D, cost = self.calculateCoefficients(data = data)
        self.A = A
        self.A_W = A_W
        self.A_O = A_O
        self.A_g = A_g
        self.V = V
        self.D = D
        self.cost = cost
        self.feasible = None

    def __repr__(self):
        repr = ('Employee: ' + str(self.employee) + '\n'
             +  'Column: ' + str(self.rosterlineNumber) + '\n'
             +  'Rosterline: ' + str(self.rosterline) + '\n'
             +  'Cost: ' + str(self.cost) + '\n')
        return repr

    def calculateCoefficients(self, data):
        '''Function to calculate column coefficients'''

        # Unpack data
        for key in data:
            globals()[key] = data[key]

        # Initialize cost (to be accumulated in the following)
        cost = 0

        # A coefficients:
        A = dict.fromkeys([(self.employee, self.rosterlineNumber, d, s) for d in Days for s in ShiftTypes], 0)
        # Temporarily store previous shift type worked
        prev_s = 0
        # Iterate over days...
        for d in Days:
            # ...and shift types
            for s in ShiftTypes:
                # If the shift type is assingned on the day...
                if self.rosterline[d-1] == s:
                    # ...indicate shift assignment
                    A[(self.employee, self.rosterlineNumber, d, s)] = 1
                    # ...add the cost of assignment
                    cost += C[(self.employee,d,s)]
                    # ...add costs associated with two-day rewarded patterns
                    # Ensure shift types are working shifts and may be in pattern
                    if (self.employee in data['PatternsRewarded'] and
                        prev_s in data['ShiftTypesWorking'] and
                        s in data['ShiftTypesWorking']):
                        prevGroup = None # Group of previos shift type
                        curGroup = None # Group of current shift type
                        # Iterate over all employee relevant two-day rewarded patterns
                        for pat in data['PatternsRewarded'][self.employee]:
                            if (data['PatternDuration'][(self.employee,pat)] == 2 and
                                d in data['PatternDays'][(self.employee, pat)]):
                                # If not already done, identify the shift groups
                                if prevGroup == None:
                                    for shiftGroup in data['ShiftTypesGroup']:
                                        if (prev_s in
                                            data['ShiftTypesGroup'][shiftGroup]):
                                            prevGroup = shiftGroup
                                        if (s in
                                            data['ShiftTypesGroup'][shiftGroup]):
                                            curGroup = shiftGroup
                                # Check if the rewarded pattern is assigned
                                if (data['M'][(self.employee, pat, 1, prevGroup)] == 1 and
                                    data['M'][(self.employee, pat, 2, curGroup)] == 1):
                                    # If so, update the cost of the roster line
                                    cost -= data['R'][(self.employee, pat)]
                                    # Unique rewarded patterns are assumed
                                    break
                    # ...add costs associated with two-day penalized patterns
                    # Ensure shift types are working shifts and may be in pattern
                    if (self.employee in data['PatternsPenalized'] and
                          prev_s in data['ShiftTypesWorking'] and
                          s in data['ShiftTypesWorking']):
                        prevGroup = None # Group of previos shift type
                        curGroup = None # Group of current shift type
                        # Iterate over all employee relevant two-day penalized patterns
                        for pat in data['PatternsPenalized'][self.employee]:
                            if (data['PatternDuration'][(self.employee,pat)] == 2 and
                                d in data['PatternDays'][(self.employee, pat)]):
                                # If not already done, identify the shift groups
                                if prevGroup == None:
                                    for shiftGroup in data['ShiftTypesGroup']:
                                        if (prev_s in
                                            data['ShiftTypesGroup'][shiftGroup]):
                                            prevGroup = shiftGroup
                                        if (s in
                                            data['ShiftTypesGroup'][shiftGroup]):
                                            curGroup = shiftGroup
                                # Check if the rewarded pattern is assigned
                                if (data['M'][(self.employee, pat, 1, prevGroup)] == 1 and
                                    data['M'][(self.employee, pat, 2, curGroup)] == 1):
                                    # If so, update the cost of the rosterline
                                    cost += data['P'][(self.employee, pat)]
                                    # Unique penalized patterns are assumed
                                    break
                    # One shift type assigned per day is assumed
                    break
            # Update the previos shift type worked
            prev_s = s

        # A_W, A_O and A_g coefficients:
        # Initialize dictionaries assuming all assigned shifts are working shifts
        A_W = dict.fromkeys([(self.employee, self.rosterlineNumber, d) for d in Days], 1)
        A_O = dict.fromkeys([(self.employee, self.rosterlineNumber, d) for d in Days], 0)
        A_g = dict.fromkeys([(self.employee, self.rosterlineNumber, d, g) for d in Days for g in ShiftGroups], 0)
        # Iterate over days
        for d in Days:
            # Check whether assigned shift is off or working
            if self.rosterline[d-1] in ShiftTypesOff:
                A_W[(self.employee, self.rosterlineNumber, d)] = 0
                A_O[(self.employee, self.rosterlineNumber, d)] = 1
            else:
                # If the shift is a working shift, identify the shift group
                for g in ShiftGroups:
                    if self.rosterline[d-1] in ShiftTypesGroup[g]:
                        A_g[(self.employee, self.rosterlineNumber, d, g)] = 1
                        # One shift type assigned per day is assumed along with
                        # disjoint shift groups
                        break

        # V coefficients
        V = dict.fromkeys([(self.employee, self.rosterlineNumber, d) for d in Days], 0)
        # Iterate over all days but the first, assuming no reduced rest is
        # incurred on the first day
        for d in Days[1:]:
            # Note the reduced rest penalty if it is incurred
            if self.rosterline[d-2] in FollowingShiftsPenalty:
                if self.rosterline[d-1] in FollowingShiftsPenalty[self.rosterline[d-2]]:
                    V[(self.employee, self.rosterlineNumber, d)] = 1
                    cost += C_R

        # D coefficients
        D = dict.fromkeys([(self.employee, self.rosterlineNumber, d) for d in NormPeriodStartDays], 0)
        # Iterate over all workload norm period start days
        for d in NormPeriodStartDays:
            # Initialize the norm period workload
            D[(self.employee, self.rosterlineNumber, d)] = 0
            # Iterate over the days in the norm period
            for dd in range(d,d+N_N):
                # Identify the shift type assigned (if working)
                for s in ShiftTypesWorking:
                    if self.rosterline[dd-1] == s:
                        # Update the norm period workload
                        D[(self.employee, self.rosterlineNumber, d)] += T[s]
                        # One assignment per day is assumed
                        break

        return A, A_W, A_O, A_g, V, D, cost

    def reducedCost(self, graph, data):
        '''Calculate the reduced cost of the column'''

        # Initialize cost
        redCost = 0

        # Iterate over all arcs in the graph
        for prev_shift in graph.nodes:
            for cur_shift in prev_shift.neighbors:
                day = cur_shift.day
                # Skip the arc to the end node (as it bears no cost)
                if day != data['Days'][-1] + 1:
                    # If the shift (destination node) is assigned in the roster line
                    if cur_shift.shiftType == self.rosterline[day - 1]:
                        # If first day, set default previous shift type
                        if day == data['Days'][0]:
                            redCost += graph.costs[(prev_shift, cur_shift)]
                        # Else, set cost based on previos shift
                        elif self.rosterline[day - 2] == prev_shift.shiftType:
                            redCost += graph.costs[(prev_shift, cur_shift)]

        return redCost

    def checkMasterFeasible(self, data):
        '''Checks if the column is master feasible'''
        # Only check if column not already checked
        if self.feasible == None:
            # Assume infeasible
            self.feasible = False

            # Initialize counters for constraints
            # Consecutive days working
            consecutiveDaysWorking = 0
            # Reduced rest
            reducedRest = dict.fromkeys((d for d in range(data['D_R'])),0)
            # Strict days off
            strictDaysOff = dict.fromkeys((d for d in range(data['D_S'])),0)
            # Workload
            workload = 0
            # Illegal patterns
            if self.employee in data['PatternsIllegal']:
                illegalPatterns = dict.fromkeys(((pat,d) for pat in data['PatternsIllegal'][self.employee]
                                                         for d in data['Days']),0)
            else:
                illegalPatterns = {}


            # Iterate through rosterline
            for day in data['Days']:
                # Retrieve shift type
                shiftType = self.rosterline[day - 1]

                # Update counters
                # Consecutive days working
                if shiftType in data['ShiftTypesWorking']:
                    consecutiveDaysWorking += 1
                else:
                    consecutiveDaysWorking = 0
                # Reduced rest
                for index in reducedRest:
                    if day % data['D_R'] == index:
                        reducedRest[index] = 0
                    if (day >= 2 and
                        self.rosterline[day - 2] in FollowingShiftsPenalty
                        and shiftType in FollowingShiftsPenalty[self.rosterline[day - 2]]):
                        reducedRest[index] += 1
                # Strict days off
                # Check if day is strict day off
                if shiftType in ShiftTypesOff:
                    # Assume strict day off
                    SDO = True
                    # Check if not one strict day off
                    if (day > data['Days'][0] and day < data['Days'][-1]
                        and self.rosterline[day - 2] in data['StrictDayOff1']
                        and self.rosterline[day] in data['StrictDayOff1'][self.rosterline[day - 2]]):
                        SDO = False
                    elif (day > data['Days'][0] and day < data['Days'][-2]
                          and self.rosterline[day] in ShiftTypesOff
                          and self.rosterline[day - 2] in data['StrictDayOff2']
                          and self.rosterline[day+1] in data['StrictDayOff2'][self.rosterline[day - 2]]):
                        SDO = False
                else:
                    SDO = False
                for index in strictDaysOff:
                    if day % data['D_S'] == index:
                        strictDaysOff[index] = 0
                    if SDO:
                        strictDaysOff[index] += 1
                # Workload
                if day in data['NormPeriodStartDays'] and shiftType not in data['ShiftTypesOff']:
                    workload = data['T'][shiftType]
                elif shiftType not in data['ShiftTypesOff']:
                    workload += data['T'][shiftType]
                # Illegal Patterns
                # Find shift group
                shiftGroup = None
                found = False
                for g in data['ShiftGroups']:
                    for s in data['ShiftTypesGroup'][g]:
                        if shiftType == s:
                            shiftGroup = g
                            found = True
                            break
                    if found:
                        break
                # Update counter
                # Only update if working shift
                if not shiftGroup == None:
                    # Iterate over patterns if employee has illegal patterns
                    if self.employee in data['PatternsIllegal']:
                        for pat in data['PatternsIllegal'][self.employee]:
                            # Iterate over days with patterns that can include the current day
                            for d in range(day - data['PatternDuration'][(self.employee, pat)] + 1, day):
                                # Update counter if correct shift group is worked
                                if d >= 1 and data['M'][(self.employee, pat, day - d + 1, shiftGroup)] == 1:
                                    illegalPatterns[(pat, d)] += 1
                            # If at the start day: update only if we are on a possible start day of pattern
                            if day in data['PatternDays'][(self.employee, pat)]:
                                if data['M'][(self.employee, pat, 1, shiftGroup)] == 1:
                                    illegalPatterns[(pat, day)] += 1


                # Check feasibility
                # Consecutive days working
                if consecutiveDaysWorking > data['Nmax']:
                    return
                # Reduced rest
                for index in reducedRest:
                    if reducedRest[index] > data['Nmax_R']:
                        return
                # Strict days off
                for index in strictDaysOff:
                    if day >= data['D_S'] and (day + 1) % data['D_S'] == index:
                        if strictDaysOff[index] < data['Nmin_S']:
                            return
                # Workload
                if day - data['N_N'] + 1 in data['NormPeriodStartDays']:
                    if workload < data['W_N'] * data['H_W'][self.employee] - WMax_minus[self.employee]:
                        return
                    elif workload > data['W_N'] * data['H_W'][self.employee] + WMax_plus[self.employee]:
                        return
                # Illegal patterns
                if self.employee in data['PatternsIllegal']:
                    for pat in data['PatternsIllegal'][self.employee]:
                        # Entry in counter to check
                        dayCheck = day-data['PatternDuration'][(self.employee, pat)]+1
                        # Day check must be greater than 1
                        if dayCheck >= 1:
                            # If all days in pattern was worked: return
                            if illegalPatterns[(pat, dayCheck)] >= data['PatternDuration'][(self.employee, pat)]:
                                return


            # Set feasible if no constraints violated
            self.feasible = True
            return
