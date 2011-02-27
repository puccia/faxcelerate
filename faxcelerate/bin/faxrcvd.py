#!/usr/bin/env python

# Copyright 2007-2011 C.O.R.P. s.n.c.
#
# This file is part of Faxcelerate.
# Faxcelerate is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU Affero General Public
# License, as published by the Free Software Foundation.
#
# Faxcelerate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with Faxcelerate.  If not, see
# <http://www.gnu.org/licenses/>.

__author__			= "Emanuele Pucciarelli"
__organization__	= "C.O.R.P. s.n.c"
__copyright__		= "Copyright 2007-2011, C.O.R.P. s.n.c"
__license__ 		= "GNU Affero GPL v. 3.0"
__contact__			= "faxcelerate@corp.it"

from sys import argv
import os, re
import logging
from datetime import datetime

def set_environment():
	import os, sys
	sys.path.append(os.path.dirname(__file__) + '/../..')
	dsm = 'DJANGO_SETTINGS_MODULE'
	if dsm not in os.environ.keys():
		os.environ[dsm] = 'faxcelerate.settings'

set_environment()

from faxcelerate import settings
from faxcelerate.fax.models import Fax
from faxcelerate.fax.image import FaxImage

def setup_logging():
	import logging
	try:
		loglevel = settings.loglevel
	except AttributeError:
		loglevel = logging.INFO
	logging.basicConfig(level=loglevel)
	import logging.handlers
	syslog = logging.handlers.SysLogHandler(address='/dev/log')
	logging.getLogger('').addHandler(syslog)

def receive_fax():
	(scriptname, filename, device, commid, reason, id, mystery2, msn) = [arg.rstrip() for arg in argv]
	logging.info('Processing received fax %s' % commid)
	logging.debug('Fax %s in file %s, received on device %s MSN %s, '
		'reason "%s", id %s' % (commid, filename, device, msn, reason, id))
	fullfname = settings.FAX_SPOOL_DIR + '/%s' % filename
	fax = Fax()
	fax.received_on = datetime.fromtimestamp(os.path.getmtime(fullfname))
	fax.filename = filename
	fax.comm_id = commid
	fax.msn = msn
	fax.station_id = id
	fax.reason = reason
	try:
		fax.update_from_tiff()
	except ValueError, e:
		if not fax.reason == "":
			# There was an error
			fax.error = True
			logging.info("Fax %s has an error; reason: %s" % fax.reason)
		else:
			raise e
	fax.update_from_logfile()
	if fax.station_id == fax.callerid or fax.station_id == '-':
		fax.station_id = None
	fax.set_sender()
	fax.save()
	FaxImage(fax).cache_thumbnails()
	

if __name__ == '__main__':
	setup_logging()
	try:
		receive_fax()
	except Exception, e:
		logging.error(e)
		raise

