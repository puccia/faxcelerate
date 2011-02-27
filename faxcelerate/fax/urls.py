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

from django.conf.urls.defaults import *

from faxcelerate.fax.models import Fax
from faxcelerate.fax.views import *

urlpatterns = patterns('',
	(r'^png/(?P<commid>\d+)/(?P<page>\d+)/$',
		png, {}, 'fax-png'),
	(r'^(?P<filetype>pdf|tiff)/(?P<commid>\d+)/$', serve_file, {}, 'fax-serve'),
	(r'^delete/(?P<commid>\d+)/$', delete, {}, 'fax-delete'),
	(r'^undelete/(?P<commid>\d+)/$', undelete, {}, 'fax-undelete'),
	(r'^print/(?P<commid>\d+)/(?P<printer>[A-Za-z_\d]+)/$', print_fax, {}, 'fax-print'),
	(r'^rotate/', rotate, {}, 'fax-rotate'),
	(r'^view/(?P<object_id>\d+)/$',
		fax_detail, 
		{ 'queryset': Fax.objects,
                 'slug_field': 'comm_id',
                 'extra_context': width_calculation()}, 'fax-view'),
	(r'^bind_(?P<metadata_item>\w+)/(?P<commid>\d+)/$', bind, {}, 'fax-bind'),
        
        # Fax send page
        (r'^send/$', fax_send, {}, 'fax-send'),
)