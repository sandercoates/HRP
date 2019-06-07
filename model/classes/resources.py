class Resources:
    '''All resource definitions and functions to extend resourceValues and check
    feasibility.
    Allowed resourceValues are TWMax, TWMin, TWMax_g, TWMin_g, TH, TV, TL, TI.

    Initial values are returned after taking data as input

        def initial_name(self, data, employee):
            return value

    All REFs take resource value, d, i and j as input:

        def ref_name(self, value, d, i, j, data, employee):
            # ...
            return value

    Resource windows are given on day d, shift type s:

        def window_name(self, value, d, s, data, employee):
            # ...
            return [lwr, upr]

    Dominance criteria are gived with the initial hypothesis that they are
    satisfied (i.e. superior dominates subordinate). Check if superior dominates
    subordinate with respect to the resource "name".

        def dominance_name(self, superior_value, subordinate_value, data):
            # if (condition):
            #    return False
            return True

    resource_list:  list of the resource names
    resourceValues: dictionary with keys from resource_list and resource values
    employee:       employee id (integer)
    d:              integer day
    s:              shit type
    i:              shift type assigned on day d - 1
    j:              shift type assigned on day d
    '''

    def __init__(self, resource_list):
        '''Define "active" resources'''
        # Default is empty list of active resources
        self.resource_list = []
        # Iterate over input list of resources
        for r in resource_list:
            # If initial value, REF, resource window and dominance is defined...
            if (hasattr(self, 'initial_%s' % r)
                and hasattr(self, 'ref_%s' % r)
                and hasattr(self, 'window_%s' % r)
                and hasattr(self, 'dominance_%s' % r)):
                # ...add the resource to the list of active resources
                self.resource_list.append(r)

    def __repr__(self):
        return str(self.resource_list)

    def initialize(self, data, employee):
        '''Generate initial resources for first label'''
        resourceValues = {}
        # Iterate over all resources
        for r in self.resource_list:
            # Get the respective initial resource value
            resourceValues[r] = getattr(self, 'initial_%s' % r)(data, employee)
        # Return initial resources
        return resourceValues

    def extend(self, resourceValues, d, i, j, data, employee):
        '''Extend all resources along arc from shift type i on day d - 1 to
        shift type j on day d
        '''
        # Initialize the extended resources (different from input resources)
        extended_resourceValues = {}
        # Iterate over all resources
        for r in resourceValues:
            # Update the resource by calling the respective REF
            extended_resourceValues[r] = getattr(self, 'ref_%s' % r)(resourceValues[r],
                                                                     d, i, j, data)
        # Return the updated resources
        return extended_resourceValues

    def feasible(self, resourceValues, d, s, data, employee):
        '''Check resource feasibility on day d, shift type s'''
        # Resource feasibility is inevitable in start and end node
        if (d in [0, data['Days'][-1] + 1]) and (s == 0):
            return True
        # Iterate over all resources
        for r in self.resource_list:
            # Get the lower (lwr) and upper (upr) bound for node d, s
            window = getattr(self, 'window_%s' % r)(resourceValues[r], d, s, data,
                                                    employee)
            # Check if resource window is indexed
            if type(window) == dict:
                for i in window:
                    lwr, upr = window[i]
                    # Not feasible if the resource is outside the resource window
                    if (resourceValues[r][i] < lwr) or (upr < resourceValues[r][i]):
                        return False
            # Not feasible if the resource is outside the resource window
            else:
                [lwr, upr] = window
                if (resourceValues[r] < lwr) or (upr < resourceValues[r]):
                    return False
        # If all resources within resource windows, resource feasible
        return True

    def dominance(self, superior_resourceValues, subordinate_resourceValues, data, employee):
        '''Check if superior dominates subordinate with respect to resourceValues'''
        # Iterate over all resources
        for r in self.resource_list:
            # If any resource does not allow dominance, return false
            if not getattr(self, 'dominance_%s' % r)(superior_resourceValues[r],
                                                     subordinate_resourceValues[r],
                                                     data, employee):
                return False
        # Initial hypothesis is that superior dominates subordinate resources
        return True


    '''Minimum consecutive days working'''
    def initial_TWMin(self, data, employee):
        # See the thesis for mathematical details
        return data['Nmin'][employee]

    def ref_TWMin(self, TWMin, d, i, j, data):
        # See the thesis for mathematical details
        ShiftTypesWorking = data['ShiftTypesWorking']
        if (i in ShiftTypesWorking) and (j in ShiftTypesWorking):
            return TWMin + 1
        elif (i not in ShiftTypesWorking) and (j in ShiftTypesWorking):
            return 1
        else:
            return TWMin

    def window_TWMin(self, TWMin, d, s, data, employee):
        # See the thesis for mathematical details
        if s in data['ShiftTypesWorking']:
            return [0, float('inf')]
        # Sligt deviation from mathematical formulation for speed-up
        return [data['Nmin'][employee], float('inf')]

    def dominance_TWMin(self, superior_TWMin, subordinate_TWMin, data, employee):
        # See the thesis for mathematical details
        if ((superior_TWMin < data['Nmin'][employee])
            and (superior_TWMin < subordinate_TWMin)):
            return False
        return True

    '''Minimum consecutive days working shift group'''
    def initial_TWMin_g(self, data, employee):
        # See the thesis for mathematical details
        initial_TWMin_g = {}
        for g in data['ShiftGroups']:
            initial_TWMin_g[g] = data['NminGroup'][(employee, g)]
        return initial_TWMin_g

    def ref_TWMin_g(self, TWMin_g, d, i, j, data):
        # See the thesis for mathematical details
        extended_TWMin_g = {}
        ShiftTypesGroup = data['ShiftTypesGroup']
        for g in ShiftTypesGroup:
            if ((i in ShiftTypesGroup[g]) and
                (j in ShiftTypesGroup[g])):
                extended_TWMin_g[g] = TWMin_g[g] + 1
            elif ((i not in ShiftTypesGroup[g]) and
                  (j in ShiftTypesGroup[g])):
                extended_TWMin_g[g] = 1
            else:
                extended_TWMin_g[g] = TWMin_g[g]
        return extended_TWMin_g

    def window_TWMin_g(self, TWMin_g, d, s, data, employee):
        # See the thesis for mathematical details
        ShiftTypesGroup = data['ShiftTypesGroup']
        window = {}
        for g in ShiftTypesGroup:
            if s in ShiftTypesGroup[g]:
                window[g] = [0, float('inf')]
            # Sligt deviation from mathematical formulation for speed-up
            else:
                window[g] = [data['NminGroup'][(employee, g)], float('inf')]
        return window

    def dominance_TWMin_g(self, superior_TWMin_g, subordinate_TWMin_g, data, employee):
        # See the thesis for mathematical details
        for g in data['ShiftGroups']:
            if ((superior_TWMin_g[g] < data['NminGroup'][(employee, g)])
                and (superior_TWMin_g[g] < subordinate_TWMin_g[g])):
                return False
        return True

    '''Maxium consecutive days working'''
    def initial_TWMax(self, data, employee):
        # See the thesis for mathematical details
        return 0

    def ref_TWMax(self, TWMax, d, i, j, data):
        # See the thesis for mathematical details
        if j in data['ShiftTypesWorking']:
            return TWMax + 1
        else:
            return 0

    def window_TWMax(self, TWMax, d, s, data, employee):
        # See the thesis for mathematical details
        return [0, data['Nmax']]

    def dominance_TWMax(self, superior_TWMax, subordinate_TWMax, data, employee):
        # See the thesis for mathematical details
        if superior_TWMax > subordinate_TWMax:
            return False
        return True

    '''Minimum number of weekends off'''
    def initial_TV(self, data, employee):
        # See the thesis for mathematical details
        initial_TV = {}
        W_W=data['W_W']
        for t in range(1, W_W + 1):
            initial_TV[t] = 0
        return initial_TV

    def ref_TV(self, TV, d, i, j, data):
        # See the thesis for mathematical details
        extended_TV = {}
        W_W=data['W_W']
        for t in range(1, W_W + 1):
            if ((d in data['DaysOnWeekday']['SAT']) and
                (i in data['ShiftTypes'] + [0]) and
                (j in data['ShiftTypesWorking'])):
                extended_TV[t] = TV[t] + 1
            # Sligt deviation from mathematical formulation for speed-up
            elif (d in data['DaysOnWeekday']['MON']):
                for w in data['Weeks']:
                    if d in data['DaysOnWeekdayInWeek'][(w, 'MON')]:
                        if t - 1 == w % W_W:
                            extended_TV[t] = 0
                        else:
                            extended_TV[t] = TV[t]
                        break
            else:
                extended_TV[t] = TV[t]

        return extended_TV

    def window_TV(self, TV, d, s, data, employee):
        # See the thesis for mathematical details
        window = {}
        for t in range(1, data['W_W'] + 1):
            window[t] = [0, data['W_W'] - data['Nmin_W']]
        return window

    def dominance_TV(self, superior_TV, subordinate_TV, data, employee):
        # See the thesis for mathematical details
        for t in range(1, data['W_W'] + 1):
            if superior_TV[t] > subordinate_TV[t]:
                return False
        return True
