from wikipydia import get_positive_controls
import datetime
import sys
import random
import os

date = datetime.date(int((sys.argv[2])[:4]), int((sys.argv[2])[5:7]), int((sys.argv[2])[8:10]))

# first argument: language
# second argument: date
# third argument: number of days spanned for current news
positives = get_positive_controls(sys.argv[1], date, int(sys.argv[3]))

wikitopics_path = os.environ['WIKITOPICS']
articles_path = wikitopics_path + "/data/articles/" + sys.argv[1] + "/" + (sys.argv[2])[:4] + "/"
first_sentence_path = wikitopics_path + "/data/sentences/first/" + sys.argv[1] + "/" + sys.argv[2][:4] + "/"

for article in positives:
    section_file = open(articles_path + positives[article] + "/" + article + ".sentences")
    tags_file = open(articles_path + positives[article] + "/" + article + ".tags")

    section = section_file.read().split('\n')
    tags = tags_file.read().split('\n')
    sentence = open(first_sentence_path + positives[article] + "/" + article + ".sentences")

    print article.replace("_", " "), '\t',
    print "0000", '\t',
    print sentence.read()[2:].rstrip(), '\t',

    paragraph = ''
    for sent, tag in zip(section, tags):
        print sent,
        if tag == "LastSentence":
            print ""
            break

    
