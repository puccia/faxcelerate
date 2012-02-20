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

# -*- coding: utf-8 -*-

# Create your views here.

from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import user_passes_test, permission_required

from image import FaxImage
from faxcelerate.fax.models import Fax, SenderCID, SenderStationID
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotModified, Http404
from django.shortcuts import render_to_response
import stat
import rfc822

class WasModified(Exception):
    """
    This exception is triggered when the code detects that an object
    to be served was modified after the date in the conditional GET
    request.
    """
    pass
    
def not_modified(request, img):
    """
    (Code stolen from the static file view.)
    """
    from django.views.static import was_modified_since
    if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
        img.statobj[stat.ST_MTIME], 0):
            return HttpResponseNotModified()
    raise WasModified()


def based_on_fax_image(func):
    """
    Create a fax image object, and return 304 if we can.
    """
    def wrapper(request, commid=None, *args, **kwargs):
        # Get the fax image object; return 404 if not found
        try:
            img = FaxImage(Fax.objects.visible_to_user(request.user
                ).get(pk=commid))
        except Fax.DoesNotExist:
            raise Http404
        # Try to satisfy conditional GET
        from django.views.static import was_modified_since
        if not was_modified_since(request.META.get('HTTP_IF_MODIFIED_SINCE'),
            img.statobj[stat.ST_MTIME], 0):
                return HttpResponseNotModified()
        # No, we have to send the full response
        response = func(request, commid=commid, img=img, *args, **kwargs)
        response["Last-Modified"] = rfc822.formatdate(img.statobj[stat.ST_MTIME])
        return response
    return wrapper
        
@based_on_fax_image
def png(request, commid=None, page=None, img=None):
    """
    Generates a PNG response, based on the required fax and the optional size arguments.
    """
    stream_args = {} #: the size arguments for the stream
    # Ignore parameters other than 'height' and 'width'
    for k in ('height', 'width'):
        try:
            stream_args[k] = int(request.REQUEST[k])
        except KeyError:
            pass
    try:
        rotation = request.REQUEST['r']
    except KeyError:
        rotation = None
    response = HttpResponse(mimetype='image/png')
    img.generate_png_stream(stream_args, rotation=rotation,
        page_number=int(page), out_file=response)   
    return response

@based_on_fax_image
def serve_file(request, filetype, commid=None, img=None):
    if filetype == 'pdf':
        mimetype = 'application/pdf'
        filename = 'fax_%s.pdf'
        generator = 'generate_pdf_stream'
    elif filetype == 'tiff':
        mimetype = 'image/tiff'
        filename = 'fax_%s.tif'
        generator = 'generate_tiff_stream'
    else:
        raise TypeError('Unknown filetype: %s' % filetype)
    fax = Fax.objects.visible_to_user(request.user).get(pk=commid)
    response = HttpResponse(mimetype=mimetype)
    getattr(img, generator)(out_file=response)
    response['Content-Disposition'] = 'attachment; filename=' + filename % fax.short_id();
    response["Last-Modified"] = rfc822.formatdate(img.statobj[stat.ST_MTIME])
    return response
    
@user_passes_test(lambda u: u.is_superuser)
def bind(request, commid=None, metadata_item=None):
    if metadata_item == 'cid':
        table = SenderCID
        field = 'caller_id'
        human_descr = _('The calling number')
    elif metadata_item == 'tsi':
        table = SenderStationID
        field = 'station_id'
        human_descr = _('The calling station ID')
    else:
        raise Http404
    fax = Fax.objects.get(pk=commid)
    test = getattr(fax, field + '_storable')
    if not test():
        raise Exception('Invalid operation')
    new_item = table()
    setattr(new_item, field, getattr(fax, field))
    new_item.sender = fax.sender
    new_item.save()
    my_filter = { field + '__exact': getattr(fax, field)}
    modifiable_faxes = Fax.objects.filter(**my_filter)
    modifiable_faxes = modifiable_faxes.filter(sender__isnull=True)
    for f in modifiable_faxes:
        f.sender = fax.sender
        f.save()
    msg = _('%s was learned.') % human_descr
    if modifiable_faxes:
        msg += _(' The correct sender was set in %s more fax messages.') % len(modifiable_faxes)
    request.user.message_set.create(message=msg)
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def check_deleted(request):
    try:
        if request.GET['deleted__exact'] == '1':
            return { 'deleted': True }
    except KeyError:
        pass
    return {}
    
def width_calculation():
    ICON_WIDTH = 32
    from django.conf import settings
    return { 'faxwidth': settings.FAX_WIDTH,
        'faxpagewidth': settings.FAX_WIDTH + ICON_WIDTH + 30,
        }

def delete(request, commid=None):
    # DO NOT use the delete() method!
    fax = Fax.objects.visible_to_user(request.user).get(comm_id=commid)
    fax.deleted = True
    fax.save()
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def undelete(request, commid=None):
    # DO NOT use the delete() method!
    fax = Fax.objects.visible_to_user(request.user).get(comm_id=commid)
    fax.deleted = False
    fax.save()
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def print_fax(request, commid=None, printer=None):
    from faxcelerate import settings
    if printer is None:
        printer = settings.PRINTERS[0]
    FaxImage(Fax.objects.visible_to_user(request.user
        ).get(comm_id=commid)).print_fax(printer)
    request.user.message_set.create(message=_('The fax was queued for printing.'))
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def rotate(request):
    commid = request.REQUEST['commid']
    page = int(request.REQUEST['page'])
    rtype = request.REQUEST['type']
    fax = Fax.objects.visible_to_user(request.user).get(comm_id=commid)
    fax.rotation.rotate(rtype, page)
    fax.save()
    from django.utils import simplejson
    return HttpResponse(
        simplejson.dumps({'newsrc':
            fax.related_image().thumbnail_links(page)['full']}),
        mimetype='application/json')

def fax_detail(request, *args, **kwargs):
    from django.views.generic.list_detail import object_detail
    # Tune queryset
    from fax.models import FaxManager
    kwargs['queryset'] = Fax.objects.filter_queryset_for_user(
        kwargs['queryset'], request.user)
    return object_detail(request, *args, **kwargs)

def fax_send(request):
    """
    Display a web page to send a new fax, or perform the action.
    """
    from django.contrib import admin
    if not request.user.has_perm('fax.can_send'):
        return admin.site.login(request)
    
    from django import forms
    from fax.models import PhonebookEntry

    def make_context(pbform, sfform, context={}):
        context.update({
            'form': sfform,
            'phonebook': pbform,
            'adminform': {'model_admin': None},
        })
        from django.template import RequestContext
        return RequestContext(request, context)

    class SendFaxForm(forms.Form):
        file = forms.FileField()
        numberlist = forms.CharField(required=False, widget=forms.HiddenInput)

    class PhonebookForm(forms.Form):
        phonebook = forms.MultipleChoiceField(choices=[(x.number, unicode(x))
            for x in PhonebookEntry.objects.all()])

    pbform = PhonebookForm()
    server_response = None
    if request.method == 'GET':
        form = SendFaxForm()
        context = make_context(pbform, form)
        return render_to_response('fax/fax_send.html', context)
    elif request.method == 'POST':
        form = SendFaxForm(request.POST, request.FILES)
        if form.is_valid():
            dest_numbers = form.cleaned_data['numberlist'].split('~')
            # Prepare command
            command = ['/usr/bin/sendfax', '-s', 'A4', '-R', '-n']
            for number in dest_numbers:
                command += ['-d', number]
            import subprocess
            sendfax = subprocess.Popen(command, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            # We have a single file
            out, err = sendfax.communicate(request.FILES['file'].read())
            server_response = '\n'.join([out, err])
        return render_to_response('fax/fax_send.html', make_context(
                pbform, form, context={'server_response': server_response}))
        # Remove when done
        raise Exception('Not yet implemented')

    else:
        raise Exception
    
