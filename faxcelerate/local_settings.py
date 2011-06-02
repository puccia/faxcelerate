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

DEBUG = True

# Configure the database name and engine as you see fit. The default 
# configuration uses PostgreSQL.

DATABASE_NAME = 'faxcelerate2'
DATABASE_ENGINE = 'postgresql_psycopg2'

# This URL prefix will be used to serve fax images.
FAX_MEDIA_PREFIX = '/support/'

# This is the HylaFAX spool directory.
FAX_SPOOL_DIR = '/var/spool/hylafax'

# Usually the formats that refer to HylaFAX files need not be changed.
FAX_NAME_FORMAT = FAX_SPOOL_DIR + '/%s'
COMM_LOG_FORMAT = FAX_SPOOL_DIR + '/log/c%s'

# These are the URL that your web server will map to the cached
# thumbnail files and their actual location in the file system. 
FAX_CACHE_URL_FORMAT = '/cache/thumbnails/%s-%s.png'
FAX_CACHE_NAME_FORMAT = '/tmp/cache/thumbnails/%s-%s.png'

# The path to the "faxinfo" binary that comes with HylaFAX.
FAXINFO = '/usr/sbin/faxinfo'

# Default width for the rendered fax images.
FAX_WIDTH = 720

