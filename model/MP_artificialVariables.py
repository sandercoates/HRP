import xpress as xp

def defineMP_artificialVariables(data, initialColumns, LP=True, outputPrint=False,
            problemName='RMP_artificialVariables', coverConstraint = '='):
    '''Define the problem with artificial variables specified by data and
    load initial columns.'''

    '''Unpack data'''
    for key in data:
        globals()[key] = data[key]

    '''Unpack column data'''
    rosterlines, CK, A, A_W, A_O, A_g, V, D = initialColumns.unpackColumns(data = data)

    '''Setup'''
    p = xp.problem(name = problemName)
    p.controls.outputlog = outputPrint

    '''Variables'''
    if LP:
        vartype = 'continuous'
    else:
        vartype = 'binary'

    # Note: This implementation is approx. 25% slower than when using
    # lists, but is easier to use lambda-variables
    l = dict.fromkeys((e,k) for e in Employees for k in rosterlines[e])
    for e in Employees:
        for k in rosterlines[e]:
            l[(e,k)] = xp.var(vartype = xp.__dict__[vartype],
                        name = 'lambda({},{})'.format(e,k))
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
    # s-variables
    strict = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            strict[(e,d)] = xp.var(vartype = xp.__dict__[vartype],
                name = 's({},{})'.format(e,d))
    # over- and undertime
    u_plus = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
    u_minus = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
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
                         if PatternDuration[(e,pat)] > 2
                         for d in PatternDays[(e,pat)]]
    keyVec2 = [(e,pat,d) for e in Employees if e in PatternsPenalized.keys()
                         for pat in PatternsPenalized[e]
                         if PatternDuration[(e,pat)] > 2
                         for d in PatternDays[(e,pat)]]
    keyVec = keyVec1 + keyVec2
    m = dict.fromkeys(keyVec)
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        m[(e,pat,d)] = xp.var(vartype = xp.__dict__[vartype],
                            name = 'm({},{},{})'.format(e,pat,d))
        if e in PatternsPenalized.keys():
            for pat in PatternsPenalized[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        m[(e,pat,d)] = xp.var(vartype = xp.__dict__[vartype],
                            name = 'm({},{},{})'.format(e,pat,d))

    '''Artificial variables''' # One for each constraint
    # Demand coverage
    demandCoverage_variables_plus = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    demandCoverage_variables_minus = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    for d in Days:
        for s in ShiftTypesWorking:
            demandCoverage_variables_plus[(d,s)] = xp.var(vartype = xp.continuous,
                            name = 'demandCoverage_variables_plus({},{})'.format(d,s))
            demandCoverage_variables_minus[(d,s)] = xp.var(vartype = xp.continuous,
                            name = 'demandCoverage_variables_minus({},{})'.format(d,s))

    # Maximum consecutive days working
    maxConsecutiveDays_variables = dict.fromkeys((e,d) for e in Employees
                                             for d in Days if d <= nDays - Nmax)
    for e in Employees:
        for d in Days:
            if d <= nDays - Nmax:
                maxConsecutiveDays_variables[(e,d)] = xp.var(vartype = xp.continuous,
                            name = 'maxConsecutiveDays_variables({},{})'.format(e,d))

    # Maximum consecutive days working shift group
    maxConsecutiveDaysGroup_variables = dict.fromkeys((e,d,g) for g in ShiftGroups
                                                    for e in Employees
                                                    for d in Days if d <= nDays - NmaxGroup[g])
    for g in ShiftGroups:
        for e in Employees:
            for d in Days:
                if d <= nDays - NmaxGroup[g]:
                    maxConsecutiveDaysGroup_variables[(e,d,g)] = xp.var(vartype = xp.continuous,
                                name = 'maxConsecutiveDaysGroup_variables({},{},{})'.format(e,d,g))

    # Maxiumum number of days with rest penalty
    maxDaysWithRestPenalty_variables = dict.fromkeys((e,d) for e in Employees
                                                 for d in Days if d <= nDays - D_R + 1)
    for e in Employees:
        for d in Days:
            if d <= nDays - D_R + 1:
                maxDaysWithRestPenalty_variables[(e,d)] = xp.var(vartype = xp.continuous,
                            name = 'maxDaysWithRestPenalty_variables({},{})'.format(e,d))

    # Min number of strict days off
    minStrictDaysOff_variables = dict.fromkeys((e,d) for e in Employees
                                           for d in Days if d <= nDays - D_S + 1)
    for e in Employees:
        for d in Days:
            if d <= nDays - D_S + 1:
                minStrictDaysOff_variables[(e,d)] = xp.var(vartype = xp.continuous,
                            name = 'minStrictDaysOff_variables({},{})'.format(e,d))

    # Workload
    workload_variables_plus = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
    workload_variables_minus = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
    for e in Employees:
        for d in NormPeriodStartDays:
            workload_variables_plus[(e,d)] = xp.var(vartype = xp.continuous,
                        name = 'workload_variables_plus({},{})'.format(e,d))
            workload_variables_minus[(e,d)] = xp.var(vartype = xp.continuous,
                        name = 'workload_variables_minus({},{})'.format(e,d))

    # Illegal patterns
    illegalPatterns_variables = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsIllegal.keys()
                                              for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2
                                              for d in PatternDays[(e,pat)])
    for e in Employees:
        if e in PatternsIllegal.keys():
            for pat in PatternsIllegal[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        illegalPatterns_variables[(e,pat,d)] = xp.var(vartype = xp.continuous,
                                    name = 'illegalPatterns_variables({},{},{})'.format(e,pat,d))

    p.addVariable(l,
                  wPlus,
                  wMinus,
                  strict,
                  u_plus,
                  u_minus,
                  m,
                  demandCoverage_variables_plus,
                  demandCoverage_variables_minus,
                  maxConsecutiveDays_variables,
                  maxConsecutiveDaysGroup_variables,
                  maxDaysWithRestPenalty_variables,
                  minStrictDaysOff_variables,
                  workload_variables_plus,
                  workload_variables_minus,
                  illegalPatterns_variables)

    '''Objective function''' # Sum of artificial variables
    p.setObjective(xp.Sum([demandCoverage_variables_plus[(d,s)] for d in Days
                                                                for s in ShiftTypesWorking])
                   + xp.Sum([demandCoverage_variables_minus[(d,s)] for d in Days
                                                                   for s in ShiftTypesWorking])
                   + xp.Sum([maxConsecutiveDays_variables[(e,d)] for e in Employees
                                                                 for d in Days
                                                                 if d <= nDays - Nmax])
                   + xp.Sum([maxConsecutiveDaysGroup_variables[(e,d,g)] for g in ShiftGroups
                                                                      for e in Employees
                                                                      for d in Days
                                                                      if d <= nDays - NmaxGroup[g]])
                   + xp.Sum([maxDaysWithRestPenalty_variables[(e,d)] for e in Employees
                                                                 for d in Days
                                                                 if d <= nDays - D_R + 1])
                   + xp.Sum([minStrictDaysOff_variables[(e,d)] for e in Employees
                                                               for d in Days
                                                               if d <= nDays - D_S + 1])
                   + xp.Sum([workload_variables_plus[(e,d)] for e in Employees
                                                            for d in NormPeriodStartDays])
                   + xp.Sum([workload_variables_minus[(e,d)] for e in Employees
                                                            for d in NormPeriodStartDays])
                   + xp.Sum([illegalPatterns_variables[(e,pat,d)] for e in Employees
                                                                  if e in PatternsIllegal.keys()
                                                                  for pat in PatternsIllegal[e]
                                                                  if PatternDuration[(e,pat)] > 2
                                                                  for d in PatternDays[(e,pat)]])
                    , sense = xp.minimize)

    '''Constraints'''
    # Demand coverage
    demandCoverage = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
    for d in Days:
        for s in ShiftTypesWorking:
            if coverConstraint == '>=':
                demandCoverage[(d,s)] = xp.constraint(
                name = 'demandCoverage({},{})'.format(d,s),
                constraint = xp.Sum([A[(e,k,d,s)]*l[(e,k)] for e in Employees
                                                           for k in rosterlines[e]])
                                + wMinus[(d,s)] - wPlus[(d,s)]
                                >= Demand[(d,s)] + demandCoverage_variables_plus[(d,s)]
                                                 - demandCoverage_variables_minus[(d,s)]
                )
            else:
                demandCoverage[(d,s)] = xp.constraint(
                name = 'demandCoverage({},{})'.format(d,s),
                constraint = xp.Sum([A[(e,k,d,s)]*l[(e,k)] for e in Employees
                                                           for k in rosterlines[e]])
                                + wMinus[(d,s)] - wPlus[(d,s)]
                                == Demand[(d,s)] + demandCoverage_variables_plus[(d,s)]
                                                 - demandCoverage_variables_minus[(d,s)]
                )

    # Convexity
    convexity = dict.fromkeys(e for e in Employees)
    for e in Employees:
        convexity[e] = xp.constraint(
        name = 'convexity({})'.format(e),
        constraint = xp.Sum([l[(e,k)] for k in rosterlines[e]])
                        == 1
        )

    # Maximum consecutive days working
    maxConsecutiveDays = dict.fromkeys((e,d) for e in Employees
                                             for d in Days if d <= nDays - Nmax)
    for e in Employees:
        for d in Days:
            if d <= nDays - Nmax:
                maxConsecutiveDays[(e,d)] = xp.constraint(
                name = 'maxConsecutiveDays({},{})'.format(e,d),
                constraint = xp.Sum([A_W[(e,k,dd)] * l[(e,k)]
                            for k in rosterlines[e] for dd in range(d,d + Nmax + 1)])
                <= Nmax + maxConsecutiveDays_variables[(e,d)]
                )

    # Maximum consecutive days working shift group
    maxConsecutiveDaysGroup = dict.fromkeys((e,d,g) for g in ShiftGroups
                                                    for e in Employees
                                                    for d in Days if d <= nDays - NmaxGroup[g])
    for g in ShiftGroups:
        for e in Employees:
            for d in Days:
                if d <= nDays - NmaxGroup[g]:
                    maxConsecutiveDaysGroup[(e,d,g)] = xp.constraint(
                    name = 'maxConsecutiveDaysGroup({},{},{})'.format(e,d,g),
                    constraint = xp.Sum([A_g[(e,k,dd,g)] * l[(e,k)]
                                for k in rosterlines[e] for dd in range(d,d + NmaxGroup[g] + 1)])
                    <= NmaxGroup[g] + maxConsecutiveDaysGroup_variables[(e,d,g)]
                    )

    # Maxiumum number of days with rest penalty
    maxDaysWithRestPenalty = dict.fromkeys((e,d) for e in Employees
                                                 for d in Days if d <= nDays - D_R + 1)
    for e in Employees:
        for d in Days:
            if d <= nDays - D_R + 1:
                maxDaysWithRestPenalty[(e,d)] = xp.constraint(
                name = 'maxDaysWithRestPenalty({},{})'.format(e,d),
                constraint = xp.Sum([V[(e,k,dd)] * l[(e,k)]
                            for k in rosterlines[e] for dd in range(d, d + D_R)])
                <= Nmax_R + maxDaysWithRestPenalty_variables[(e,d)]
                )

    # Strict days off
    # Day off
    strictDaysOff_dayOff = dict.fromkeys((e,d) for e in Employees for d in Days)
    for e in Employees:
        for d in Days:
            strictDaysOff_dayOff[(e,d)] = xp.constraint(
            name = 'strictDaysOff_dayOff({},{})'.format(e,d),
            constraint = strict[(e,d)] - xp.Sum([A_O[(e,k,d)] * l[(e,k)]
                                        for k in rosterlines[e]])
            <= 0
            )
    # One strict day off
    strictDaysOff_one = dict.fromkeys((e,d,s1,s2) for e in Employees for d in Days[1:nDays-1]
                                                  for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys()
                                                  for s2 in StrictDayOff1[s1])
    for e in Employees:
        for d in Days[1:nDays-1]:
            for s1 in ShiftTypesWorking:
                if s1 in StrictDayOff1.keys():
                    for s2 in StrictDayOff1[s1]:
                        strictDaysOff_one[(e,d,s1,s2)] = xp.constraint(
                        name = 'strictDaysOff_one({},{},{},{})'.format(e,d,s1,s2),
                        constraint = xp.Sum([(A[(e,k,d-1,s1)] + A[(e,k,d+1,s2)]) * l[(e,k)]
                                        for k in rosterlines[e]])
                        + strict[(e,d)]
                        <= 2
                        )
    # Two strict days off
    strictDaysOff_two = dict.fromkeys((e,d,s1,s2) for e in Employees for d in Days[1:nDays-2]
                                                  for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys()
                                                  for s2 in StrictDayOff2[s1])
    for e in Employees:
        for d in Days[1:nDays-2]:
            for s1 in ShiftTypesWorking:
                if s1 in StrictDayOff2.keys():
                    for s2 in StrictDayOff2[s1]:
                        strictDaysOff_two[(e,d,s1,s2)] = xp.constraint(
                        name = 'strictDaysOff_two({},{},{},{})'.format(e,d,s1,s2),
                        constraint = xp.Sum([(A[(e,k,d-1,s1)] + A[(e,k,d+2,s2)]) * l[(e,k)]
                                        for k in rosterlines[e]])
                        + strict[(e,d)] + strict[(e,d+1)]
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
                >= Nmin_S - minStrictDaysOff_variables[(e,d)]
                )

    # Workload
    workload = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
    for e in Employees:
        for d in NormPeriodStartDays:
            workload[(e,d)] = xp.constraint(
            name = 'workload({},{})'.format(e,d),
            constraint = xp.Sum([D[(e,k,d)] * l[(e,k)] for k in rosterlines[e]])
            - u_plus[(e,d)] + u_minus[(e,d)]
            == W_N*H_W[e] + workload_variables_plus[(e,d)] - workload_variables_minus[(e,d)]
            )

    # Patterns
    # Illegal patterns
    illegalPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsIllegal.keys()
                                              for pat in PatternsIllegal[e]
                                              if PatternDuration[(e,pat)] > 2
                                              for d in PatternDays[(e,pat)])
    for e in Employees:
        if e in PatternsIllegal.keys():
            for pat in PatternsIllegal[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        illegalPatterns[(e,pat,d)] = xp.constraint(
                        name = 'illegalPatterns({},{},{})'.format(e,pat,d),
                        constraint = xp.Sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] * l[(e,k)]
                                        for k in rosterlines[e]
                                        for dd in range(1,PatternDuration[(e,pat)]+1)
                                        for g in ShiftGroups])
                        <= PatternDuration[(e,pat)] - 1 + illegalPatterns_variables[(e,pat,d)]
                        )
    # Penalized patterns
    penalizedPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsPenalized.keys()
                                                for pat in PatternsPenalized[e]
                                                if PatternDuration[(e,pat)] > 2
                                                for d in PatternDays[(e,pat)])
    for e in Employees:
        if e in PatternsPenalized.keys():
            for pat in PatternsPenalized[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        penalizedPatterns[(e,pat,d)] = xp.constraint(
                        name = 'penalizedPatterns({},{},{})'.format(e,pat,d),
                        constraint = xp.Sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] * l[(e,k)]
                                        for k in rosterlines[e]
                                        for dd in range(1,PatternDuration[(e,pat)]+1)
                                        for g in ShiftGroups])
                        <= PatternDuration[(e,pat)] + m[(e,pat,d)] - 1
                        )
    # Rewarded patterns
    rewardedPatterns = dict.fromkeys((e,pat,d,dd) for e in Employees if e in PatternsRewarded.keys()
                                               for pat in PatternsRewarded[e]
                                               if PatternDuration[(e,pat)] > 2
                                               for d in PatternDays[(e,pat)]
                                               for dd in range(1,PatternDuration[(e,pat)]+1))
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        for dd in range(1,PatternDuration[(e,pat)]+1):
                            rewardedPatterns[(e,pat,d,dd)] = xp.constraint(
                            name = 'rewardedPatterns({},{},{},{})'.format(e,pat,d,dd),
                            constraint = xp.Sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] * l[(e,k)]
                                            for k in rosterlines[e]
                                            for g in ShiftGroups])
                            >= m[(e,pat,d)]
                            )
    # Overlapping patterns
    overlappingPatterns = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsRewarded.keys()
                                                  for pat in PatternsRewarded[e]
                                                  if PatternDuration[(e,pat)] > 2
                                                  for d in PatternDays[(e,pat)] if d <= nDays - 2*PatternDuration[(e,pat)] + 3)
    for e in Employees:
        if e in PatternsRewarded.keys():
            for pat in PatternsRewarded[e]:
                if PatternDuration[(e,pat)] > 2:
                    for d in PatternDays[(e,pat)]:
                        if d <= nDays - 2*PatternDuration[(e,pat)] + 3:
                            overlappingPatterns[(e,pat,d)] = xp.constraint(
                            name = 'overlappingPatterns({},{},{})'.format(e,pat,d),
                            constraint = xp.Sum([m[(e,pat,dd)] for dd in range(d,d+PatternDuration[(e,pat)]-1)
                                                               if dd in PatternDays[(e,pat)]])
                            <= 1
                            )

    p.addConstraint(demandCoverage,
                    convexity,
                    maxConsecutiveDays,
                    maxConsecutiveDaysGroup,
                    maxDaysWithRestPenalty,
                    strictDaysOff_dayOff,
                    strictDaysOff_one,
                    strictDaysOff_two,
                    minStrictDaysOff,
                    workload,
                    illegalPatterns,
                    penalizedPatterns,
                    rewardedPatterns,
                    overlappingPatterns)

    return p

def solveMP_artificialVariables(masterProblem_artVars, data, columns, outputPrint=False):
    '''Solve the master problem with artificial variables. The problem is input.'''

    p = masterProblem_artVars

    '''Unpack data'''
    for key in data:
        globals()[key] = data[key]

    '''Unpack column data'''
    rosterlines, CK, A, A_W, A_O, A_g, V, D = columns.unpackColumns(data = data)


    '''Check feasibility'''
    feasible = bool(p.iisfirst(0))

    '''Solve and store solutions, duals and objective, if feasible'''
    if feasible:
        # Solve
        p.solve()

        # Get objective value
        objective = p.getObjVal()

        # Get weighting variable (lambda) solution
        temp = p.getSolution('lambda({},{})'.format(e,k) for e in Employees for k in rosterlines[e])
        solution = dict.fromkeys((e,k)  for e in Employees for k in rosterlines[e])
        count = 0
        for e in Employees:
            for k in rosterlines[e]:
                solution[(e,k)] = temp[count]
                count += 1

        # Get dual variables (Assumed LP)
        # Note: This implementation is faster than only using dictionaries and calling getDuals() many times
        duals = {} #Dictionary to store duals

        #Demand coverage
        temp = p.getDual('demandCoverage({},{})'.format(d,s) for d in Days for s in ShiftTypesWorking)
        pi = dict.fromkeys((d,s) for d in Days for s in ShiftTypesWorking)
        count = 0
        for d in Days:
            for s in ShiftTypesWorking:
                pi[(d,s)] = temp[count]
                count += 1
        duals['pi'] = pi

        #Convexity
        temp = p.getDual('convexity({})'.format(e) for e in Employees)
        omega = dict.fromkeys(e for e in Employees)
        for e in Employees:
            omega[e] = temp[e-1]
        duals['omega'] = omega

        #Maximum consecutive days working
        temp = p.getDual('maxConsecutiveDays({},{})'.format(e,d) for e in Employees for d in Days if d <= nDays - Nmax)
        alpha_W = dict.fromkeys((e,d) for e in Employees for d in Days if d <= nDays - Nmax)
        count = 0
        for e in Employees:
            for d in Days:
                if d <= nDays - Nmax:
                    alpha_W[(e,d)] = temp[count]
                    count += 1
        duals['alpha_W'] = alpha_W

        #Maximum consecutive days working shift group
        temp = p.getDual('maxConsecutiveDaysGroup({},{},{})'.format(e,d,g) for g in ShiftGroups for e in Employees for d in Days if d <= nDays - NmaxGroup[g])
        alpha = dict.fromkeys((e,d,g) for g in ShiftGroups for e in Employees for d in Days if d <= nDays - NmaxGroup[g])
        count = 0
        for g in ShiftGroups:
            for e in Employees:
                for d in Days:
                    if d <= nDays - NmaxGroup[g]:
                        alpha[(e,d,g)] = temp[count]
                        count += 1
        duals['alpha'] = alpha

        #Maxiumum number of days with rest penalty
        temp = p.getDual('maxDaysWithRestPenalty({},{})'.format(e,d) for e in Employees for d in Days if d <= nDays - D_R + 1)
        gamma = dict.fromkeys((e,d) for e in Employees for d in Days if d <= nDays - D_R + 1)
        count = 0
        for e in Employees:
            for d in Days:
                if d <= nDays - D_R + 1:
                    gamma[(e,d)] = temp[count]
                    count += 1
        duals['gamma'] = gamma

        #Strict days off
        #Day off
        temp = p.getDual('strictDaysOff_dayOff({},{})'.format(e,d) for e in Employees for d in Days)
        epsilon_0 = dict.fromkeys((e,d) for e in Employees for d in Days)
        count = 0
        for e in Employees:
            for d in Days:
                epsilon_0[(e,d)] = temp[count]
                count += 1
        duals['epsilon_0'] = epsilon_0
        #One strict day off
        temp = p.getDual('strictDaysOff_one({},{},{},{})'.format(e,d,s1,s2) for e in Employees
                                                                            for d in Days[1:nDays-1]
                                                                            for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys()
                                                                            for s2 in StrictDayOff1[s1])
        epsilon_1 = dict.fromkeys((e,d,s1,s2) for e in Employees
                                              for d in Days[1:nDays-1]
                                              for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys()
                                              for s2 in StrictDayOff1[s1])
        count = 0
        for e in Employees:
            for d in Days[1:nDays-1]:
                for s1 in ShiftTypesWorking:
                    if s1 in StrictDayOff1.keys():
                        for s2 in StrictDayOff1[s1]:
                            epsilon_1[(e,d,s1,s2)] = temp[count]
                            count += 1
        duals['epsilon_1'] = epsilon_1
        #Two strict days off
        temp = p.getDual('strictDaysOff_two({},{},{},{})'.format(e,d,s1,s2) for e in Employees
                                                                            for d in Days[1:nDays-2]
                                                                            for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys()
                                                                            for s2 in StrictDayOff2[s1])
        epsilon_2 = dict.fromkeys((e,d,s1,s2) for e in Employees
                                              for d in Days[1:nDays-2]
                                              for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys()
                                              for s2 in StrictDayOff2[s1])
        count = 0
        for e in Employees:
            for d in Days[1:nDays-2]:
                for s1 in ShiftTypesWorking:
                    if s1 in StrictDayOff2.keys():
                        for s2 in StrictDayOff2[s1]:
                            epsilon_2[(e,d,s1,s2)] = temp[count]
                            count += 1
        duals['epsilon_2'] = epsilon_2

        #Workload
        temp = p.getDual('workload({},{})'.format(e,d) for e in Employees for d in NormPeriodStartDays)
        zeta = dict.fromkeys((e,d) for e in Employees for d in NormPeriodStartDays)
        count = 0
        for e in Employees:
            for d in NormPeriodStartDays:
                zeta[(e,d)] = temp[count]
                count += 1
        duals['zeta'] = zeta

        #Patterns
        #Illegal patterns
        temp = p.getDual('illegalPatterns({},{},{})'.format(e,pat,d)    for e in Employees if e in PatternsIllegal.keys()
                                                                        for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2
                                                                        for d in PatternDays[(e,pat)])
        theta_I = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsIllegal.keys()
                                          for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2
                                          for d in PatternDays[(e,pat)])
        count = 0
        for e in Employees:
            if e in PatternsIllegal.keys():
                for pat in PatternsIllegal[e]:
                    if PatternDuration[(e,pat)] > 2:
                        for d in PatternDays[(e,pat)]:
                            theta_I[(e,pat,d)] = temp[count]
                            count += 1
        duals['theta_I'] = theta_I
        #Penalized patterns
        temp = p.getDual('penalizedPatterns({},{},{})'.format(e,pat,d)  for e in Employees if e in PatternsPenalized.keys()
                                                                        for pat in PatternsPenalized[e] if PatternDuration[(e,pat)] > 2
                                                                        for d in PatternDays[(e,pat)])
        theta_P = dict.fromkeys((e,pat,d) for e in Employees if e in PatternsPenalized.keys()
                                          for pat in PatternsPenalized[e] if PatternDuration[(e,pat)] > 2
                                          for d in PatternDays[(e,pat)])
        count = 0
        for e in Employees:
            if e in PatternsPenalized.keys():
                for pat in PatternsPenalized[e]:
                    if PatternDuration[(e,pat)] > 2:
                        for d in PatternDays[(e,pat)]:
                            theta_P[(e,pat,d)] = temp[count]
                            count += 1
        duals['theta_P'] = theta_P
        #Rewarded patterns
        temp = p.getDual('rewardedPatterns({},{},{},{})'.format(e,pat,d,dd) for e in Employees if e in PatternsRewarded.keys()
                                                                            for pat in PatternsRewarded[e] if PatternDuration[(e,pat)] > 2
                                                                            for d in PatternDays[(e,pat)]
                                                                            for dd in range(1,PatternDuration[(e,pat)]+1))
        theta_R = dict.fromkeys((e,pat,d,dd)    for e in Employees if e in PatternsRewarded.keys()
                                                for pat in PatternsRewarded[e] if PatternDuration[(e,pat)] > 2
                                                for d in PatternDays[(e,pat)]
                                                for dd in range(1,PatternDuration[(e,pat)]+1))
        count = 0
        for e in Employees:
            if e in PatternsRewarded.keys():
                for pat in PatternsRewarded[e]:
                    if PatternDuration[(e,pat)] > 2:
                        for d in PatternDays[(e,pat)]:
                            for dd in range(1,PatternDuration[(e,pat)]+1):
                                theta_R[(e,pat,d,dd)] = temp[count]
                                count += 1
        duals['theta_R'] = theta_R

    # If no solution is available, problem is infeasible. Return None.
    else:
        objective = None
        solution = None
        duals = None

    return feasible, objective, solution, duals

def updateMP_artificialVariables(masterProblem_artVars, data, columns, newRosterlineNumbers_artVars, LP = True):
    '''Updates the problem with artificial variables with new columns added through
    the set newRosterlineNumbers_artificialVariables'''

    p = masterProblem_artVars

    '''Unpack data'''
    for key in data:
        globals()[key] = data[key]

    '''Unpack column data'''
    rosterlines, CK, A, A_W, A_O, A_g, V, D = columns.unpackColumns(data = data,
                                                                    newRosterlineNumbers=newRosterlineNumbers_artVars)

    '''Setup'''
    if LP:
        vartype = 'continuous'
    else:
        vartype = 'binary'

    '''Variables'''
    # Add new weighting variables to problem
    l = dict.fromkeys((e,k) for e in Employees for k in rosterlines[e])
    for e in Employees:
        for k in rosterlines[e]:
            l[(e,k)] = xp.var(vartype = xp.__dict__[vartype],
                        name = 'lambda({},{})'.format(e,k))

    p.addVariable(l)

    '''Addd constraints coefficients'''
    # Demand coverage
    p.chgmcoef(['demandCoverage({},{})'.format(d,s) for e in Employees for k in rosterlines[e] for d in Days for s in ShiftTypesWorking if A[(e,k,d,s)] != 0],
                [l[(e,k)]                            for e in Employees for k in rosterlines[e] for d in Days for s in ShiftTypesWorking if A[(e,k,d,s)] != 0],
                [A[(e,k,d,s)]                        for e in Employees for k in rosterlines[e] for d in Days for s in ShiftTypesWorking if A[(e,k,d,s)] != 0]
                )

    # Convexity
    p.chgmcoef(['convexity({})'.format(e) for e in Employees for k in rosterlines[e]],
                [l[(e,k)]                  for e in Employees for k in rosterlines[e]],
                [1                         for e in Employees for k in rosterlines[e]]
                )

    # Maximum consecutive days working
    p.chgmcoef(['maxConsecutiveDays({},{})'.format(e,d)                for e in Employees for d in Days if d <= nDays - Nmax for k in rosterlines[e]],
                [l[(e,k)]                                               for e in Employees for d in Days if d <= nDays - Nmax for k in rosterlines[e]],
                [sum([A_W[(e,k,dd)]  for dd in range(d,d + Nmax + 1)])  for e in Employees for d in Days if d <= nDays - Nmax for k in rosterlines[e]]
                )

    # Maximum consecutive days working shift group
    p.chgmcoef(['maxConsecutiveDaysGroup({},{},{})'.format(e,d,g)              for g in ShiftGroups for e in Employees for d in Days if d <= nDays - NmaxGroup[g] for k in rosterlines[e]],
                [l[(e,k)]                                                       for g in ShiftGroups for e in Employees for d in Days if d <= nDays - NmaxGroup[g] for k in rosterlines[e]],
                [sum([A_g[(e,k,dd,g)] for dd in range(d,d + NmaxGroup[g] + 1)]) for g in ShiftGroups for e in Employees for d in Days if d <= nDays - NmaxGroup[g] for k in rosterlines[e]]
                )

    # Maxiumum number of days with rest penalty
    p.chgmcoef(['maxDaysWithRestPenalty({},{})'.format(e,d)    for e in Employees for d in Days if d <= nDays - D_R + 1 for k in rosterlines[e]],
                [l[(e,k)]                                       for e in Employees for d in Days if d <= nDays - D_R + 1 for k in rosterlines[e]],
                [sum([V[(e,k,dd)] for dd in range(d, d + D_R)]) for e in Employees for d in Days if d <= nDays - D_R + 1 for k in rosterlines[e]]
                )

    # Strict days off
    # Day off
    p.chgmcoef(['strictDaysOff_dayOff({},{})'.format(e,d) for e in Employees for d in Days for k in rosterlines[e] if A_O[(e,k,d)] != 0],
                [l[(e,k)]                                  for e in Employees for d in Days for k in rosterlines[e] if A_O[(e,k,d)] != 0],
                [-A_O[(e,k,d)]                             for e in Employees for d in Days for k in rosterlines[e] if A_O[(e,k,d)] != 0]
                )

    # One strict day off
    p.chgmcoef(['strictDaysOff_one({},{},{},{})'.format(e,d,s1,s2) for e in Employees for d in Days[1:nDays-1] for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys() for s2 in StrictDayOff1[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+1,s2)]) != 0],
                [l[(e,k)]                                           for e in Employees for d in Days[1:nDays-1] for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys() for s2 in StrictDayOff1[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+1,s2)]) != 0],
                [(A[(e,k,d-1,s1)] + A[(e,k,d+1,s2)])                for e in Employees for d in Days[1:nDays-1] for s1 in ShiftTypesWorking if s1 in StrictDayOff1.keys() for s2 in StrictDayOff1[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+1,s2)]) != 0]
                )

    # Two strict days off
    p.chgmcoef(['strictDaysOff_two({},{},{},{})'.format(e,d,s1,s2) for e in Employees for d in Days[1:nDays-2] for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys() for s2 in StrictDayOff2[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+2,s2)]) != 0],
                [l[(e,k)]                                           for e in Employees for d in Days[1:nDays-2] for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys() for s2 in StrictDayOff2[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+2,s2)]) != 0],
                [(A[(e,k,d-1,s1)] + A[(e,k,d+2,s2)])                for e in Employees for d in Days[1:nDays-2] for s1 in ShiftTypesWorking if s1 in StrictDayOff2.keys() for s2 in StrictDayOff2[s1] for k in rosterlines[e] if (A[(e,k,d-1,s1)] + A[(e,k,d+2,s2)]) != 0]
                )

    # Workload
    p.chgmcoef(['workload({},{})'.format(e,d) for e in Employees for d in NormPeriodStartDays for k in rosterlines[e]],
                [l[(e,k)] for e in Employees for d in NormPeriodStartDays for k in rosterlines[e]],
                [D[(e,k,d)] for e in Employees for d in NormPeriodStartDays for k in rosterlines[e]]
                )

    # Patterns
    # Illegal patterns
    p.chgmcoef(['illegalPatterns({},{},{})'.format(e,pat,d)                                                                     for e in Employees if e in PatternsIllegal.keys() for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]],
                [l[(e,k)]                                                                                                        for e in Employees if e in PatternsIllegal.keys() for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]],
                [sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] for dd in range(1,PatternDuration[(e,pat)]+1) for g in ShiftGroups]) for e in Employees if e in PatternsIllegal.keys() for pat in PatternsIllegal[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]]
                )

    # Penalized patterns
    p.chgmcoef(['penalizedPatterns({},{},{})'.format(e,pat,d)                                                                   for e in Employees if e in PatternsPenalized.keys() for pat in PatternsPenalized[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]],
                [l[(e,k)]                                                                                                        for e in Employees if e in PatternsPenalized.keys() for pat in PatternsPenalized[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]],
                [sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] for dd in range(1,PatternDuration[(e,pat)]+1) for g in ShiftGroups]) for e in Employees if e in PatternsPenalized.keys() for pat in PatternsPenalized[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for k in rosterlines[e]]
                )

    # Rewarded patterns
    p.chgmcoef(['rewardedPatterns({},{},{},{})'.format(e,pat,d,dd)                for e in Employees if e in PatternsRewarded.keys() for pat in PatternsRewarded[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for dd in range(1,PatternDuration[(e,pat)]+1) for k in rosterlines[e]],
                [l[(e,k)]                                                          for e in Employees if e in PatternsRewarded.keys() for pat in PatternsRewarded[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for dd in range(1,PatternDuration[(e,pat)]+1) for k in rosterlines[e]],
                [sum([M[(e,pat,dd,g)] * A_g[(e,k,d+dd-1,g)] for g in ShiftGroups]) for e in Employees if e in PatternsRewarded.keys() for pat in PatternsRewarded[e] if PatternDuration[(e,pat)] > 2 for d in PatternDays[(e,pat)] for dd in range(1,PatternDuration[(e,pat)]+1) for k in rosterlines[e]]
                )

    return p
