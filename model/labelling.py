import sys
sys.path.append('./classes')
from node import Node
from graph import Graph
from resources import Resources
from label import Label
from helpers import *

def labelling(resources, graph, data, employee, extensionLimit):
	'''SPPRC labelling algorithm. See thesis for algorithmic details'''

	# Initialize start label
	initial_label = Label.initialize(node = graph.nodes[0], resources = resources,
									 data=data, employee=employee)

	# Increment label name
	label_name = initial_label.name + 1

	# Initialize unprocessed_labels and processed_labels
	unprocessed_labels = [initial_label]
	processed_labels = []

	# Assume extension is not limited by extensionLimit
	extension_limited = False

	# While there are unprocessed labels
	while unprocessed_labels:
		# Get an unprocessed label
		cur_label = unprocessed_labels.pop(0)

		# If a limit on the number of labels extended is set, limit extension
		if extensionLimit != None:
			# Set reference lenght of unprocessed labels and cur_label
			referenceLength = 1 + len(unprocessed_labels)
			# Find all labels in unprocessed_labels that are in the node
			unprocessed_labels, labels_in_node = labelsInNode(labels=unprocessed_labels,
										 			  		  label=cur_label,
													  		  size=extensionLimit)
			# Check if no labels are discarded by extensionLimit
			if (not extension_limited and
				len(unprocessed_labels) + len(labels_in_node) < referenceLength):
					extension_limited = True
			# Extend all labels_in_node
			extended_labels = []
			for label in labels_in_node:
				labels, label_name = label.extend(label_name, resources, graph,
												  data, employee)
				extended_labels += labels
		else:
			# Otherwise, extend the label as if there was no limit
			extended_labels, label_name = cur_label.extend(label_name, resources,
														   graph, data, employee)

		# Check dominance among all labels
		for extended_label in extended_labels:
			# The initial hypothesis is that the extended label is not dominated
			extended_label_dominated = False
			# Iterate over processed labels
			for processed_label in processed_labels:
				# Check if extended_label is dominated by processed_label
				if processed_label.dominance(extended_label, resources,
											 data, employee):
					extended_label_dominated = True
				# Check if processed_label is dominated by extended_label
				elif extended_label.dominance(processed_label, resources,
											  data, employee):
					# If so, remove the dominated processed_label
					processed_labels.remove(processed_label)
			# Iterate over unprocessed labels
			for unprocessed_label in unprocessed_labels:
				# Check if extended_label is dominated by unprocessed_label
				if unprocessed_label.dominance(extended_label, resources,
											   data, employee):
					extended_label_dominated = True
				# Check if unprocessed_label is dominated by extended_label
				elif extended_label.dominance(unprocessed_label, resources,
											  data, employee):
					unprocessed_labels.remove(unprocessed_label)
			# If extended_label is not dominated, add it to unprocessed_labels
			if not extended_label_dominated:
				unprocessed_labels.append(extended_label)
		# Add unprocessed_label to the set of processed_labels
		if extensionLimit == None:
			processed_labels.append(cur_label)
		else:
			processed_labels += labels_in_node

	return processed_labels, extension_limited
