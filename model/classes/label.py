from node import Node

class Label:
    '''Dependent on Node, Graph and resources classes'''

    def __init__(self, name: int = None, node: Node = Node(),
                 path: [Node] = [None], cost: float = None,
                 resourceValues: dict = {}):
        self.name = name
        self.node = node
        self.path = path
        self.cost = cost
        self.resourceValues = resourceValues

    def __repr__(self):
        rep = ("Label:\t\t" + str(self.name)
            + "\n-----------------"
            + "\nNode:\t\t" + str(self.node.name)
            + ",\nDay:\t\t" + str(self.node.day)
            + ",\nShift type:\t" + str(self.node.shiftType)
            + ",\nCost:\t\t" + str(self.cost))
        for r in self.resourceValues:
            rep = rep + ",\n" + r + ":\t\t" + str(self.resourceValues[r]) + '\n'
        return rep

    def initialize(node, resources, data, employee):
        '''initialize first label in start node with initial resource values'''
        resourceValues = resources.initialize(data=data, employee=employee)
        label = Label(name = 1, node = node, path = [node], cost = 0,
                      resourceValues = resourceValues)
        return label

    def feasible(self, resources, data, employee):
        '''Check label resource feasibility'''
        return resources.feasible(resourceValues = self.resourceValues,
                                  d = self.node.day,
                                  s = self.node.shiftType,
                                  data = data,
                                  employee = employee)

    def extend(self, label_name, resources, graph, data, employee):
        '''Extend self (label) along all arcs. Return list of extended labels'''
        extended_labels = []
        # Iterate over neighbors to the current node
        for destination in self.node.neighbors:
            # Initialize a new label with the extension and associated arc cost
            label = Label(name = label_name, node = destination,
                          path = self.path + [destination],
                          cost = self.cost + graph.costs[(self.node, destination)])
            # Extend all resources
            label.resourceValues = resources.extend(self.resourceValues, label.node.day,
                                               self.node.shiftType,
                                               label.node.shiftType, data,
                                               employee)
            # Check that the label is feasible, append if, delete object if not
            if label.feasible(resources, data, employee):
                extended_labels.append(label)
            # Update label_name
            label_name += 1
        return extended_labels, label_name

    def dominance(self, subordinate, resources, data, employee):
        '''Check if self (label) dominates subordinate. The initial hypothesis
        is that it does.

        If dominanceFreeDays > -1, dominance is neglected in the last
        dominanceFreeDays of the planning period to yield more labels in the end
        node. If dominanceFreeDays = 0, dominance is only neglected in the end
        node.
        '''

        # Neglect dominance in end node
        dominanceFreeDays = 0

        # Labels in different nodes cannot dominate one another
        if self.node != subordinate.node:
            return False
        # Consider dominanceFreeDays (as specified in above function description)
        if self.node.day > data['nDays'] - dominanceFreeDays:
            return False
        # Self must have a weakly lower cost to dominate subordinate
        if self.cost > subordinate.cost:
            return False
        # Self must dominate subordinate with respect to all resourceValues
        if not resources.dominance(self.resourceValues, subordinate.resourceValues,
                                   data, employee):
            return False
        # If all dominance criteria satisfied, self dominates subordinate
        return True
