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

from sys import argv
import tempfile
import subprocess
import os
from cStringIO import StringIO

try:
    from PIL import Image
except ImportError:
    import Image
try:
    from PIL.ImageOps import grayscale
except ImportError:
    from ImageOps import grayscale

from faxcelerate import settings

def has_opened_file(func):
    """
    This is a class method decorator. It ensures that the "image" attribute
    exists in the called instance. If it does not, this decorator invokes
    the "tiffcp" command to uncompress the TIFF file and make it
    palatable to PIL.
    """
    def wrapper(self, *args, **kwargs):
        if self.image is None:
            try:
                (handle, self.tempname) = tempfile.mkstemp(".tif")
                os.system("tiffcp -c none %s %s" %
                    (self.tiff_filename, self.tempname))
                self.image = Image.open(self.tempname, "r")
                os.close(handle)
            except IOError, e:
                #raise Exception("Original image not found: %s. Commid: %s, original: %s, tempname: %s" % (e, self.commid, self.tiff_filename, self.tempname))
                self.damaged = True
        return func(self, *args, **kwargs)
    return wrapper
        
class PageUtilities(object):
    def __init__(self, image):
        self.image = image
        
    def ratio(self):
        "Computes the aspect ratio for this image."
        try:
            dpi = self.image.info['dpi']
        except KeyError:
            dpi = (200, 100)
        i = self.image
        return i.size[1]*dpi[0]*1.0/i.size[0]/dpi[1]
        
    def newsize(self, *args, **kwargs):
        "Computes the new width and height for a scaled image."
        # 'i' is a shorthand
        i = self.image
        try:
            for k in args[0].keys():
                kwargs[k] = args[0][k]
        except IndexError:
            pass
        sizes = 0
        for possible_size in ('height', 'width'):
            if possible_size in kwargs:
                sizes += 1
        if sizes != 1:
            raise Exception, 'One, and only one, of width and height must' \
                ' be specified'
        # Compute ratio
        ratio = self.ratio()
        # Take the rotation into account, if any
        try:
            if kwargs['rotation'] in ('r', 'l'): ratio = 1/ratio
        except KeyError:
            pass
        if 'height' in kwargs:
            # Called with an absolute height
            h = kwargs['height']
            if h > i.size[1]:
                h = i.size[1]
            return (int(h/ratio), h)
        else:
            # Called with an absolute width
            w = kwargs['width']
            if w > i.size[0]:
                w = i.size[0]
            return (w, int(w*ratio))
        # Control will not get here
        assert(False)

class FaxImage(object):
    """
    This class deals with a fax message as a (single- or multi-page) image,
    and not with its metadata.
    """
    def __init__(self, fax):
        import faxcelerate.fax.models
        if isinstance(fax, faxcelerate.fax.models.Fax):
            self.commid = fax.comm_id
            self.total_pages = fax.pages
            self.rotation_defaults = fax.rotation
        else:
            self.commid = fax
            self.total_pages = None
        self.tiff_filename = settings.FAX_NAME_FORMAT % fax.filename
        self.statobj = os.stat(self.tiff_filename)
        self.tempname = None
        self.image = None
        self.damaged = False
        
    def __del__(self):
        "Delete any temporary file before decreasing refcount to 0."
        if self.image:
            del self.image
        if self.tempname is not None:
            os.remove(self.tempname)
        
    @has_opened_file
    def pages(self):
        "Generate each page in the file."
        count = 0
        if self.damaged:
            raise IndexError
        self.image.util = PageUtilities(self.image)
        try:
            while True:
                self.image.seek(count)
                self.image.page_index = count
                count += 1
                self.image.page_number = count
                yield self.image
        except EOFError, e:
            raise IndexError(e)
        
    def page_count(self):
        "Return the total number of pages. If it was not cached, compute it."
        if self.total_pages is not None:
            return self.total_pages
        try:
            p = self.pages()
            while True:
                lastpage = p.next()
        except IndexError:
            self.total_pages = lastpage.page_number
            return self.total_pages
        
    def cache_thumbnails(self):
        """
        Save a thumbnail for each page of this fax message. The size is
        hard-coded in the newsize() call.
        """
        p = self.pages()
        try:
            while True:
                i = p.next()
                ni = grayscale(i).resize(i.util.newsize(height=200), Image.ANTIALIAS)
                ni.save(settings.FAX_CACHE_NAME_FORMAT % (self.commid, 
                    i.page_number), "PNG")
                del ni
        except IndexError:
            pass
            
    def thumbnail_links(self, page=None):
        def full_width():
            from django.conf import settings
            try:
                return settings.FAX_WIDTH
            except AttributeError:
                return 800

        def links_for_page(pagenum):
            return {
                'small': settings.FAX_CACHE_URL_FORMAT % (self.commid, pagenum),
                'big':  '/fax/png/%s/%s/?width=250' % (self.commid, pagenum),
                'full': '/fax/png/%s/%s/?width=%s&r=%s' % (self.commid, pagenum,
                    full_width(), self.rotation_defaults[pagenum]),
                'page': str(pagenum)
            }
        if page:
            return links_for_page(page)
        l = []
        pages= self.page_count()
        if pages > 0:
            for pagenum in range(1,pages+1):
                l.append(links_for_page(pagenum))
        return l
    
    DEGREES = {'n': 0, 'l': 90, 'r': 270, 'p': 180}
    
    def generate_png_stream(self, sizes, rotation=None, page_number=1,
        out_file=None):
        """
        Generate a PNG file for a given page.
        """
        # Skip pages before the desired one
        p = self.pages()
        while True:
            page = p.next()
            if page.page_number == page_number:
                break
        else:
            raise IndexError
        # Check if we must rotate
        if rotation is None:
            try:
                rotation = self.rotation_defaults[page_number]
            except AttributeError:
                pass
        # We have the page in the right format
        ni = page
        # Rotation?
        if rotation:
            ni = ni.rotate(self.DEGREES[rotation])
        # Scaling?
        if sizes:
            sizes['rotation'] = rotation
            ni = grayscale(ni).resize(page.util.newsize(sizes), Image.ANTIALIAS)
        # Save the resulting image
        ni.save(out_file, "PNG")
        del ni
    
    def generate_pdf_stream_inner(self, out_file=None, page_size=None):
        if page_size is None:
            cmdline = ["tiff2pdf", self.tiff_filename] 
        else:
            cmdline = ["tiff2pdf", "-p%s" % page_size, self.tiff_filename]
        converter = subprocess.Popen(cmdline, stdout=out_file)
	converter.wait()

    def generate_pdf_stream(self, out_file=None, page_size=None):
        tmp = tempfile.NamedTemporaryFile()
        self.generate_pdf_stream_inner(tmp, page_size)
        content = file(tmp.name, 'r').read()
        tmp.close()
        out_file.write(content)

    def print_fax(self, printer=None):
        "Print the whole fax message through CUPS."
        tmp = tempfile.NamedTemporaryFile()
        self.generate_pdf_stream_inner(tmp, 'A4')
        cmdline = '/usr/bin/lp -o media=A4 -d %s %s' % (printer, tmp.name)
        os.system(cmdline)
        tmp.close()

    def generate_tiff_stream(self, out_file=None):
        orig = open(self.tiff_filename, "rb")
        for line in orig:
            out_file.write(line)
    

# test
if __name__ == '__main__':
    f = FaxImage(argv[1])
    s = f.generate_pdf_stream()
    import sys
    sys.stdout.write(s.read())
    
