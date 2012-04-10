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

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from faxcelerate.fax.models import *

from django.core.exceptions import PermissionDenied

class FaxAdmin(admin.ModelAdmin):
    #list_filter = ['outbound', 'received_on', 'expiry', 'sender', 'in_folders']
    list_filter = ['outbound', 'received_on',  'in_folders', 'status']
    list_display = ('short_id', 'device_friendly_name', 'inout', 'status',
        'sender_field', 'sender_ident', 'received_on', 'folder_list',
        'admin_notes', 'admin_thumbs')
    list_per_page = 10
    date_hierarchy = 'received_on'
    fieldsets = (
        ('Metadata', {
            'fields': ('expiry', 'sender', 'in_folders', 'notes')
        }),
    )
    js = (
        '/support/js/jquery.js',
        '/support/js/hovertip.js',
        '/support/js/init.js'
        )
    save_on_top = True
    search_fields = ['station_id', 'caller_id', 'sender__label', 'notes']

    def lookup_allowed(self, key, value):
        lookups = ['in_folders', 'deleted']
        for l in lookups:
            if key.startswith(l):
                return True
        return super(FaxAdmin, self).lookup_allowed(key, value)

    def changelist_view(self, request, extra_context=None):
        if 'deleted' in request.GET and request.GET['deleted']:
            if not extra_context:
                extra_context = {}
            extra_context.update({'deleted': True})
        return super(FaxAdmin, self).changelist_view(request, extra_context)

    def change_view(self, request, object_id, extra_content=None):
        if not request.user.is_superuser:
            raise PermissionDenied
        import django.contrib.admin.views.main
        from django.http import HttpResponse
        r = super(FaxAdmin, self).change_view(request, object_id, extra_content)
        if request.method == 'POST':
            Fax.objects.get(pk=object_id).fix_folders()
        if r.status_code == 302:
            return HttpResponse('<script>window.opener.location.href = window.opener.location.href; window.close();</script>')
        return r

class PhonebookAdmin(admin.ModelAdmin):
    list_display = ('subject', 'number')

class FaxcelerateAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        if not extra_context:
            extra_context = {}
        extra_context.update({'title': _('Main dashboard')})
        return super(FaxcelerateAdminSite, self).index(request, extra_context)

admin.site = FaxcelerateAdminSite()

admin.site.register(Folder)
admin.site.register(Fax, FaxAdmin)
admin.site.register(Sender)
admin.site.register(SenderCID)
admin.site.register(SenderStationID)
admin.site.register(FolderACL)
admin.site.register(PhonebookEntry, PhonebookAdmin)

from django.contrib.auth import admin
