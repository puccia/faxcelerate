from django.contrib import admin
from faxcelerate.fax.models import *

from django.core.exceptions import PermissionDenied

class FaxAdmin(admin.ModelAdmin):
    #list_filter = ['outbound', 'received_on', 'expiry', 'sender', 'in_folders']
    list_filter = ['outbound', 'received_on',  'in_folders']
    list_display = ('short_id', 'inout', 'sender_field', 'sender_ident',
        'received_on', 'folder_list', 'admin_notes', 'admin_thumbs')
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
    search_fields = ['station_id', 'caller_id', 'notes']

    def lookup_allowed(self, key):
        lookups = ['in_folders']
        for l in lookups:
            if key.startswith(l):
                return True
        return super(FaxAdmin, self).lookup_allowed(key)

    def queryset(self, request):
        if 'deleted' in request.GET and request.GET['deleted']:
            parms = {'deleted__exact': True}
        else:
            parms = {'deleted__exact': False}
        
        # Post-process __isnull parts
        new_qd = request.GET.copy()
        for k, v in new_qd.items():
            if k.endswith('__isnull'):
                del new_qd[k]
                if v == 'True' or v == '1':
                    parms[str(k)] = True
                else:
                    parms[str(k)] = False
        request.GET = new_qd
        base_qs = super(FaxAdmin, self).queryset(request)
        return Fax.objects.filter_queryset_for_user(base_qs, request.user)
    
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

admin.site.register(Folder)
admin.site.register(Fax, FaxAdmin)
admin.site.register(Sender)
admin.site.register(SenderCID)
admin.site.register(SenderStationID)
admin.site.register(FolderACL)
admin.site.register(PhonebookEntry, PhonebookAdmin)
from django.contrib.auth import admin as auth_admin
#admin.site.register(auth_admin.User, auth_admin.UserAdmin)

