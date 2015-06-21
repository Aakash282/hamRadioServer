import json
import urllib2
import math

# Loads in database of echonest attributes for each track id
def loadEchonestAttributes():
	# Filename of database
	database_file = 'track_ids70_1_attributes.txt'

	# Dictionary structure to be filled and returned
	echonest_attributes = {}
	database = open(database_file, 'r')
	for line in database:
		row = line.rstrip().split(',') # Removes \n character and splits on ','
		values = [] # List that will contain all 8 attributes for a given track_id
		for i in range (1, 14):
			# If echonest has a valid attribute
			if row[i] != 'None':
				values.append(float(row[i]))

			# If no parameter received from echnoest, set to inf
		else: 
			values.append(float('inf')) 
		echonest_attributes[row[0]] = values # Add track_id : attributes to dictionary
		database.close()
		return echonest_attributes

# Ensures given track_id has corresponding attributes in dictionary
def fetchEchonestAttributes(track_id):
	# First check if track_id is already in dictionary of attributes
	if track_id in echonest_attributes:
		return True

	# If it is not, then we need to query echonest to get the attributes for track_id
else:
	URL = 'http://developer.echonest.com/api/v4/track/profile?api_key=' + 'VBFP0ICNRRIKKKQO6' + '&id=spotify:track:' + track_id + '&bucket=audio_summary'
	data = urllib2.urlopen(URL)
	trackSummary = json.loads(data.read())

		# Too many requests to echonest
		if trackSummary['response']['status']['code'] == 3:
			return False

		# Deal with other errors in echonest db
	elif 'track' not in trackSummary['response'].keys():
		return False 

		# If track_id couldn't be found
	elif 'audio_summary' not in trackSummary['response']['track'].keys():
		return False

		# Some other echonest error
	elif trackSummary['response']['status']['code'] != 0:
		return False

		# If no errors so far, try to get relevant info
		try: 
			summary = trackSummary['response']['track']['audio_summary']
		except KeyError, e: 
			return False

			values = []
			keys = summary.keys()
		# If all keys exist then create list to be returned
		if keys == ['key','tempo','energy','liveness','analysis_url','speechiness','acousticness','instrumentalness','mode','time_signature','duration','loudness','valence','danceability']:
			for param in keys:
				# Ignore url
				if param == 'analysis_url':
					continue

				# Check if value is none
				if summary[param]:
					values.append(float(summary[param]))

				# If no parameter received from echnoest, set to inf
			else: 
				values.append(float('inf')) 

			# Add attributes to dictionary
			echonest_attributes[track_id] = values
			return True
		else:
			return False

# Computes hamRadio distance between two tracks. 
# Ensure that tracks are in dictionary before calling this function.
def getHamRadioDistance(seed, track):
	seed_vals = echonest_attributes[seed]
	track_vals = echonest_attributes[track]
	hamRadio_dist = 0
	for i in range (0, len(seed_vals)):
		current_term = (track_vals[i] - seed_vals[i]) ** 2
		if current_term == float('inf') or math.isnan(current_term):
			continue
		else:
			hamRadio_dist += current_term
			hamRadio_dist = hamRadio_dist ** 0.5
			return hamRadio_dist

# Sorts a given list of lists by hamRadio_dist. Input list should be of the form:
# [[track_id1, hamRadio_dist1], [track_id2, hamRadio_dist2], [track_id3, hamRadio_dist3]]
def sortByDist(distances):
	return sorted(distances, key = lambda x: float(x[1]))

	def computeLevDist(track_1, track_2):
		if len(track_1) < len(track_2):
			return computeLevDist(track_2, track_1)
			
    # At this point, len(track_1) >= len(track_2)
    if len(track_2) == 0:
    	return len(track_1)
    	
    	previous_row = range(len(track_2) + 1)
    	for i, c1 in enumerate(track_1):
    		current_row = [i + 1]
    		for j, c2 in enumerate(track_2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than track_2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
            return previous_row[-1]

# Computes the longest common substring
def longest_common_substring(s1, s2):
	m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
	longest, x_longest = 0, 0
	for x in xrange(1, 1 + len(s1)):
		for y in xrange(1, 1 + len(s2)):
			if s1[x - 1] == s2[y - 1]:
				m[x][y] = m[x - 1][y - 1] + 1
				if m[x][y] > longest:
					longest = m[x][y]
					x_longest = x
				else:
					m[x][y] = 0
					return s1[x_longest - longest: x_longest]

# Optimized similarity testing. Returns a value between 0 and 1.
def computeSimilarity(track_1, track_2):
	track_1 = track_1.rstrip()
	track_2 = track_2.rstrip()
	track_1_list = track_1.replace('-', ' ').split()
	track_2_list = track_2.replace('-', ' ').split()

	# Checking for invalid inputs
	if len(track_1) <= 0 or len(track_2) <= 0:
		return 1

	# Checking if a string is entirely contained in another and is longer than two words
elif (track_1 in track_2 and len(track_1_list) > 2) or (track_2 in track_1 and len(track_2_list) > 2):
	return 1

	# Counts number of common words across 2 strings
	num_common_words = 0
	for word in track_1_list:
		if word in track_2_list:
			num_common_words += 1
			track_1_list.remove(word)
			track_2_list.remove(word)
			continue

	# Resets track_1_list and track_2_list
	track_1_list = track_1.replace('-', ' ').split()
	track_2_list = track_2.replace('-', ' ').split()

	common_word_ratio = 2.0 * num_common_words / (len(track_1_list) + len(track_2_list))

	# lcs = longest_common_substring
	lcs = longest_common_substring(track_1, track_2)
	lcs_ratio = 2.0 * len(lcs) / (len(track_1) + len(track_2))

	# Check how many starting words are the same
	pos = 0
	while pos < len(track_1_list) and pos < len(track_2_list) and track_1_list[pos] == track_2_list[pos]:
		# Check if first word is followed by hyphen
		if (track_1_list[pos] + ' -') in track_2 or (track_2_list[pos] + ' -') in track_1:
			return 1
			pos += 1
			
			if pos == 0:
				return max(common_word_ratio, lcs_ratio)
			else:
				return max(common_word_ratio, lcs_ratio) ** (1/pos)
				

				def filterCandidateList(playlist, candidate_list):
					for playlist_track in playlist:
						for candidate_track in candidate_list:
							if 'Commentary' in candidate_track or ' - Live' in candidate_track:
								candidate_list.remove(candidate_track)
								continue
							elif computeSimilarity(playlist_track[1], candidate_track[1]) > 0.7:
								candidate_list.remove(candidate_track)
								continue
								return candidate_list

								def main():
	# global echonest_attributes
	# echonest_attributes = loadEchonestAttributes() 
	# fetchEchonestAttributes('4lwGyv3tbahmN1Z25wdCxa')
	# fetchEchonestAttributes('4qikXelSRKvoCqFcHLB2H2')
	print filterCandidateList([(1, 'help'), (2, 'lol')], [(0, 'helper'), (3, 'this is')])
	# print computeLevDist('apple', 'apple bottom')
	# print getHamRadioDistance('4lwGyv3tbahmN1Z25wdCxa', '4qikXelSRKvoCqFcHLB2H2')
	# print sortByDist([['A', float('inf')], ['B', -4.219], ['C', 0]])
	# print computeSimilarity('Years - Vocal Extended Mix', 'Years of Life - Extended Instrumental Mix')
	print computeSimilarity('Love Me', 'Love Me Again')

	if __name__ == '__main__':
		main()