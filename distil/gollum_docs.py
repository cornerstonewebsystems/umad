import os
# Fuck urllib2, that's effort. You may need to `pip install requests`.
# http://docs.python-requests.org/en/latest/index.html
import requests
# lxml to parse the HTML and grab the title
from lxml import html

# Plaintext-ify all the junk we get
import html2text

JUNK_CONTENT = []
JUNK_CONTENT.append('  * Search\n\n  * Home\n  * All\n  * Files\n  * New\n  * Upload\n  * Rename\n  * Edit\n  * History')
JUNK_CONTENT.append('  * Search\n\n  * Home\n  * All\n  * New\n  * Upload\n  * Rename\n  * Edit\n  * History') # womble stole the precious thing (Files)


class FailedToRetrievePage(Exception): pass

def blobify(url):
	MAPWIKI_USER = os.environ.get('MAPWIKI_USER', '')
	MAPWIKI_PASS = os.environ.get('MAPWIKI_PASS', '')

	response = requests.get(url, auth=(MAPWIKI_USER, MAPWIKI_PASS))
	try:
		response.raise_for_status()
	except:
		raise FailedToRetrievePage("Error getting page from map wiki, got HTTP response {0} with error: {1}".format(response.status_code, response.reason) )


	# An example URL:  https://docs.anchor.net.au/system/anchor-wikis/Namespaces
	#
	# url      = https://docs.anchor.net.au/system/anchor-wikis/Namespaces
	# local_id = system/anchor-wikis/Namespaces
	# docs     = system/anchor-wikis/Namespaces
	# title    = Fetch from   <!-- --- title: THIS IS THE TITLE -->

	doc_tree = html.fromstring(response.text)
	content = html2text.html2text(response.text)
	# We could probably do this with lxml and some XPath, but meh
	for JUNK in JUNK_CONTENT:
		content = content.replace(JUNK, '')

	# XXX: We're assuming here that all pages across all wikis are in a single index and namespace
	# XXX: What if the page is empty? Might break a whole bunch of assumptions below this point.

	# Get the page name 
	page_name = url.replace('https://docs.anchor.net.au/', '')

	# Get the content
	page_lines = [ line.strip() for line in content.split('\n') ]

	# Kill empty lines and clean out footer
	page_lines = [ line for line in page_lines if line ]
	if page_lines[-1] == 'Delete this Page': del(page_lines[-1])
	if page_lines[-1].startswith('Last edited by '): del(page_lines[-1])
	# Kill residue from conversion
	page_lines = [ line for line in page_lines if line != '!toc' ]

	# Local identifier will be the URL path components
	# Foo/Bar/Baz-is-da-best  =>  Foo Bar Baz is da best
	local_id = page_name.replace('/', ' ').replace('-', ' ')

	# Pull the title from the HTML
	title_list = doc_tree.xpath('//title/text()')
	if title_list:
		title = title_list[0]
		# Slashes in titles aren't very useful, we'll break on spaces instead later
		title = title.replace('/', ' / ')
		# If we have a real document title, roll it into the local_id for searchability goodness
		local_id += " " + ' '.join(title.split())
	else:
		title = local_id


	# If we get this title, it means that the page doesn't exist, it was probably deleted.
	# XXX: Just bail out for now, but the correct action is to probably nuke the index entry.
	if title == 'Create a new page':
		return

	# The homepage of each repo is called Home, let's have something slightly more useful
	if title == 'Home':
		title = local_id

	# Content is now considered tidy
	blob = '\n'.join([title]+page_lines)

	# Try and find an exciting excerpt, this is complete and utter guesswork
	excerpt = '\n'.join(page_lines[:10])

	# Good to go now
	document = {}
	document['url']  = url
	document['blob'] = blob
	document['local_id'] = local_id
	document['title']    = title
	document['excerpt']  = excerpt

	for key in document:
		print u"{0}\n\t{1}\n".format(key, document[key][:400]).encode('utf8')


	yield document
