import csv
import operator
import codecs
import sys

## opening the file and initializing first variables
## hits(list): holds all hits
## header_index(dictionary): holds headers
## blank_hits (list): holds the blank hits

blank_hits = []
worker_ID_list = []
total = 0.0

#reads in the file
filename = sys.argv[1]
output_filename = sys.argv[1].replace('.csv', '') + '-to-upload.csv'

#opens the file
csv_reader = csv.reader(open(filename))
csv_writer = csv.writer(open(output_filename, 'wb'), delimiter=',', quotechar='"')

#reads in the headers
header_index = {}
headers_in_order = csv_reader.next()
for i, header in enumerate(headers_in_order):
   header_index[header] = i

#reads in the hits
hits = []
for hit in csv_reader:
    hits.append(hit)

#gets the average blank-ness of hits
def get_average_blank():
    counter = 0.0
    for hit in hits:
        for i in range(0,11):
	     answer_string = 'Answer.newsworthy' + str(i)
             if hit[header_index[answer_string]] == "":
                 counter += 1.0
             answer2_string = 'Answer.when newsworthy' + str(i)
             if hit[header_index[answer2_string]] == "":
	         counter += 1.0

    return counter/len(hits)

#function to check for blank hits
def check_blank(hit):
    counter = 0
    for i in range(0,11):
	answer_string = 'Answer.newsworthy' + str(i)
        if hit[header_index[answer_string]] == "":
            counter += 1
        answer2_string = 'Answer.when newsworthy' + str(i)
        if hit[header_index[answer2_string]] == "":
	    counter += 1
    return counter

#gets the percentage scores for controls for each Turker
def get_grades():
   grades = {}
   correct_rates = {}
   for hit in hits:
       worker_ID = hit[header_index['WorkerId']]
       global total
       answer_positive = hit[header_index['Answer.newsworthy10']]
       total += 1.0
       if not grades.has_key(worker_ID):
           grades[worker_ID] = {}
           grades[worker_ID]['positive'] = 0
           grades[worker_ID]['num_total'] = 0.0
           worker_ID_list.append(worker_ID)
       if answer_positive == 'Yes':
           grades[worker_ID]['positive'] += 1.0
       grades[worker_ID]['num_total'] += 1.0

   for w in worker_ID_list:
       correct_rates[w] = grades[w]['positive'] / grades[w]['num_total']

   print correct_rates
   return correct_rates

#calls the function to get the average blank
average_blank = get_average_blank()
worker_rates = get_grades()

print average_blank, "\n"
print worker_rates, "\n"

#loops through the hits to approve/reject

#writes the headers
csv_writer.writerow(headers_in_order)
#counts how many hits there are to approve/reject
expected_length = max(header_index['Approve'], header_index['Reject'])
for hit in hits:
    while len(hit) < expected_length+1:
        hit.append(' ')
    if hit[header_index['AssignmentStatus']] == 'Submitted':
        worker_id = hit[header_index['WorkerId']]
        feedback = hit[header_index['RequesterFeedback']]
	positive_control = hit[header_index['Answer.newsworthy10']]
	negative_control = hit[header_index['Answer.newsworthy11']]
	positive2_control = hit[header_index['Answer.when newsworthy10']]
	negative2_control = hit[header_index['Answer.when newsworthy11']]
        blank_sections = check_blank(hit)
        if feedback != "":
            pass
        elif blank_sections > average_blank:
            reason = 'Thanks for doing my HIT. You accidentally left this HIT blank. Please be sure to complete the assignment before submitting. Thanks!'
            hit[header_index['Reject']] = reason
            print worker_id, reason
        else: 
            if positive_control == "Yes" and positive2_control != "Never" and negative_control == "No":
                hit[header_index['Approve']] = 'x'
	    elif worker_rates[worker_id] > .8:
                hit[header_index['Approve']] = 'x'
            else:
            	reason = 'Thanks for doing my HIT. In these assignments, you did not answer the control (one of the questions in which we know the answer to) correctly. These control questions were purposely made obvious to make sure that you picked the right answer if you were doing the HIT correctly. If you would like to continue doing these HITs, please be sure to spend more time on them. Thanks!'
            	hit[header_index['Reject']] = reason
            	print worker_id,  reason
        csv_writer.writerow(hit)
