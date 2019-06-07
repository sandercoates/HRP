import xlrd


def dataLoader(filename = 'testInstances/roster_data_input.xlsx'):
    '''Loads data from the Excel instance sheets.'''

    '''Raw data'''
    # Load Excel workboad
    wb = xlrd.open_workbook(filename)

    # Ignore first (0-index) input sheet
    sheet_index = 1

    # Initialize data dictionary
    data = {}

    # Iterate over all workbook sheets
    while True:
        try:
            sheet = wb.sheet_by_index(sheet_index)
            sheet_index += 1
        except:
            break

        # Handle sheets by type
        if sheet.name == 'non-indexed_parameters':
            # Load parameters into data dictionary (skip header)
            for row in range(1, sheet.nrows):
                # Special case weekdays (list of days)
                if sheet.cell_value(row,0) == 'Weekdays':
                    data[sheet.cell_value(row,0)] = sheet.cell_value(row,1).split(', ')
                elif sheet.cell_value(row,0) == 'problemName':
                    data[sheet.cell_value(row,0)] = sheet.cell_value(row,1)
                else:
                    data[sheet.cell_value(row,0)] = int(sheet.cell_value(row,1))
        #=======================================================================
        elif sheet.name == 'shifts':
            # Initialize shift related sets
            data['ShiftTypes'] = []
            data['ShiftGroups'] = []
            data['ShiftTypesGroup'] = {}
            data['ShiftTypesWorking'] = []
            data['ShiftTypesOff'] = []
            data['T_S'] = {}
            data['T_E'] = {}
            data['T'] = {}
            data['SkillsShiftType'] = {}
            # Iterate over all shifts (skip header)
            for row in range(1, sheet.nrows):
                # Assume all input shift types are unique, add to list of shift types
                shift_type = int(sheet.cell_value(row,0))
                data['ShiftTypes'].append(shift_type)
                # Add shift to working or off
                if sheet.cell_value(row,1) == 'w':
                    data['ShiftTypesWorking'].append(shift_type)
                    # Add shift to associated group
                    shift_group = int(sheet.cell_value(row,2))
                    if shift_group not in data['ShiftGroups']:
                        data['ShiftGroups'].append(shift_group)
                        data['ShiftTypesGroup'][shift_group] = []
                    data['ShiftTypesGroup'][shift_group].append(shift_type)
                    # Add times
                    data['T_S'][shift_type] = float(sheet.cell_value(row,3))
                    data['T_E'][shift_type] = float(sheet.cell_value(row,4))
                    data['T'][shift_type] = float(sheet.cell_value(row,5))
                    data['SkillsShiftType'][shift_type] = [int(float(x)) for x in str(sheet.cell_value(row,6)).split(',')]
                else:
                    data['ShiftTypesOff'].append(shift_type)
        #=======================================================================
        elif sheet.name == 'shift_groups':
            data['NmaxGroup'] = {}
            # Iterate over shift groups
            for col in range(1, sheet.ncols):
                data['NmaxGroup'][int(sheet.cell_value(0,col))] = int(sheet.cell_value(1,col))
        #=======================================================================
        elif sheet.name == 'demand':
            data['Demand'] = {}
            # Iterate over all rows (shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(1, sheet.ncols):
                    # Store in by (day, ShiftType) tuple key
                    data['Demand'][(int(sheet.cell_value(0,col)),
                                    int(sheet.cell_value(row,0)))] = int(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'overcoverage_cost':
            data['OvercoverageCost'] = {}
            # Iterate over all rows (shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(1, sheet.ncols):
                    # Store in by (day, ShiftType) tuple key
                    data['OvercoverageCost'][(int(sheet.cell_value(0,col)),
                                    int(sheet.cell_value(row,0)))] = float(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'undercoverage_cost':
            data['UndercoverageCost'] = {}
            # Iterate over all rows (shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(1, sheet.ncols):
                    # Store in by (day, ShiftType) tuple key
                    data['UndercoverageCost'][(int(sheet.cell_value(0,col)),
                                    int(sheet.cell_value(row,0)))] = float(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'overcoverage_limit':
            data['OvercoverageLimit'] = {}
            # Iterate over all rows (shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(1, sheet.ncols):
                    # Store in by (day, ShiftType) tuple key
                    data['OvercoverageLimit'][(int(sheet.cell_value(0,col)),
                                    int(sheet.cell_value(row,0)))] = int(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'undercoverage_limit':
            data['UndercoverageLimit'] = {}
            # Iterate over all rows (shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(1, sheet.ncols):
                    # Store in by (day, ShiftType) tuple key
                    data['UndercoverageLimit'][(int(sheet.cell_value(0,col)),
                                    int(sheet.cell_value(row,0)))] = int(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'employee_non-indexed_parameters':
            # Ierate over all parameters
            for row in range(1, sheet.nrows):
                # Add parameter to data
                if sheet.cell_value(row, 0) not in data:
                    data[sheet.cell_value(row, 0)] = {}
                # Iterate over all employees (skills require special care)
                if sheet.cell_value(row, 0) == 'SkillsEmployee':
                    for col in range(1, sheet.ncols):
                        data[sheet.cell_value(row,0)][int(sheet.cell_value(0,col))] = [int(float(x)) for x in str(sheet.cell_value(row,col)).split(',')]
                # Nmin is integer
                elif sheet.cell_value(row, 0) == 'Nmin':
                    for col in range(1, sheet.ncols):
                        data[sheet.cell_value(row,0)][int(sheet.cell_value(0,col))] = int(sheet.cell_value(row,col))
                else:
                    for col in range(1, sheet.ncols):
                        data[sheet.cell_value(row,0)][int(sheet.cell_value(0,col))] = float(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'employee_Nmin_g':
            data['NminGroup'] = {}
            # Iterate over all rows (employee parameter tuple)
            for row in range(1, sheet.nrows):
                for col in range(1, sheet.ncols):
                    data['NminGroup'][(int(sheet.cell_value(row,0)),
                                    int(sheet.cell_value(0, col)))] = int(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'employee_costs':
            data['C'] = {}
            # Iterate over all rows (employees and shift types)
            for row in range(1, sheet.nrows):
                # Iterate over all columns (days)
                for col in range(2, sheet.ncols):
                    # Store in by (employee, day, ShiftType) tuple key
                    data['C'][(int(sheet.cell_value(row,0)),
                               int(sheet.cell_value(0,col)),
                               int(sheet.cell_value(row,1)),)] = float(sheet.cell_value(row,col))
        #=======================================================================
        elif sheet.name == 'employee_patterns':
           data['PatternsRewarded'] = {}
           data['PatternsPenalized'] = {}
           data['PatternsIllegal'] = {}
           data['R'] = {}
           data['P'] = {}
           data['WeekdaysStartPattern'] = {}
           data['PatternDuration'] = {}
           data['M'] = {}
           # Iterate over all rows (employee pattern tuples)
           for row in range(1, sheet.nrows):
               # Add pattern to set of employee's patterns based on pattern type
               employee = int(sheet.cell_value(row, 0))
               patternType = sheet.cell_value(row, 2)
               patternNumber = int(sheet.cell_value(row, 1))
               # Ensure employee has list of pattern type
               if employee not in data['Patterns'+patternType]:
                   data['Patterns'+patternType][employee] = []
               # Add pattern to employee's list of patterns
               if patternNumber not in data['Patterns'+patternType][employee]:
                   data['Patterns'+patternType][employee].append(patternNumber)
               # Add penalty/reward if relevant
               if patternType == 'Rewarded':
                   data['R'][(employee, patternNumber)] = float(sheet.cell_value(row, 3))
               if patternType == 'Penalized':
                   data['P'][(employee, patternNumber)] = float(sheet.cell_value(row, 4))
               # Add pattern duration
               data['PatternDuration'][(employee, patternNumber)] = int(sheet.cell_value(row, 5))
               # Add pattern start days
               data['WeekdaysStartPattern'][(employee, patternNumber)] = sheet.cell_value(row, 6).split(', ')
               # Add pattern matrix parameters (shift sequence)
               for col in range(7, 7 + data['PatternDuration'][(employee, patternNumber)]):
                   patternShiftGroup = int(sheet.cell_value(row, col))
                   # Iterate over all shift groups
                   for shiftGroup in data['ShiftGroups']:
                       # Assign matrix index value one if shift group in pattern on day
                       if shiftGroup == patternShiftGroup:
                           data['M'][(employee, patternNumber, col - 7 + 1, shiftGroup)] = 1
                       # Assign zero otherwise
                       else:
                           data['M'][(employee, patternNumber, col - 7 + 1, shiftGroup)] = 0

    '''Derived data'''
    data['Weeks'] = [w for w in range(1, data['nWeeks'] + 1)]
    data['Days'] = [d for d in range (1, data['nDays'] + 1)]
    data['Employees'] = [e for e in range(1, data['nEmployees'] + 1)]
    #===========================================================================
    data['FollowingShiftsIllegal'] = {}
    data['FollowingShiftsPenalty'] = {}
    for s1 in data['ShiftTypesWorking']:
        ShiftsIllegal = []
        ShiftsPenalty = []
        for s2 in data['ShiftTypesWorking']:
            # Indentify shifts s2 that cannot follow shift s1
            if data['T_S'][s2] + data['H'] - data['T_E'][s1] < data['T_R']:
                ShiftsIllegal.append(s2)
            # Indentify shifts s2 that incur a penalty if following shift s1
            elif data['T_S'][s2] + data['H'] - data['T_E'][s1] < data['T_RS']:
                ShiftsPenalty.append(s2)
        # As long as the lists are not empty, store data on shift tuples
        if ShiftsIllegal:
            data['FollowingShiftsIllegal'][s1] = ShiftsIllegal
        if ShiftsPenalty:
            data['FollowingShiftsPenalty'][s1] = ShiftsPenalty
    #===========================================================================
    data['StrictDayOff1'] = {}
    data['StrictDayOff2'] = {}
    for s1 in data['ShiftTypesWorking']:
        DayOff1 = []
        DayOff2 = []
        for s2 in data['ShiftTypesWorking']:
            # Indentify shifts s2 that cannot follow shift s1 for a strict day off
            if data['T_S'][s2] + 2*data['H'] - data['T_E'][s1] < data['H_S1']:
                DayOff1.append(s2)
            # Indentify shifts s2 that cannot follow shift s1 for two strict days off
            if data['T_S'][s2] + 3*data['H'] - data['T_E'][s1] < data['H_S2']:
                DayOff2.append(s2)
        if DayOff1:
            data['StrictDayOff1'][s1] = DayOff1
        if DayOff2:
            data['StrictDayOff2'][s1] = DayOff2
    #===========================================================================
    # Calculate days in week
    data['DaysInWeek'] = {}
    for w in data['Weeks']:
        data['DaysInWeek'][w] = [d for d in range(7*(w-1)+1, 7*(w-1) + 8) if d <= data['nDays']]
    #===========================================================================
    # Calculate weekdays in week
    data['WeekendDaysInWeek'] = {} # This assumes starting on a Monday and ends on a Sunday
    for w in data['Weeks']:
        data['WeekendDaysInWeek'][w] = [6 + 7*(w-1), 7 + 7*(w-1)]
    #===========================================================================
    # Indentify days on weekday
    data['DaysOnWeekday'] = {} # This assumes starting on a Monday and ends on a Sunday
    def weekdayNumber(b):
        #Returns number of weekday
        return {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6, 'SUN': 7}[b]
    for b in data['Weekdays']:
        data['DaysOnWeekday'][b] = [d for d in data['Days'] if d % 7 == weekdayNumber(b) % 7]
    #===========================================================================
    # Indentify days on weekday in week
    data['DaysOnWeekdayInWeek'] = {}
    for b in data['Weekdays']:
        for w in data['Weeks']:
            data['DaysOnWeekdayInWeek'][(w, b)] = [d for d in data['DaysInWeek'][w] if d % 7 == weekdayNumber(b) % 7]
    #===========================================================================
    # Calculate start days of patterns
    data['PatternDays'] = {} #List of start days for each pattern
    for e in data['Employees']:
        if e in data['PatternsRewarded']:
            for pat in data['PatternsRewarded'][e]:
                PatternDaysVec = []
                for b in data['WeekdaysStartPattern'][(e, pat)]:
                    for d in data['DaysOnWeekday'][b]:
                        if d <= data['nDays'] - data['PatternDuration'][(e, pat)] + 1:
                            PatternDaysVec.append(d)
                PatternDaysVec.sort()
                data['PatternDays'][(e, pat)] = PatternDaysVec
        if e in data['PatternsPenalized']:
            for pat in data['PatternsPenalized'][e]:
                PatternDaysVec = []
                for b in data['WeekdaysStartPattern'][(e, pat)]:
                    for d in data['DaysOnWeekday'][b]:
                        if d <= data['nDays'] - data['PatternDuration'][(e, pat)] + 1:
                            PatternDaysVec.append(d)
                PatternDaysVec.sort()
                data['PatternDays'][(e, pat)] = PatternDaysVec
        if e in data['PatternsIllegal']:
            for pat in data['PatternsIllegal'][e]:
                PatternDaysVec = []
                for b in data['WeekdaysStartPattern'][(e, pat)]:
                    for d in data['DaysOnWeekday'][b]:
                        if d <= data['nDays'] - data['PatternDuration'][(e, pat)] + 1:
                            PatternDaysVec.append(d)
                PatternDaysVec.sort()
                data['PatternDays'][(e, pat)] = PatternDaysVec
    #===========================================================================
    # Calculate norm period start days (for workload calculation)
    data['NormPeriodStartDays'] = []
    d = 1
    while d <= data['nDays']:
        data['NormPeriodStartDays'].append(d)
        d += data['N_N']
    #===========================================================================

    return data
