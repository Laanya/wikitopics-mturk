#!/usr/bin/env python

"""
Interface to Wikipedia. Their API is in beta and subject to change.
As a result, this code is also in beta and subject to unexpected brokenness.

http://en.wikipedia.org/w/api.php
http://github.com/j2labs/wikipydia

jd@j2labs.net
"""

import urllib
import json as simplejson

import calendar
import datetime

import os
import sys
import time

import re

api_url = 'http://%s.wikipedia.org/w/api.php'

def _unicode_urlencode(params):
	"""
	A unicode aware version of urllib.urlencode.
	Borrowed from pyfacebook :: http://github.com/sciyoshi/pyfacebook/
	"""
	if isinstance(params, dict):
		params = params.items()
	return urllib.urlencode([(k, isinstance(v, unicode) and v.encode('utf-8') or v) for k, v in params])

def _run_query(args, language, retry=5, wait=5):
	"""
	takes arguments and optional language argument and runs query on server
	if a socket error occurs, wait the specified seconds of time and retry for the specified number of times
	"""
	url = api_url % (language)
	data = _unicode_urlencode(args)
	while True:
		try:
			search_results = urllib.urlopen(url, data=data)
			json = simplejson.loads(search_results.read())
		except:
			if not retry:
				raise
			retry -= 1
			time.sleep(wait)
		else:
			break
	return json


def opensearch(query, language='en'):
	"""
	action=opensearch
	"""
	query_args = {
		'action': 'opensearch',
		'search': query,
		'format': 'json'
	}
	return _run_query(query_args, language)

def get_page_id(title, query_results):
   """
   Extracts the title's pageid from the query results.
   Assumes queries of the form query:pages:id, 
   and properly handle the normalized method.
   Returns -1 if it cannot find the page id
   """
   if 'normalized' in query_results['query'].keys():
	   for normalized in query_results['query']['normalized']:
		   if title == normalized['from']:
			  title = normalized['to']
   for page in query_results['query']['pages']:
	   if title == query_results['query']['pages'][page]['title']:
		  return str(query_results['query']['pages'][page]['pageid'])
   return str(-1)


def query_page_id(title, language='en'):
   """
   Queries for the title's pageid.
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'prop': 'info',
	   'titles': title,
	   'format': 'json',
   }
   json = _run_query(query_args, language)
   return get_page_id(title, json)

def query_exists(title, language='en'):
	"""
	Query if the page of the title exists.
	"""
	if title.find('|') != -1:
		return False
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'titles': title,
		'format': 'json',
	}
	json = _run_query(query_args, language)
	# check if it is an inter-wiki title e.g. Commons:Main_Page
	if 'pages' not in json['query']:
		return False
	for page_id, page_info in json['query']['pages'].items():
		if int(page_id) > 0:
			if 'missing' not in page_info and 'invalid' not in page_info:
				return True
	return False

def query_normalized_title(title, language='en'):
	"""
	Query the normalization of the title.
	title is a Unicode string.
	"""
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'titles': title,
		'format': 'json',
	}
	json = _run_query(query_args, language)
	if 'normalized' in json['query']:
		for pair in json['query']['normalized']:
			if title == pair['from']:
				title = pair['to']
	return title

def query_redirects(title, language='en'):
	"""
	Query the normalization of the title.
	title is a Unicode string.
	"""
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'titles': title,
		'format': 'json',
		'redirects': '',
	}
	json = _run_query(query_args, language)
	if 'normalized' in json['query']:
		for pair in json['query']['normalized']:
			if title == pair['from']:
				title = pair['to']
	if 'redirects' in json['query']:
		for pair in json['query']['redirects']:
			if title == pair['from']:
				title = pair['to']
	return title

def query_revid_by_date(title, language='en', date=datetime.date.today(), time="000000", direction='older', limit=1):
	"""
	Query for the revision ID of an article on a certain date.  
	Return 0 if no revision ID is found.
	This method can be used in conjuction with query_text_raw_by_revid
	"""
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'format': 'json',
		'prop': 'revisions',
		'rvprop': 'ids',
		'titles': title,
		'rvdir': direction,
		'rvlimit': limit,
		'rvstart': date.strftime("%Y%m%d")+time
		}
	json = _run_query(query_args, language)
	pageid = json['query']['pages'].keys()[0]
	if 'revisions' not in json['query']['pages'][pageid]:
		return 0
	revid = json['query']['pages'][pageid]['revisions'][0]['revid']
	return revid


def query_revid_by_date_fallback(title, language='en', date=datetime.date.today(), time="235959"):
	"""
	Query for revision ID of an article on a certain date.
	If the article was moved later, it fallsback to the moved article.
	The title argument is a Unicode string.
	Return 0 if there exists no such an revision before the date.
	"""
	revid = query_revid_by_date(title, language, date, time=time, direction="older")
	while not revid:
		# the page was moved later
		revid = query_revid_by_date(title, language, date, time=time, direction='newer')
		if not revid:
			return 0
		redirects = query_text_raw_by_revid(revid, language)['text']
		if not redirects or not redirects.lower().startswith('#redirect [[') or not redirects.endswith(']]'):
			return 0
		title = redirects[12:-2]
		revid = query_revid_by_date(title, language, date, time="235959", direction="older")
	return revid


def query_language_links(title, language='en', limit=250):
   """
   action=query,prop=langlinks
   returns a dict of inter-language links, containing the lang abbreviation
   and the corresponding title in that language
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'prop': 'langlinks',
	   'titles': title,
	   'format': 'json',
	   'lllimit': limit
   }
   json = _run_query(query_args, language)
   page_id = get_page_id(title, json)
   lang_links = {}
   if 'langlinks' in json['query']['pages'][page_id].keys():
	   lang_links = dict([(ll['lang'],ll['*']) for ll in json['query']['pages'][page_id]['langlinks']])
   return lang_links


def query_categories(title, language='en'):
   """
   action=query,prop=categories
   Returns a full list of categories for the title
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'prop': 'categories',
	   'titles': title,
	   'format': 'json',
   }
   categories = []
   while True:
	  json = _run_query(query_args, language)
	  for page_id in json['query']['pages']:
		  if 'categories' in json['query']['pages'][page_id].keys():
			  for category in json['query']['pages'][page_id]['categories']:
				  categories.append(category['title'])
	  if 'query-continue' in json:
		  continue_item = json['query-continue']['categories']['clcontinue']
		  query_args['clcontinue'] = continue_item
	  else:
		  break
   return categories


def query_categories_by_revid(revid, language='en'):
   """
   action=query,prop=categories
   Returns a full list of categories for the revision id
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'prop': 'categories',
	   'revids': revid,
	   'format': 'json',
   }
   categories = []
   while True:
	  json = _run_query(query_args, language)
	  for page_id in json['query']['pages']:
		  if 'categories' in json['query']['pages'][page_id].keys():
			  for category in json['query']['pages'][page_id]['categories']:
				  categories.append(category['title'])
	  if 'query-continue' in json:
		  continue_item = json['query-continue']['categories']['clcontinue']
		  query_args['clcontinue'] = continue_item
	  else:
		  break
   return categories


def query_category_members(category, language='en', limit=100):
   """
   action=query,prop=categories
   Returns all the members of a category up to the specified limit
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'list': 'categorymembers',
	   'cmtitle': category,
	   'format': 'json',
	   'cmlimit': min(limit, 500)
   }
   members = []
   while True:
	  json = _run_query(query_args, language)
	  for member in json['query']['categorymembers']:
		  members.append(member['title'])
	  if 'query-continue' in json and len(members) <= limit:
		  continue_item = json['query-continue']['categorymembers']['cmcontinue']
		  query_args['cmcontinue'] = continue_item
	  else:
		  break
   return members[0:limit]


def query_random_titles(language='en', num_items=10):
   """
   action=query,list=random
   Queries wikipedia multiple times to get random pages from namespace 0
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'list': 'random',
	   'format': 'json',
   }
   random_titles = []
   while len(random_titles) < num_items:
	  json = _run_query(query_args, language)
	  for random_page in json['query']['random']:
		  if random_page['ns'] == 0:
			  random_titles.append(random_page['title'])
   return random_titles




def query_links(title, language='en'):
   """
   action=query,prop=categories
   Returns a full list of links on the page
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'prop': 'links',
	   'titles': title,
	   'format': 'json',
   }
   links = []
   while True:
	  json = _run_query(query_args, language)
	  for page_id in json['query']['pages']:
		  if 'links' in json['query']['pages'][page_id].keys():
			  for category in json['query']['pages'][page_id]['links']:
				  links.append(category['title'])
	  if 'query-continue' in json:
		  continue_item = json['query-continue']['links']['plcontinue']
		  query_args['plcontinue'] = continue_item
	  else:
		  break
   return links


def query_links_by_revid(revid, language='en'):
   """
   action=query,prop=categories
   Returns a full list of links on the page
   """
   text = query_text_raw_by_revision(revid)['text']
   links = get_links(text).values()
   return links


def query_revision_by_date(title, language='en', date=datetime.date.today(), time="000000", direction='newer', limit=10):
	"""
	Queries wikipeida for revisions of an article on a certain date.  
	CCB: I'm not quite sure what I should be returning just yet...
	"""
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'format': 'json',
		'prop': 'revisions',
		'titles': title,
		'rvdir': direction,
		'rvlimit': limit,
		'rvstart': date.strftime("%Y%m%d")+time
		}
	json = _run_query(query_args, language)
	return json


def query_revision_diffs(rev_id_1, rev_id_2, language='en'):
   """
   Queries wikipedia for the diff between two revisions of an article 
   CCB: I'm not quite sure what I should be returning just yet...
   """
   url = api_url % (language)
   query_args = {
	   'action': 'query',
	   'format': 'json',
	   'prop': 'revisions',
	   'revids': min(rev_id_1, rev_id_2),
	   'rvdiffto': max(rev_id_1, rev_id_2)
   }
   json = _run_query(query_args, language)
   return json



def query_page_view_stats(title, language='en', start_date=(datetime.date.today()-datetime.timedelta(1)), end_date=datetime.date.today()):
	"""
	Queries stats.grok.se for the daily page views for wikipedia articles
	"""
	stats_api_url = 'http://stats.grok.se/json/%s/%s/%s'
	earliest_date = datetime.date(2007, 01, 01)
	query_date = max(start_date, earliest_date)
	end_date = min(end_date, datetime.date.today())
	total_views = 0
	stats = {}
	stats['monthly_views'] = {}
	while(query_date < end_date):
		query_date_str = query_date.strftime("%Y%m")
		url = stats_api_url % (language, query_date_str, urllib.quote(title.encode('utf-8')))
		search_results = urllib.urlopen(url)
		json = simplejson.loads(search_results.read())
		total_views += json['total_views']
		stats['monthly_views'][query_date_str] = json
		days_in_month = calendar.monthrange(query_date.year, query_date.month)[1]
		query_date = query_date + datetime.timedelta(days_in_month)		
	stats['total_views'] = total_views
	return stats



def query_text_raw(title, language='en'):
	"""
	action=query
	Fetches the article in wikimarkup form
	"""
	query_args = {
		'action': 'query',
		'titles': title,
		'rvprop': 'content',
		'prop': 'info|revisions',
		'format': 'json',
		'redirects': ''
	}
	json = _run_query(query_args, language)
	for page_id in json['query']['pages']:
		if page_id != -1 and 'missing' not in json['query']['pages'][page_id]:
			response = {
				'text': json['query']['pages'][page_id]['revisions'][0]['*'],
				'revid': json['query']['pages'][page_id]['lastrevid'],
			}
			return response
	return None

def query_text_raw_by_revid(revid, language='en'):
	"""
	action=query
	Fetches the specified revision of an article in wikimarkup form
	"""
	url = api_url % (language)
	query_args = {
		'action': 'query',
		'rvprop': 'content',
		'prop': 'info|revisions',
		'format': 'json',
		'revids': revid,
	}
	json = _run_query(query_args, language)
	for page_id, page_info in json['query']['pages'].items():
		if '*' in page_info['revisions'][0]:
			response = {
				'text': json['query']['pages'][page_id]['revisions'][0]['*'],
				'revid': json['query']['pages'][page_id]['lastrevid'],
			}
			return response
	response = {
		'text': None,
		'revid': 0,
	}
	return response


def query_text_rendered_by_revid(revid, language='en'):
	"""
	action=query
	Fetches the specified revision of an article in HTML form
	"""
	url = api_url % (language)
	query_args = {
		'action': 'parse',
		'format': 'json',
		'oldid': revid,
	}
	json = _run_query(query_args, language)
	response = {
		'html': json['parse']['text']['*'],
		'revid': revid,
	}
	return response



def query_random_titles(language='en', num_items=10):
	"""
	action=query,list=random
	Queries wikipedia multiple times to get random articles
	"""

	url = api_url % (language)
	query_args = {
		'action': 'query',
		'list': 'random',
		'format': 'json',
		'rnnamespace': '0',
		'rnlimit': str(num_items),
	} 
	random_titles = []
	while len(random_titles) < num_items:
		json = _run_query(query_args, language)
		for random_page in json['query']['random']:
			random_titles.append(random_page['title'].encode("utf-8").replace(' ', '_'))
	return random_titles
 


def query_text_rendered(page, language='en'):
	"""
	action=parse
	Fetches the article in parsed html form
	"""
	query_args = {
		'action': 'parse',
		'page': page,
		'format': 'json',
		'redirects': ''
	}
	json = _run_query(query_args, language)
	response = {
		'html': json['parse']['text']['*'],
		'revid': json['parse']['revid'],
	}
	return response



def query_rendered_altlang(title, title_lang, target_lang):
	"""
	Takes a title and the language the title is in, asks wikipedia for
	alternative language offerings and fetches the article hosted by
	wikipedia in the target language.
	"""
	lang_links = query_language_links(title, title_lang, lllimit=100)
	if target_lang in lang_links:
		return query_text_rendered(lang_links[target_lang], language=target_lang)
	else:
		return ValueError('Language not supported')


def get_sections(wikified_text):
	"""
	Parses the wikipedia markup for a page and returns
	two arrays, one containing section headers and one
	containing the (marked up) text of the section.
	"""
	title_pattern = re.compile('==.*?==')
	iterator = title_pattern.finditer(wikified_text)
	headers = []
	contents = []
	header = ''
	content_start = 0
	for match in iterator:
		headers.append(header)
		content = wikified_text[content_start:match.start()]
		contents.append(content)
		header = wikified_text[match.start()+2:match.end()-2]
		content_start = match.end()
	headers.append(header)
	content = wikified_text[content_start:len(wikified_text)-1]
	contents.append(content)
	return dict([('headers', headers), ('contents', contents)])


def get_first_section(wikified_text):
        """
        Parses the wikipedia markup for a page and returns
	the firs tsection
        """
        title_pattern = re.compile('==.*?==')
        iterator = title_pattern.finditer(wikified_text)
        content_start = 0
	content = ''
        for match in iterator:
                content = wikified_text[content_start:match.start()].encode("utf-8")
		break
	return content


def get_links(wikified_text):
	"""
	Parses the wikipedia markup for a page and returns
	a dict of rendered link text onto underlying wiki links
	"""
	link_pattern = re.compile('\[\[.*?\]\]')
	linked_text = {}
	iterator = link_pattern.finditer(wikified_text)
	for match in iterator:
		link = wikified_text[match.start()+2:match.end()-2].split('|', 1)
		linked_text[link[-1]] = link[0]
	return linked_text


def get_article_titles(wikified_text):
	"""
	Parses the wikipedia markup for a page and returns
	an array of article titles linked
	Will change unicode string to UTF-8
	"""
	link_pattern = re.compile('\[\[.*?\]\]')
	linked_text = []
	iterator = link_pattern.finditer(wikified_text)
	for match in iterator:
		link = wikified_text[match.start()+2:match.end()-2].split('|', 1)
		link_title = link[0].encode("utf-8")
		linked_text.append(link_title.replace(' ', '_'))
	return linked_text


def get_externallinks(wikified_text):
	"""
	Parses the wikipedia markup for a page and returns
	a dict of rendered link text onto underlying wiki links
	"""
	link_pattern = re.compile(r'\[[^[\]]*?\](?!\])')
	linked_text = {}
	iterator = link_pattern.finditer(wikified_text)
	for match in iterator:
		link = wikified_text[match.start()+1:match.end()-1].split(' ', 1)
		linked_text[link[-1]] = link[0]
	return linked_text


def get_parsed_text(wikified_text, language='en'):
	"""
	action=parse
	Parse the given wiki text
	"""
	query_args = {
		'action': 'parse',
		'text': wikified_text,
		'format': 'json'
	}
	json = _run_query(query_args, language)
	return json


def get_plain_text(wikified_text):
	"""
	Strip links and external links from the given text
	"""
	link_pattern = re.compile(r'\[\[(.*?)\]\]')
	link_stripped = link_pattern.sub(lambda x: x.group(1).split('|',1)[-1], wikified_text)
	externallink_pattern = re.compile(r'\[.*?\]')
	all_stripped = externallink_pattern.sub('', link_stripped)
	return all_stripped.strip() 


def get_positive_controls(language, date, num_days):
	"""returns the positive controls for the HIT"""
	current_news = query_current_events(date, num_days)
	top_news = {}

	wikitopics_path = os.environ['WIKITOPICS']

	articles_path = wikitopics_path + "/data/articles/" + language + "/" + str(date.year) + "/"
	for i in range(0, num_days):
		previousdays = datetime.timedelta(days=i)
		new_date = date - previousdays;
		article_date = new_date.strftime("%Y-%m-%d")
		articles = articles_path + article_date
		if (os.path.exists(articles)):
			listing = os.listdir(articles)
			for infile in listing:
				if infile[-2:] == "es":
					top_news[infile[:-10]] = article_date

	intersection = list(set(current_news) & set(top_news.keys()))

	for key,value in top_news.items():
		if key not in intersection:
			del top_news[key]

	"""
	For debugging
	print current_news
	print "\n\n\n\n"
	print top_news
	print "\n\n\n\n"
	"""
	return top_news


def get_negative_controls(language, date, num_random=10, num_days=1):
    """ returns the negative controls for the HIT """
    random = query_random_titles(language, num_random)


    """
    For purpose of debugging the difference function for sets
    (python generate_negative.py en 2011-05-11 50 15)
    random.append('The_Pirate_Bay')
    """

    wikitopics_path = os.environ['WIKITOPICS']
    articles_path = wikitopics_path + "/data/articles/" + language + "/" + str(date.year) + "/"

    top_news = []
    for i in range(0, num_days):
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

def query_current_events(date, numDays=1):
    """
    Retrieves the current events for a specified date.
    Can also retrieve the previous dates if needed.
    Currently only works for English.
    """
    response = []
    oneday = datetime.timedelta(days=1)
    for i in range(0, numDays):
        date = date - oneday
        title = 'Portal:Current_events/' + date.strftime("%Y_%B_") + str(date.day)
        text_raw = query_text_raw(title)
        if not text_raw:
            return None
        text = text_raw['text']
        lines = text.splitlines()
        for line in lines:
            if not line.startswith('*'):
                continue
	    response.extend(get_article_titles(line))
    return response

    """
    For now, we just need the article title
    event = {
    'text' : get_plain_text(line),
    'links' : get_links(line),
    'externallinks' : get_externallinks(line),
    'revid' : text_raw['revid']
    }
    response.append(event)
    """
