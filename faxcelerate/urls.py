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

from django.conf.urls.defaults import *
from django.shortcuts import redirect
from django.contrib import admin
from fax import admin as fax_admin
from faxcelerate.settings import ADMIN_MEDIA_PREFIX
import faxcelerate.fax
import faxcelerate.settings as fax_settings
import os.path

try:
    from faxcelerate.settings import URL_PREFIX
    prefix = URL_PREFIX
except ImportError:
    prefix = ''

urlpatterns = patterns(prefix,
    # Example:
    #(r'^faxcelerate/', include('faxcelerate.foo.urls')),
    (r'^fax/', include('faxcelerate.fax.urls')),

    # Uncomment this for admin:

(r'^admin/', include(admin.site.urls)),
(r'^grappelli/', include('grappelli.urls')),
(r'^' + fax_settings.FAX_MEDIA_PREFIX.lstrip('/') + '(?P<path>.*)$',
	'django.views.static.serve',
	{'document_root': os.path.dirname(faxcelerate.fax.__file__) + '/support'  }),
(r'^$', lambda r: redirect('/admin/fax/fax/'), {}),	

)
