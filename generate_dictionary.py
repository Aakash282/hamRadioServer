# Loads in database of echonest attributes for each track id
def load_echonest_attributes():
	# Filename of database
	database_file = 'track_ids70_1_attributes.txt'

	# Dictionary structure to be filled and returned
	echonest_attributes = {}
	database = open(database_file, 'r')
	for line in database:
		row = line.rstrip().split(',') # Removes \n character and splits on ','
		values = [] # List that will contain all 8 attributes for a given track_id
		for i in range (1, 9):
			# If echonest has a valid attribute
			if row[i] != 'None':
				values.append(float(row[i]))

			# If no parameter received from echnoest, set to inf
			else: 
				values.append(float('inf')) 
		echonest_attributes[row[0]] = values # Add track_id : attributes to dictionary
	database.close()
	return echonest_attributes
	