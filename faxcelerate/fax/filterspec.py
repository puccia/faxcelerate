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

from django.contrib.admin.filterspecs \
    import FilterSpec, RelatedFilterSpec, DateFieldFilterSpec
from django.utils.translation import ugettext_lazy as _

import datetime
    
import models

from django.db import models as django_models

class FolderFilterSpec(RelatedFilterSpec):
    def __init__(self, f, request, params, model, model_admin):
        super(FolderFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.lookup_kwarg2 = '%s__%s__in' % (f.name, f.rel.to._meta.pk.name)
        self.lookup_val2 = request.GET.get(self.lookup_kwarg2, None)
        self.lookup_kwarg3 = '%s__isnull' % (f.name)
        self.lookup_val3 = request.GET.get(self.lookup_kwarg3, None)
        
    def has_output(self):
        return len(self.lookup_choices) > 0

    def choices(self, cl):
        yield {'selected': self.lookup_val is None and self.lookup_val2 is None
                   and self.lookup_val3 is None,
               'query_string': cl.get_query_string({}, [self.lookup_kwarg, self.lookup_kwarg2, self.lookup_kwarg3]),
               'display': _('All')}
        yield {'selected': self.lookup_val3 == 'True',
               'query_string': cl.get_query_string({self.lookup_kwarg3: 'True'}, [self.lookup_kwarg, self.lookup_kwarg2]),
               'display': _('Unfiled'),
              }
        m = [c for c in self.lookup_choices]
        def foldersort(x, y):
            if x == y.parent or x.__str__() < y.__str__():
               return -1
            else:
                return 1
        #m.sort(foldersort)
        m.sort()
        for val in m:
            val = self.field.rel.to.objects.get(pk=val[0])
            pk_val = getattr(val, self.field.rel.to._meta.pk.attname)
            d = {'selected': self.lookup_val == str(pk_val),
                   'query_string': cl.get_query_string(
                        {self.lookup_kwarg: pk_val},
                        [self.lookup_kwarg2, self.lookup_kwarg3]
                        ),
                   'display': val}
            if val.has_children():
                 d = {'selected': self.lookup_val2 == val.subtree(make_string=False),
                    'query_string': cl.get_query_string(
                        {self.lookup_kwarg2: str(val.subtree(make_string=False))},
                        [self.lookup_kwarg, self.lookup_kwarg3]
                        ),
                    'display': val
                    }
            yield d
    

FilterSpec.filter_specs.insert(0, 
    (lambda f: hasattr(f, 'folder_nature'), FolderFilterSpec))

class ExpiryFilterSpec(DateFieldFilterSpec):
    def __init__(self, f, request, params, model, model_admin):
        super(ExpiryFilterSpec, self).__init__(f, request, params, model, model_admin)

        today = datetime.date.today()
        today_str = isinstance(self.field, django_models.DateTimeField) and today.strftime('%Y-%m-%d 23:59:59') or today.strftime('%Y-%m-%d')

        self.links = (
            (_('All'), {}),
            (_('Going to expire'), {'%s__gte' % self.field.name: str(today_str)}),
            (_('Without expiration'), {'%s__isnull' % self.field.name: str(True)}),
            (_('Expired'), {'%s__lt' % self.field.name: str(today_str)}),
        )

    def choices(self, cl):
     return super(ExpiryFilterSpec, self).choices(cl)

FilterSpec.filter_specs.insert(0, (lambda f: hasattr(f, 'expiry_nature'), ExpiryFilterSpec))
