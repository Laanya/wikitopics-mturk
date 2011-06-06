import wikipydia
from wikipydia import get_negative_controls, query_text_raw, get_first_section

from splitting import determine_splitter

import datetime
import wpTextExtractor

import sys

date = datetime.date(int((sys.argv[2])[:4]), int((sys.argv[2])[5:7]), int((sys.argv[2])[8:10]))

negatives = get_negative_controls(sys.argv[1], date, int(sys.argv[3]))

for article in negatives:
    print article.replace("_", " "), '\t', 
    print '-1', '\t',
    first_sentence = ''
    paragraph = ''
    text = query_text_raw(article,sys.argv[1])['text']
    sentences, tags = wpTextExtractor.wiki2sentences(text, determine_splitter(sys.argv[1]), True)
    for sent, tag in zip(sentences, tags):
        if first_sentence == '':
            first_sentence = '1'
            print sent.encode('utf-8').rstrip(), '\t',
        print sent.encode('utf-8'),
        if tag == "LastSentence":
            break

    print ""


#negatives = get_negative_controls(sys.argv[1], date, int(sys.argv[3]))


#for article in negatives:
 #   text = query_text_raw(article, sys.argv[1])['text']
  #  section = get_first_section(text)
   # print article
    #print "-------------------------------------------------"
    #print section
    #print "\n"
