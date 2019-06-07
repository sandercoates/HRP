import xpress as xp
import pickle
import time

def solveMIP(data, outputPrint = True, problemName = 'MIP',
             heuristicOnly = False, coverConstraint = '=',
             outputPickle = None, timeLimit = None,
             gapLimit = None):
    '''This is the MIP of the full roster problem in the master
    thesis of Sander Coates and Vegard Pedersen. The function takes as input
    instance data and returns feasibility (boolean), the objective value and
    the solution (in assignment x-variables).
    '''

    # Initialize time
    start = time.time()

    '''Unpack data'''
    for key in data:
        globals()[key] = data[key]

    '''Pre-processing'''
    # Find employee shift types (based on skills of employees and shifts)
    EmployeeShiftTypes = {}
    for e in Employees:
        # Initialize list of shift types that may be assigned to the employee
        EmployeeShiftTypes[e] = []
        # Iterate over working shift types
        for s in ShiftTypesWorking:
            # Iterate over the skill qualifications of the shift type
            for requiredSkill in SkillsShiftType[s]:
                # If the qualification is amongst the employee's
                if requiredSkill in SkillsEmployee[e]:
                    # Add the shift type to the list and continue to next shift
                    EmployeeShiftTypes[e].append(s)
        # Add off shifts that can be worked by all employees
        EmployeeShiftTypes[e] += [s for s in ShiftTypesOff]

    '''Setup'''
    p = xp.problem(name = problemName)
    p.controls.outputlog = outputPrint
    # If only heuristic search: set max nodes to 0 in B&B tree
    if heuristicOnly:
        p.setControl('maxnode', 0)
    # If time limit is input, set control
    if timeLimit != None:
        p.setControl('maxtime', -timeLimit)
    # If optimality gap limit is input, set control
    if gapLimit != None:
        p.setControl('miprelstop', gapLimit)

    '''Variables'''
    # Assignment
    x = dict.fromkeys((e,d,s) for e in Employees
                              for d in Days
                              for s in ShiftTypes)
    for e in Employees:
        for d in Days:
            for s in ShiftTypes:
                if s in EmployeeShiftTypes[e]:
                    x[(e,d,s)] = xp.var(vartype = xp.binary,
                                        name = 'x({},{},{})'.format(e,d,s))
                # Set variable to zero if it cannot be assigned to the employee
                else:
                    x[(e,d,s)] = xp.var(vartype = xp.binary,
                                        name = 'x({},{},{})'.format(e,d,s),
                                        ub = 0)

    # Over- and undercoverage
    wPlus = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    wMinus = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    for s in ShiftTypesWorking:
        for d in Days:
            wPlus[(d,s)] = xp.var(vartype = xp.continuous,
                                  name = 'w_plus({},{})'.format(d,s),
                                  ub = OvercoverageLimit[(d,s)])
            wMinus[(d,s)] = xp.var(vartype = xp.continuous,
                                   name = 'w_minus({},{})'.format(d,s),
                                   ub = UndercoverageLimit[(d,s)])

    # Reduced rest
    v = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            v[(e,d)] = xp.var(vartype = xp.binary,
                              name = 'v({},{})'.format(e,d))

    # s-variables
    strict = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            strict[(e,d)] = xp.var(vartype = xp.binary,
                                   name = 's({},{})'.format(e,d))

    # Over- and undertime
    u_plus = dict.fromkeys((e,d) for e in Employees
                                 for d in NormPeriodStartDays)
    u_minus = dict.fromkeys((e,d) for e in Employees
                                  for d in NormPeriodStartDays)
    for e in Employees:
        for d in NormPeriodStartDays:
            u_plus[(e,d)] = xp.var(vartype = xp.continuous,
                                   name = 'u_plus({},{})'.format(e,d),
                                   ub = WMax_plus[e])
            u_minus[(e,d)] = xp.var(vartype = xp.continuous,
                                    name = 'u_minus({},{})'.format(e,d),
                                    ub = WMax_minus[e])

    # m-variables
    keyVec1 = [(e,pat,d) for e in Employees if e in PatternsRewarded.keys()
                         for pat in PatternsRewarded[e]
                         for d in PatternDays[(e,pat)]]
    keyVec2 = [(e,pat,d) for e in Employees if e in PatternsPenalized.keys()
                         for pat in PatternsPenalized[e]
                         for d in PatternDays[(e,pat)]]
    keyVec = keyVec1 + keyVec2
    m = dict.fromkeys(keyVec)
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                for d in PatternDays[(e,pat)]:
                    m[(e,pat,d)] = xp.var(vartype = xp.binary,
                                            name = 'm({},{},{})'.format(e,pat,d))
        if e in PatternsPenalized.keys():
            for pat in PatternsPenalized[e]:
                for d in PatternDays[(e,pat)]:
                    m[(e,pat,d)] = xp.var(vartype = xp.binary,
                                            name = 'm({},{},{})'.format(e,pat,d))

    # Add variables to problem
    p.addVariable(x, wPlus, wMinus, v, strict, u_plus, u_minus, m)

    '''Objective function'''
    p.setObjective(sense = xp.minimize, objective =
        # Cost of assignment to shift
        xp.Sum([C[(e,d,s)] * x[(e,d,s)] for e in Employees
                                        for d in Days
                                        for s in EmployeeShiftTypes[e]])
        # Cost of overcoverage
        + xp.Sum([OvercoverageCost[(d,s)] * wPlus[(d,s)] for d in Days
                                                         for s in ShiftTypesWorking])
        # Cost of undercoverage
        + xp.Sum([UndercoverageCost[(d,s)] * wMinus[(d,s)] for d in Days
                                                           for s in ShiftTypesWorking])
        # Cost of reduced rest
        + xp.Sum([C_R * v[(e,d)] for e in Employees for d in Days])
        # Cost of overtime
        + xp.Sum([OvertimeCost[e] * u_plus[(e,d)] for e in Employees
                                                  for d in NormPeriodStartDays])
        # Cost of undertime
        + xp.Sum([UndertimeCost[e] * u_minus[(e,d)] for e in Employees
                                                    for d in NormPeriodStartDays])
        # Cost of penalized patterns
        + xp.Sum([P[(e,pat)] * m[(e,pat,d)] for e in Employees
                                            if e in PatternsPenalized.keys()
                                            for pat in PatternsPenalized[e]
                                            for d in PatternDays[(e,pat)]])
        # (Negative) Cost of rewarded patterns
        - xp.Sum([R[(e,pat)] * m[(e,pat,d)] for e in Employees
                                            if e in PatternsRewarded.keys()
                                            for pat in PatternsRewarded[e]
                                            for d in PatternDays[(e,pat)]])
    )

    '''Constraints'''
    # Demand coverage
    demandCoverage = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    for d in Days:
        for s in ShiftTypesWorking:
            if coverConstraint == '>=':
                demandCoverage[(d,s)] = xp.constraint(
                name = 'demandCoverage({},{})'.format(d,s),
                constraint = xp.Sum([x[(e,d,s)] for e in Employees])
                             + wMinus[(d,s)] - wPlus[(d,s)] >= Demand[(d,s)]
                )
            else:
                demandCoverage[(d,s)] = xp.constraint(
                name = 'demandCoverage({},{})'.format(d,s),
                constraint = xp.Sum([x[(e,d,s)] for e in Employees])
                             + wMinus[(d,s)] - wPlus[(d,s)] == Demand[(d,s)]
                )

    # One shift per day
    oneShift = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            oneShift[(e,d)] = xp.constraint(
            name = 'oneShift({},{})'.format(e,d),
            constraint = xp.Sum([x[(e,d,s)] for s in EmployeeShiftTypes[e]]) == 1
            )

    # Maximum consecutive days working
    maxConsecutiveDays = dict.fromkeys((e,d) for e in Employees
                                             for d in Days if d <= nDays - Nmax)
    for e in Employees:
        for d in Days:
            if d <= nDays - Nmax:
                maxConsecutiveDays[(e,d)] = xp.constraint(
                name = 'maxConsecutiveDays({},{})'.format(e,d),
                constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                                 if s in ShiftTypesWorking
                                                 for dd in range(d,d + Nmax + 1)])
                           <= Nmax
                )

    # Maximum consecutive days working shift group
    maxConsecutiveDaysGroup = dict.fromkeys((e,d,g) for g in ShiftGroups
                                                    for e in Employees
                                                    for d in Days
                                                    if d <= nDays - NmaxGroup[g])
    for g in ShiftGroups:
        for e in Employees:
            for d in Days:
                if d <= nDays - NmaxGroup[g]:
                    maxConsecutiveDaysGroup[(e,d,g)] = xp.constraint(
                    name = 'maxConsecutiveDaysGroup({},{},{})'.format(e,d,g),
                    constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                                     if s in ShiftTypesGroup[g]
                                                     for dd in range(d,d + NmaxGroup[g] + 1)])
                    <= NmaxGroup[g]
                    )

    # Minimum consecutive days working
    minConsecutiveDays = dict.fromkeys((e,d) for e in Employees
                                             for d in [0] + Days
                                             if d <= nDays - Nmin[e])
    for e in Employees:
        for d in Days:
            if d <= nDays - Nmin[e]:
                minConsecutiveDays[(e,d)] = xp.constraint(
                name = 'minConsecutiveDays({},{})'.format(e,d),
                constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                                 if s in ShiftTypesWorking
                                                 for dd in range(d + 1, d + Nmin[e] + 1)])
                           >= Nmin[e] * xp.Sum([x[(e,d,s)] - x[(e,d+1,s)]
                                            for s in ShiftTypesOff])
                )
        # Add constraint for day 0
        minConsecutiveDays[(e,0)] = xp.constraint(
        name = 'minConsecutiveDays({},{})'.format(e,0),
        constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                         if s in ShiftTypesWorking
                                         for dd in range(1, Nmin[e] + 1)])
                   >= Nmin[e] * xp.Sum([1 - x[(e,1,s)]
                                    for s in ShiftTypesOff])
        )

    # Minimum consecutive days working shift group
    minConsecutiveDaysGroup = dict.fromkeys((e,d,g) for g in ShiftGroups
                                                    for e in Employees
                                                    for d in [0] + Days
                                                    if d <= nDays - NminGroup[(e,g)])
    for g in ShiftGroups:
        for e in Employees:
            for d in Days:
                if d <= nDays - NminGroup[(e,g)]:
                    minConsecutiveDaysGroup[(e,d,g)] = xp.constraint(
                    name = 'minConsecutiveDaysGroup({},{},{})'.format(e,d,g),
                    constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                                     if s in ShiftTypesGroup[g]
                                                     for dd in range(d + 1, d + NminGroup[(e,g)] + 1)])
                               >= NminGroup[(e,g)] * xp.Sum([x[(e,d+1,s)] - x[(e,d,s)]
                                                            for s in EmployeeShiftTypes[e]
                                                            if s in ShiftTypesGroup[g]])
                    )
            # Add constraint for day 0
            minConsecutiveDaysGroup[(e,0,g)] = xp.constraint(
            name = 'minConsecutiveDaysGroup({},{},{})'.format(e,0,g),
            constraint = xp.Sum([x[(e,dd,s)] for s in EmployeeShiftTypes
                                             if s in ShiftTypesGroup[g]
                                             for dd in range(1, NminGroup[(e,g)] + 1)])
                       >= NminGroup[(e,g)] * xp.Sum([x[(e,1,s)] - 1
                                                    for s in EmployeeShiftTypes[e]
                                                    if s in ShiftTypesGroup[g]])
            )

    # Required rest
    requiredRest = dict.fromkeys((e,d,s1,s2) for e in Employees
                                             for d in Days[1:]
                                             for s1 in EmployeeShiftTypes[e]
                                             if s1 in FollowingShiftsIllegal
                                             for s2 in FollowingShiftsIllegal[s1]
                                             if s2 in EmployeeShiftTypes[e])
    for e in Employees:
        for d in Days[1:]:
            for s1 in EmployeeShiftTypes[e]:
                # Slight equivalent deviation from mathematical model
                if s1 in FollowingShiftsIllegal:
                    for s2 in FollowingShiftsIllegal[s1]:
                        if s2 in EmployeeShiftTypes[e]:
                            requiredRest[(e,d,s1,s2)] = xp.constraint(
                            name = 'requiredRest({},{},{},{})'.format(e,d,s1,s2),
                            constraint = x[(e,d-1,s1)] + x[(e,d,s2)] <= 1
                            )

    # Reduced rest
    reducedRest = dict.fromkeys((e,d,s1,s2) for e in Employees
                                             for d in Days[1:]
                                             for s1 in EmployeeShiftTypes[e]
                                             if s1 in FollowingShiftsPenalty
                                             for s2 in FollowingShiftsPenalty[s1]
                                             if s2 in EmployeeShiftTypes[e])
    for e in Employees:
        for d in Days[1:]:
            for s1 in EmployeeShiftTypes[e]:
                # Slight equivalent deviation from mathematical model
                if s1 in FollowingShiftsPenalty:
                    for s2 in FollowingShiftsPenalty[s1]:
                        if s2 in EmployeeShiftTypes[e]:
                            reducedRest[(e,d,s1,s2)] = xp.constraint(
                            name = 'reducedRest({},{},{},{})'.format(e,d,s1,s2),
                            constraint = x[(e,d-1,s1)] + x[(e,d,s2)]
                                       <= 1 + v[(e,d)]
                            )

    # Maxiumum number of days with rest penalty
    maxDaysWithRestPenalty = dict.fromkeys((e,d) for e in Employees
                                                 for d in Days if d <= nDays - D_R + 1)
    for e in Employees:
        for d in Days:
            if d <= nDays - D_R + 1:
                maxDaysWithRestPenalty[(e,d)] = xp.constraint(
                name = 'maxDaysWithRestPenalty({},{})'.format(e,d),
                constraint = xp.Sum([v[(e,dd)] for dd in range(d, d + D_R)])
                <= Nmax_R
                )

    # Weekends
    # Both or no days in weekend
    bothOrNoWeekendDays = dict.fromkeys((e,d) for e in Employees
                                              for d in DaysOnWeekday['SAT'] if d <= nDays - 1)
    for e in Employees:
        for d in DaysOnWeekday['SAT']:
            if d <= nDays - 1:
                bothOrNoWeekendDays[(e,d)] = xp.constraint(
                name = 'bothOrNoWeekendDays({},{})'.format(e,d),
                constraint = xp.Sum([x[(e,d,s)] - x[(e,d+1,s)] for s in ShiftTypesOff])
                == 0
                )

    # No late Friday shift before weekend off
    noLateIntoWeekend = dict.fromkeys((e,d) for e in Employees
                                              for d in DaysOnWeekday['SAT'] if d <= nDays - 1)
    for e in Employees:
        for d in DaysOnWeekday['SAT']:
            if d >= 2:
                noLateIntoWeekend[(e,d)] = xp.constraint(
                name = 'noLateIntoWeekend({},{})'.format(e,d),
                constraint = xp.Sum([x[(e,d-1,s)] for s in EmployeeShiftTypes[e]
                                                  if s in ShiftTypesWorking
                                                  if T_E[s] > H])
                           + xp.Sum([x[(e,d,s)] for s in ShiftTypesOff])
                <= 1
                )

    # Min weekends off
    minWeekendsOff = dict.fromkeys((e,w) for e in Employees
                                         for w in Weeks if w <= nWeeks - W_W + 1)
    for e in Employees:
        for w in Weeks:
            if w <= nWeeks - W_W + 1:
                minWeekendsOff[(e,w)] = xp.constraint(
                name = 'minWeekendsOff({},{})'.format(e,w),
                constraint = xp.Sum([x[(e,d,s)] for ww in range(w, w + W_W)
                                                for s in ShiftTypesOff
                                                for d in DaysOnWeekdayInWeek[(ww,'SAT')]])
                >= Nmin_W
                )

    # Strict days off
    # Day off
    strictDaysOff_dayOff = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            strictDaysOff_dayOff[(e,d)] = xp.constraint(
            name = 'strictDaysOff_dayOff({},{})'.format(e,d),
            constraint = strict[(e,d)] - xp.Sum([x[(e,d,s)] for s in ShiftTypesOff])
            <= 0
            )
    # One strict day off
    strictDaysOff_one = dict.fromkeys((e,d,s1,s2) for e in Employees for d in Days[1:nDays-1]
                                                  for s1 in ShiftTypesWorking
                                                  if (s1 in EmployeeShiftTypes[e] and s1 in StrictDayOff1.keys())
                                                  for s2 in StrictDayOff1[s1])
    for e in Employees:
        for d in Days[1:nDays-1]:
            for s1 in ShiftTypesWorking:
                if (s1 in EmployeeShiftTypes[e] and s1 in StrictDayOff1.keys()):
                    for s2 in StrictDayOff1[s1]:
                        strictDaysOff_one[(e,d,s1,s2)] = xp.constraint(
                        name = 'strictDaysOff_one({},{},{},{})'.format(e,d,s1,s2),
                        constraint = x[(e,d-1,s1)] + x[(e,d+1,s2)] + strict[(e,d)]
                        <= 2
                        )
    # Two strict days off
    strictDaysOff_two = dict.fromkeys((e,d,s1,s2) for e in Employees for d in Days[1:nDays-2]
                                                  for s1 in ShiftTypesWorking
                                                  if (s1 in EmployeeShiftTypes[e] and s1 in StrictDayOff2.keys())
                                                  for s2 in StrictDayOff2[s1])
    for e in Employees:
        for d in Days[1:nDays-2]:
            for s1 in ShiftTypesWorking:
                if (s1 in EmployeeShiftTypes[e] and s1 in StrictDayOff2.keys()):
                    for s2 in StrictDayOff2[s1]:
                        strictDaysOff_two[(e,d,s1,s2)] = xp.constraint(
                        name = 'strictDaysOff_two({},{},{},{})'.format(e,d,s1,s2),
                        constraint = x[(e,d-1,s1)] + x[(e,d+2,s2)] + strict[(e,d)] + strict[(e,d+1)]
                        <= 3
                        )
    # Min number of strict days off
    minStrictDaysOff = dict.fromkeys((e,d) for e in Employees
                                           for d in Days if d <= nDays - D_S + 1)
    for e in Employees:
        for d in Days:
            if d <= nDays - D_S + 1:
                minStrictDaysOff[(e,d)] = xp.constraint(
                name = 'minStrictDaysOff({},{})'.format(e,d),
                constraint = xp.Sum([strict[(e,dd)] for dd in range(d,d+D_S)])
                >= Nmin_S
                )

    # Workload
    workload = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
    for e in Employees:
        for d in NormPeriodStartDays:
            workload[(e,d)] = xp.constraint(
            name = 'workload({},{})'.format(e,d),
            constraint = xp.Sum([T[s] * x[(e,dd,s)] for dd in range(d, d + N_N)
                                                    for s in ShiftTypesWorking
                                                    if s in EmployeeShiftTypes[e]])
            - u_plus[(e,d)] + u_minus[(e,d)]
            == W_N*H_W[e]
            )

    # Patterns
    # Illegal patterns
    illegalPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsIllegal.keys()
                                              for pat in PatternsIllegal[e]
                                              for d in PatternDays[(e,pat)])
    for e in Employees:
        if e in PatternsIllegal.keys():
            for pat in PatternsIllegal[e]:
                for d in PatternDays[(e,pat)]:
                    illegalPatterns[(e,pat,d)] = xp.constraint(
                    name = 'illegalPatterns({},{},{})'.format(e,pat,d),
                    constraint = xp.Sum([M[(e,pat,dd,g)] * x[(e,d+dd-1,s)]
                                    for dd in range(1,PatternDuration[(e,pat)]+1)
                                    for g in ShiftGroups
                                    for s in ShiftTypesGroup[g] if s in EmployeeShiftTypes[e]])
                    <= PatternDuration[(e,pat)] - 1
                    )
    # Penalized patterns
    penalizedPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsPenalized.keys()
                                                for pat in PatternsPenalized[e]
                                                for d in PatternDays[(e,pat)])
    for e in Employees:
        if e in PatternsPenalized.keys():
            for pat in PatternsPenalized[e]:
                for d in PatternDays[(e,pat)]:
                    penalizedPatterns[(e,pat,d)] = xp.constraint(
                    name = 'penalizedPatterns({},{},{})'.format(e,pat,d),
                    constraint = xp.Sum([M[(e,pat,dd,g)] * x[(e,d+dd-1,s)]
                                    for dd in range(1,PatternDuration[(e,pat)]+1)
                                    for g in ShiftGroups
                                    for s in ShiftTypesGroup[g] if s in EmployeeShiftTypes[e]])
                    <= PatternDuration[(e,pat)] + m[(e,pat,d)] - 1
                    )
    # Rewarded patterns
    rewardedPatterns = dict.fromkeys((e,pat,d,dd) for e in Employees if e in PatternsRewarded.keys()
                                               for pat in PatternsRewarded[e]
                                               for d in PatternDays[(e,pat)]
                                               for dd in range(1,PatternDuration[(e,pat)]+1))
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                for d in PatternDays[(e,pat)]:
                    for dd in range(1,PatternDuration[(e,pat)]+1):
                        rewardedPatterns[(e,pat,d,dd)] = xp.constraint(
                        name = 'rewardedPatterns({},{},{},{})'.format(e,pat,d,dd),
                        constraint = xp.Sum([M[(e,pat,dd,g)] * x[(e,d+dd-1,s)]
                                        for g in ShiftGroups
                                        for s in ShiftTypesGroup[g]
                                        if s in EmployeeShiftTypes[e]])
                        >= m[(e,pat,d)]
                        )
    # Overlapping patterns
    overlappingPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsRewarded.keys()
                                                  for pat in PatternsRewarded[e]
                                                  for d in PatternDays[(e,pat)] if d <= nDays - 2*PatternDuration[(e,pat)] + 3)
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                for d in PatternDays[(e,pat)]:
                    if d <= nDays - 2*PatternDuration[(e,pat)] + 3:
                        overlappingPatterns[(e,pat,d)] = xp.constraint(
                        name = 'overlappingPatterns({},{},{})'.format(e,pat,d),
                        constraint = xp.Sum([m[(e,pat,dd)] for dd in range(d,d+PatternDuration[(e,pat)]-1)
                                                           if dd in PatternDays[(e,pat)]])
                        <= 1
                        )

    p.addConstraint(demandCoverage,
                    oneShift,
                    maxConsecutiveDays,
                    maxConsecutiveDaysGroup,
                    minConsecutiveDays,
                    minConsecutiveDaysGroup,
                    requiredRest,
                    reducedRest,
                    maxDaysWithRestPenalty,
                    bothOrNoWeekendDays,
                    noLateIntoWeekend,
                    minWeekendsOff,
                    strictDaysOff_dayOff,
                    strictDaysOff_one,
                    strictDaysOff_two,
                    minStrictDaysOff,
                    workload,
                    illegalPatterns,
                    penalizedPatterns,
                    rewardedPatterns,
                    overlappingPatterns
                    )

    '''Attempt to solve problem and evaluate feasibility. If feasible, store
    solutions, and objective, if feasible'''
    # Attempt to solve
    p.solve()
    # Assess problem status
    mipstatus = p.getAttrib('mipstatus')
    # Check if problem status indicates infeasibility
    if mipstatus == 4:
        feasible = 'True'
    elif mipstatus == 5:
        feasible = 'False'
    elif mipstatus == 6:
        feasible = 'True'
    else:
        feasible = 'Unknown'

    # Check if problem status indicates MIP was completed
    if mipstatus in [5, 6] and gapLimit == None:
        completed = True
    else:
        completed = False

    '''Solutions'''
    # If feasible, return solution
    if feasible == 'True':
        # Get objective value
        objective = p.getObjVal()

        # Get shift types
        solution = {}
        solution['x'] = dict.fromkeys((e,d,s) for e in Employees for d in Days for s in ShiftTypes)
        for e in Employees:
            for d in Days:
                for s in ShiftTypes:
                    solution['x'][(e,d,s)] = p.getSolution(x[(e,d,s)])
        # Set lower bound
        if completed:
            lowerBound = objective
        else:
            lowerBound = p.getAttrib('bestbound')
    # If feasibility unknown, return lower bound
    elif feasible == 'Unknown':
        objective = None
        solution = None
        lowerBound = p.getAttrib('bestbound')
    # If infeasible, return None
    else:
        objective = None
        solution = None
        lowerBound = None

    # Calculate time spent
    computationTime = time.time() - start

    # Save solution to pickle if specified
    if outputPickle != None:
        with open(outputPickle, 'wb') as f:
            pickle.dump({'completed': completed, 'feasible': feasible,
                         'objective': objective, 'lower bound': lowerBound,
                         'solution': solution,
                         'computationTime': computationTime,
                         'input parameters': {'coverConstraint': coverConstraint,
                                              'timeLimit': timeLimit,
                                              'gapLimit': gapLimit}}, f)

    return completed, feasible, objective, lowerBound, solution, computationTime
