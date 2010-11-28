from django.conf.urls.defaults import *

from django.contrib import admin
from faxcelerate.settings import ADMIN_MEDIA_PREFIX
import faxcelerate.fax
import faxcelerate.fax.admin
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
	#(r'^admin/(fax)/(fax)/(\d+)/', 'faxcelerate.fax.views.change_stage'),
	#(r'^admin/(fax)/(fax)/', 'faxcelerate.fax.views.change_list'),

    # Uncomment this for admin:

(r'^admin/(.*)', admin.site.root),
(r'^cache/thumbnails/(?P<path>.*)$', 'django.views.static.serve',
	{'document_root': '/tmp/cache/thumbnails' }),
(r'^' + fax_settings.FAX_MEDIA_PREFIX.lstrip('/') + '(?P<path>.*)$',
	'django.views.static.serve',
	{'document_root': os.path.dirname(faxcelerate.fax.__file__) + '/support'  }),
	

)
