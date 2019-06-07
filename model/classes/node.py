class Node:
    '''Node respresentation for SPPRC implementation'''

    def __init__(self,
                 name: int = None,
                 neighbors = None,
                 day: int = None,
                 shiftType: int  = None):
        self.name = name
        if neighbors == None:
            neighbors = []
        self.neighbors = neighbors
        self.day = day
        self.shiftType = shiftType

    def __repr__(self):
        '''Represent node by name and vector of neighbors' names'''
        repr = str(self.name)+': ['
        for neighbor in self.neighbors:
            if repr[-1] != '[':
                repr += ', '
            repr += str(neighbor.name)
        repr += ']'
        return repr
