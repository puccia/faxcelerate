#!/usr/bin/env python

# Copyright 2007-2012 C.O.R.P. s.n.c.
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
__copyright__		= "Copyright 2007-2012, C.O.R.P. s.n.c"
__license__ 		= "GNU Affero GPL v. 3.0"
__contact__			= "faxcelerate@corp.it"

import os, sys
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

TIFF_OUTPUT_DIR = os.path.join(settings.FAX_SPOOL_DIR, 'senttiff')

if __name__ == '__main__':
    qfile, why = sys.argv[1:3]
    print qfile, why

    # Scan qfile for info
    info = {}
    for line in open(os.path.join(settings.FAX_SPOOL_DIR, qfile), 'r'):
        tag, data = line.split(':', 1)
	data = data.strip()
        if tag[0] == '!':
            if not tag in info:
                info[tag] = []
            info[tag].append(data)
        else:
            info[tag] = data
    print info

    try:
        fax = Fax.objects.get(comm_id=info['commid'])
    except Fax.DoesNotExist:
        fax = Fax()
    
    error_message = None
    if why != 'done' or int(info['state']) == 9:
        try:
            error_message = '%s: %s' % (why, info['status'])
        except KeyError:
            error_message = why
        fax.status = 2
    else:
        fax.status = 1
    print 'OK'

    # Continue if fax is done or aborted due to an error
    if why in ('blocked', 'requeued'):
        fax.status = 0
        fax.save()
        sys.exit(1)

    fax.comm_id = info['commid']
    fax.local_sender = '%s@%s' % (info['mailaddr'], info['client'])
    fax.received_on = datetime.fromtimestamp(float(info['tts']))
    fax.outbound = True
    fax.caller_id = info['number']
    if error_message:
        fax.reason = error_message
    # Exit if job is not done
    if int(info['state']) < 7:
        fax.save()
        sys.exit(1)

    # List files
    input_files = []
    for tag in ('postscript', 'pdf', '!postscript', '!pdf'):
        if tag in info:
            input_files += [os.path.join(settings.FAX_SPOOL_DIR, 
                name.split(':')[-1]) for name in info[tag]]

    # Build TIFF file
    output_file = '%s.tif' % os.path.join(TIFF_OUTPUT_DIR, info['commid'])
    os.system('gs -dBATCH -dNOPAUSE -q -sDEVICE=tiffg3 -sOutputFile=%s %s -r200'
        % (output_file, ' '.join(input_files)))
    
    # Store in DB
    fax.filename = 'senttiff/%s.tif' % info['commid']
    fax.time_to_receive = 1
    fax.update_from_tiff()
    fax.save()
    from faxcelerate.fax.image import FaxImage
    FaxImage(fax).cache_thumbnails()
	
    
