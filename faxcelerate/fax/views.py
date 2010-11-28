# -*- coding: utf-8 -*-

# Create your views here.

from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from image import FaxImage
from faxcelerate.fax.models import Fax, SenderCID, SenderStationID
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotModified, Http404
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
            img = FaxImage(Fax.objects.get(pk=commid))
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
    fax = Fax.objects.get(pk=commid)
    response = HttpResponse(mimetype=mimetype)
    getattr(img, generator)(out_file=response)
    response['Content-Disposition'] = 'attachment; filename=' + filename % fax.short_id();
    response["Last-Modified"] = rfc822.formatdate(img.statobj[stat.ST_MTIME])
    return response
    
    
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
    
def width_calculation(request):
    ICON_WIDTH = 32
    from faxcelerate import settings
    return { 'faxwidth': settings.FAX_WIDTH,
        'faxpagewidth': settings.FAX_WIDTH + ICON_WIDTH + 30,
        }

def change_stage(request, *args, **kwargs):
    import django.contrib.admin.views.main
    r = django.contrib.admin.views.main.change_stage(request, *args, **kwargs)
    if request.method == 'POST':
        Fax.objects.get(pk=args[2]).fix_folders()
    if r.status_code == 302:
        return HttpResponse('<script>window.opener.location.href = window.opener.location.href; window.close();</script>')
    return r
    
def delete(request, commid=None):
    # DO NOT use the delete() method!
    fax = Fax.objects.get(comm_id=commid)
    fax.deleted = True
    fax.save()
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def undelete(request, commid=None):
    # DO NOT use the delete() method!
    fax = Fax.objects.get(comm_id=commid)
    fax.deleted = False
    fax.save()
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def print_fax(request, commid=None, printer=None):
    from faxcelerate import settings
    if printer is None:
        printer = settings.PRINTERS[0]
    FaxImage(Fax.objects.get(comm_id=commid)).print_fax(printer)
    request.user.message_set.create(message=_('The fax was queued for printing.'))
    return HttpResponseRedirect(reverse('fax-view', args=(commid,)))

def rotate(request):
    commid = request.REQUEST['commid']
    page = int(request.REQUEST['page'])
    rtype = request.REQUEST['type']
    fax = Fax.objects.get(comm_id=commid)
    fax.rotation.rotate(rtype, page)
    fax.save()
    from django.utils import simplejson
    return HttpResponse(
        simplejson.dumps({'newsrc':
            fax.related_image().thumbnail_links(page)['full']}),
        mimetype='application/json')
