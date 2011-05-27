import wikipydia
from wikipydia import query_current_events

import datetime
import sys
import os

date = datetime.date(int((sys.argv[2])[:4]), int((sys.argv[2])[5:7]), int((sys.argv[2])[8:10]))

loops = 1

if (len(sys.argv) > 3):
    loops = int(sys.argv[3])
current_news = query_current_events(date, loops)
top_news = []

wikitopics_path = os.environ['WIKITOPICS']

articles_path = wikitopics_path + "/data/articles/" + sys.argv[1] + "/" + (sys.argv[2])[:4] + "/"
for i in range(0, loops):
    previousdays = datetime.timedelta(days=i)
    new_date = date - previousdays;
    articles = articles_path + new_date.strftime("%Y-%m-%d")
    if (os.path.exists(articles)):
        listing = os.listdir(articles)

        for infile in listing:
            if infile[-2:] == "es":
                top_news.append(infile[:-10])

intersection = list(set(current_news) & set(top_news))

print current_news
print "\n\n\n\n"
print top_news
print "\n\n\n\n"
print intersection