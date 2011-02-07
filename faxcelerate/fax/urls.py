from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_detail

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
		object_detail, 
		{ 'queryset': Fax.objects,
                 'slug_field': 'comm_id',
                 'extra_context': width_calculation()}, 'fax-view'),
	(r'^bind_(?P<metadata_item>\w+)/(?P<commid>\d+)/$', bind, {}, 'fax-bind'),
)