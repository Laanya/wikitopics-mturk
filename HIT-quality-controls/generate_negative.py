import wikipydia
from wikipydia import query_random_titles

import datetime
import sys
import os

date = datetime.date(int((sys.argv[2])[:4]), int((sys.argv[2])[5:7]), int((sys.argv[2])[8:10]))

loops = 1

if (len(sys.argv) > 4):
    loops = int(sys.argv[4])

random = query_random_titles(sys.argv[1], int(sys.argv[3]))

"""
For purpose of debugging the difference function for sets
(python generate_negative.py en 2011-05-11 50 15)
random.append('The_Pirate_Bay')
"""

wikitopics_path = os.environ['WIKITOPICS']
articles_path = wikitopics_path + "/data/articles/" + sys.argv[1] + "/" + (sys.argv[2])[:4] + "/"

top_news = []
for i in range(0, loops):
    previousdays = datetime.timedelta(days=i)
    new_date = date - previousdays;
    articles = articles_path + new_date.strftime("%Y-%m-%d")
    if (os.path.exists(articles)):
        listing = os.listdir(articles)

        for infile in listing:
            if infile[-2:] == "es":
                top_news.append(infile[:-10])

difference = filter(lambda x:x not in top_news, random)

"""
For debugging
print random
print "\n\n\n"
print top_news
print "\n\n\n"
"""
return difference
