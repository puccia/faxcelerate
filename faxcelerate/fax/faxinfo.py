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

import os

from django.utils.safestring import SafeString, EscapeUnicode

import models
from faxcelerate import settings



class DataStore(object):
    """
    Keeps info on a fax message.  Reads it from a fax file (via the 'faxinfo'
    HylaFAX utility) and makes it available to other classes.
    """
    def __init__(self, faxinfo):
        "Needs a FaxInfo object for initialization."
        self._store = None
        self.faxinfo = faxinfo
    def __setitem__(self, key, val):
        self._store[key] = val
    def __getitem__(self, key):
        "Reads the data via faxinfo if needed, so that it can be cached."
        if self._store is None:
            self.read_data()
        return self._store[key]
    def read_data(self):
        "Initialize an empty hash and call faxinfo."
        self._store= {}
        command ='%s -r %s' % (settings.FAXINFO, self.faxinfo.path)
        info = os.popen(command)
        for key in ('tsi', 'pages', 'resolution', 'paper', 'date', 'jobtime', 'bitrate', 'mode', 'ecm'):
            self[key] = info.readline().rstrip()


class FaxInfo(object):
    "Manages metadata about a fax message."
    def __init__(self, fax):
        "Needs either a string or a fax object."
        if isinstance(fax, basestring):
            filename = fax
        elif isinstance(fax, models.Fax):
            filename = fax.filename
        else:
            raise TypeError("%s is not a fax" % fax)
        self.path = settings.FAX_SPOOL_DIR + '/' + filename
        self.data = DataStore(self)
            
    def html_summary(self):
        """
        Prepare a short summary of relevant fax details.
        
        Note that keywords are marked as no-op first, to ease detection 
        by make-messages.py; later they are translated.
        """
        from django.utils.translation import gettext_noop as _
        from django.utils.translation import gettext_lazy as __
        return SafeString('\n'.join(
            ['<dt>%s</dt> <dd>%s</dd>' % (
                EscapeUnicode(__(k).capitalize()),
                EscapeUnicode(self.data[k]))
                for k in (_('resolution'), _('paper'), _('bitrate'),
                    _('mode'), _('ecm')
                )
            ]
        ))
