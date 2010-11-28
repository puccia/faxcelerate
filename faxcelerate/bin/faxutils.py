#!/usr/bin/python

import re


def set_environment():
	import os, sys
	sys.path.append(os.path.dirname(__file__) + '/../..')
	dsm = 'DJANGO_SETTINGS_MODULE'
	if dsm not in os.environ.keys():
		os.environ[dsm] = 'faxcelerate.settings'

set_environment()

from faxcelerate import settings

class SentFaxError(Exception):
	pass

LOGLINE = re.compile('(?P<month>\d\d)/(?P<day>\d\d)/(?P<year>\d\d) '
	+'(?P<hour>\d\d):(?P<minute>\d\d)\t'
	+ 'RECV\t'
	+'(?P<commid>\d+)\t'
	+'(?P<device>\S+)\t'
	+'([^\t]*)\t'
	+'([^\t]*)\t'
	+'fax\t'
	+'(?P<msn>[^\t]+)\t'
	+'(?P<tsi>[^\t]+)\t'
	+'(?P<params>\d+)\t'
	+'(?P<pages>\d+)\t'
	+'(?P<jobmin>\d+):(?P<jobsec>\d+)\t'
	+'(?P<connmin>\d+):(?P<connsec>\d+)\t'
	+'(?P<reason>[^\t]+)')

CALL_LINE = re.compile(': Incoming (?P<calltype>\w+) call on controller (?P<ctrl>\d+) (from (?P<callerid>\d+))?')
WRITE_LINE = re.compile(': Write fax in path .* to file (?P<filename>.+)\.$')

def update_from_logfile(metadata, commid=None):
	if commid is None:
		commid = metadata['commid']
	log = open(settings.COMM_LOG_FORMAT % commid, "r")
	for line in log:
		print line
		for regex in (CALL_LINE, WRITE_LINE):
			try:
				g = regex.search(line).groupdict()
			except AttributeError:
				continue
			print "found keys: %s" % g.keys()
			for key in g.keys():
				metadata[key] = g[key]

def faxdata(line):
	try:
		m = LOGLINE.match(line.rstrip()).groupdict()
	except AttributeError:
		raise SentFaxError
	metadata = {}
	# date
	from datetime import datetime
	metadata['date'] = datetime(int(m['year'])+2000, int(m['month']),
		int(m['day']), int(m['hour']), int(m['minute']))
	metadata['jobduration'] = int(m['jobsec']) + int(m['jobmin'])*60
	metadata['connduration'] = int(m['connsec']) + int(m['connmin'])*60
	for key in ('msn', 'tsi', 'reason'):
		metadata[key] = m[key].strip('"').rstrip()
	for key in ('params', 'pages'):
		metadata[key] = int(m[key])
	for key in ('commid', 'device'):
		metadata[key] = m[key]
	update_from_logfile(metadata)
	try:
		if metadata['callerid'] == metadata['tsi']:
			del metadata['tsi']
	except KeyError:
		pass
	try:
		if metadata['tsi'] == '-':
			del metadata['tsi']
	except KeyError:
		pass
	
	return metadata
	
def create_fax_entry(metadata):
	from faxcelerate.fax.models import Fax
	def m(key):
		try:
			return metadata[key]
		except KeyError:
			return None
	f = Fax()
	f.comm_id = m('commid')
	f.station_id = m('tsi')
	f.msn = m('msn')
	f.received_on = m('date')
	f.time_to_receive = m('jobduration')
	f.conn_duration = m('connduration')
	f.pages = m('pages')
	f.params = m('params')
	f.reason = m('reason')
	f.filename = m('filename')
	f.caller_id = m('callerid')
	f.save()
	return f

if __name__ == '__main__':
	# Paths
	set_environment()
	# Options
	from optparse import OptionParser
	parser = OptionParser()
	parser.set_defaults(thumbnails=False)
	parser.add_option("-p", "--process-log", dest="logname",
		help="process each line in LOGFILE", metavar="LOGFILE")
	parser.add_option("-t", "--create-thumbnails", action="store_true",
		dest="thumbnails", help="create thumbnails")
	(options, args) = parser.parse_args()
	# Actual work
	if options.logname:
		# Process a logfile
		log = open(options.logname, "r")
		for line in log:
			try:
				fax = create_fax_entry(faxdata(line))
			except SentFaxError:
				continue
			fax.set_sender()
			fax.save()
	if options.thumbnails:
		# Create or recreate all thumbnails
		from faxcelerate.fax import image
		from faxcelerate.fax.models import Fax
		for fax in Fax.objects.all():
			f = image.FaxImage(fax)
			f.cache_thumbnails()
