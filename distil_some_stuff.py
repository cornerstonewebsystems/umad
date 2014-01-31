import sys
import os
from optparse import OptionParser
from colorama import init as init_colorama
from termcolor import colored

import distil
from elasticsearch_backend import *


DEBUG = True
def debug(msg):
	if DEBUG:
		print msg
		#sys.stderr.write(msg.encode('utf8'))
		#sys.stderr.write('\n')
		#sys.stderr.flush()

def red(msg):
	return colored(msg, 'red')
def green(msg):
	return colored(msg, 'green')


def main(argv=None):
	init_colorama()
	global DEBUG

	if argv is None:
		argv = sys.argv

	parser = OptionParser()
	parser.set_defaults(action=None)
	parser.add_option("--quiet", "-q", dest="debug", action="store_false", default=True, help="Suppress nice human-readable reporting")
	(options, urls) = parser.parse_args(args=argv)

	DEBUG = options.debug

	urls[:1] = []
	debug("Your input files are: ")
	for url in urls:
		debug("\t%s" % url)


	for url in urls:
		if url.startswith('/') and os.path.exists(url):
			url = 'file://' + url
		debug(colored("-" * len("URL: %s"%url), 'red'))
		debug(colored("URL: %s" % url, 'red'))
		debug(colored("-" * len("URL: %s"%url), 'red'))

		try:
			d = distil.Distiller(url)
		except distil.NoUrlHandler:
			print "Don't know how to handle URL: %s" % url
			continue

		for doc in d.docs:
			if doc is None:
				continue
			debug(colored("Adding to index: %(url)s" % doc, 'green'))
			# XXX: I think, depending on the backend, the blob will be
			# either str or unicode. We'll need to test for that, otherwise
			# we'll cause errors needlessly.
			# RT==str, Gollum==unicode, Map and Provsys==??
			debug(colored(u"400 chars of blob: {0}".format(doc['blob'][:400]), 'blue')) # XXX: this line has problems with unicode
			add_to_index(doc['url'], doc)
			debug(colored("Success!", 'green'))
			debug("")

			debug(red("-------"))
			debug(red("Now reprinting the document we just indexed"))
			document_just_added = get_from_index(doc['url'])['_source']
			for key in sorted(document_just_added):
				if not isinstance(document_just_added[key], (str,unicode)):
					document_just_added[key] = str(document_just_added[key])
				debug(green(key.capitalize()))
				debug(u"\t{0}".format(document_just_added[key][:1000]).encode('utf8'))
			debug("")


	return 0


if __name__ == "__main__":
	sys.exit(main())

