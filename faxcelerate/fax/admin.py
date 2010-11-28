from django.contrib import admin
from faxcelerate.fax.models import *

admin.site.register(Folder)
admin.site.register(Fax, FaxAdmin)
admin.site.register(Sender)
admin.site.register(SenderCID)
admin.site.register(SenderStationID)

from django.contrib.auth import admin as auth_admin
#admin.site.register(auth_admin.User, auth_admin.UserAdmin)

