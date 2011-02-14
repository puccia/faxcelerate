# -*- coding: utf-8 -*-
import os

from django.db import models
from django.template.loader import render_to_string
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _, gettext as __
from django.shortcuts import render_to_response
from django import template

from django.contrib.auth.models import User, Group

from faxcelerate.fax.faxinfo import FaxInfo
from faxcelerate import settings

import filterspec
import image
import extend_cache

class FolderManager(models.Manager):
    def visible_to_user(self, user):
        if user.is_superuser:
            return self.all()
        else:
            return [x for x in self.all() if x.is_allowed(1, user)]

class Folder(models.Model):
    """ This class describes an archival folder.
    """
    
    objects = FolderManager()
    
    label = models.CharField(_('Name'), max_length=40)
    parent = models.ForeignKey('Folder',
        verbose_name=_('inside folder'), blank=True,null=True,
        help_text=_("This folder's parent in the hierarchy. This "
        "folder will be shown as 'under', or 'inside' its parent."))
    order = models.IntegerField(blank=True,null=True,editable=False)

    def is_allowed(self, permission, user):
        if not isinstance(user, User):
            raise TypeError("%s is not a user" % user)
        qs = FolderACL.objects.filter(folder=self,access=permission)
        def check(qs):
            permissions = qs.filter(permit=True)
            if len(permissions) > 0:
                return True
            permissions = qs.filter(permit=False)
            if len(permissions) > 0:
                return False
        r = check(qs.filter(user=user))
        if r is not None:
            return r
        r = check(qs.filter(group__in=user.groups.all()))
        if r is not None:
            return r
        if self.parent is not None:
            return self.parent.is_allowed(permission, user)
        else:
            return False
    
    @classmethod
    def fix_sorting(cls):
        "Fix the 'order' field in all objects and save them."
        rows = [row for row in cls.objects.all()]
        rows.sort(lambda x,y: [+1, -1][x.__str__() < y.__str__()])
        for i in range(len(rows)):
            rows[i].order = i
            super(Folder, rows[i]).save()
            
    def save(self, *args, **kwargs):
        "Automatically re-sort objects."
        super(Folder, self).save(*args, **kwargs)
        for d in self.descendants():
            cache.delete(d.cache_label())
        Folder.fix_sorting()
        
    class Meta:
        ordering = ('order',)
        verbose_name = _('folder')
        verbose_name_plural = _('folders')
    
    def cache_label(self):
        return 'folder__full_label__%s' % self.id
    
    def __str__(self):
        "Pull the name from the cache, or compute it if needed."
        def full_name():
            "Build the name out of the full path to the folder."
            l = self.label
            p = self.parent
            while p is not None:
                l = p.label + u' → ' + l
                p = p.parent
            cache.set(self.cache_label(), l)
            return l
        return cache.lazy_get(self.cache_label(), full_name).encode('utf-8')
        
    def ancestors(self):
        "List the node and all the objects tracing back to the root."
        l = []
        node = self
        while node.parent:
            l.append(node.parent)
            node = node.parent
        return l
    
    def has_children(self):
        """
        Returns true if the folder has any children.
        """
        return Folder.objects.filter(parent__exact=self.id).count()>0
        try:
            o = Folder.objects.get(pk=self.id)
            return True
        except DoesNotExist:
            return False
        
    def subtree(self, make_string=True):
        """
        Returns a list with this folder and all its descendants.
        """
        l = [folder.id for folder in self.descendants()]
        if make_string:
            return ','.join([str(id) for id in l])
        else:
            return l
        
    def descendants(self):
        """
        Finds the children, grandchildren, etc. of this folder.
        
        This might be replaced with a stored procedure in the DB engine.
        """
        desc = []
        queue = [ self ]
        while len(queue) > 0:
            i = queue.pop()
            children = Folder.objects.filter(parent__exact=i.id)
            for x in children:
                if x in desc:
                    raise Exception('Circular parenthood')
                desc.append(x)
                queue.append(x)
        return desc

class FaxManager(models.Manager):
    def filter_queryset_for_user(self, queryset, user):
        if user.is_superuser:
            return self
        
        # Prepare query w/ admissible folders
        from django.db.models import Q
        Q_object = Q()
        visible = Folder.objects.visible_to_user(user)
        for folder in visible:
            Q_object = (Q_object | Q(in_folders=folder))
        return queryset.filter(Q_object).distinct()
        
    def visible_to_user(self, user):
        return self.filter_queryset_for_user(self.get_query_set(), user)

class Fax(models.Model):
    """
    This class describes a single received fax message.
    """
    objects = FaxManager()
    
    comm_id = models.CharField(_('progressive ID'),
        max_length=9,primary_key=True,editable=False)
    station_id = models.CharField(_('Calling station ID'),
        max_length=32,editable=False,null=True)
    caller_id = models.CharField(_('calling number'),
        max_length=32,blank=True,null=True,editable=False)
    msn = models.CharField(_('called number'),
        max_length=32,blank=True,null=True,editable=False)
    filename = models.CharField(_('TIFF file name'),
        max_length=80,editable=False)
    received_on = models.DateTimeField(_('date'),
        editable=False)
    time_to_receive = models.IntegerField(_('time to receive'),
        editable=False)
    conn_duration = models.IntegerField(_('total connection time'),
        editable=False,null=True)
    pages = models.IntegerField(_('pages'),
        editable=False)
    params = models.IntegerField(editable=False,null=True)
    expiry = models.DateField(_('expiration date'),
        blank=True,null=True,
        help_text=_('An expiry date after which the message will no '
        'longer be useful. You can set this for time-limited '
        'promotions you do not want to display after their validity, '
        'or you can leave this blank.')
        )
    expiry.expiry_nature = True
    in_folders = models.ManyToManyField(Folder,
        verbose_name=_('filed in folders'),
        blank=True,null=True,
        help_text=_('A list of folders under which this message will '
        'be found.  You can specify one or more folders, so that the '
        'message will be visible under each of them.')
        )
    in_folders.folder_nature = True
    sender = models.ForeignKey('Sender',
        verbose_name=_('sender'),
        null=True,blank=True,
        help_text=_('The sender of this fax message. Set this to '
        'have it displayed alongside the message, and to enable '
        'automatic identification in the future.')
        )
    reason = models.CharField(_('error reason'),
        max_length=200,blank=True,null=True,editable=False)
    notes = models.TextField(_('Notes'),blank=True,null=True)
    deleted = models.BooleanField(_('Deleted'),
        null=False,default=False)
    _rotation = models.CharField(_('Default rotation'),
        db_column='rotation', null=True, blank=True, max_length=200)
    localsender = models.CharField('local sender', max_length=120, null=True,
        blank=True)
    outbound = models.BooleanField('outbound', default=False)

    class Meta:
        ordering = ('-received_on',)
        verbose_name = _('Fax message')
        verbose_name_plural = _('Fax messages')
        permissions = (
            ('can_send_fax', _('Can send fax messages')),
        )
    
    # Regular expressions for log analysis
    import re
    DURATION = re.compile('(?P<min>\d+):(?P<sec>\d+)')
    CALL_LINE = re.compile(': Incoming (?P<calltype>\w+) call on controller (?P<ctrl>\d+) (from (?P<callerid>\d+))?')
    WRITE_LINE = re.compile(': Write fax in path .* to file (?P<filename>.+)\.$')

    def delete(self):
        self.deleted = True
        self.save()
    
    def tiff_filename(self):
        return settings.FAX_SPOOL_DIR + '/%s' % self.filename
        
    def sender_ident(self):
        if self.station_id:
            if self.station_id != '-':
                return self.station_id
        if self.caller_id:
            return self.caller_id
        return ''
    sender_ident.short_description = _('Station')
    
    def sender_field(self):
        if self.sender:
            return str(self.sender)
        return ''
    sender_field.short_description = _('Sender')
    
    def folder_list(self):
        return ', '.join([ folder.label for folder in self.in_folders.all()])
    folder_list.short_description = _('Filed under')

    def short_id(self):
        return self.comm_id.lstrip('0')
    short_id.short_description = _('Short ID')
        
    def __str__(self):
        n = 'Fax ' + self.short_id()
        if self.deleted: n += __(' (deleted)')
        if self.received_on: n += __(' on %s') % self.received_on
        if self.sender: n += __(' from %s') % self.sender
        return n
    
    def admin_thumbs(self):
        return render_to_string('fax/thumb.html',
            {'images': image.FaxImage(self).thumbnail_links(),
             'commid': self.comm_id,})
    admin_thumbs.allow_tags = True
    admin_thumbs.short_description = _('page thumbnails')
    
    def tools_html(self):
        return render_to_string('fax/fax_tools.html', {'fax': self})
    tools_html.allow_tags = True
    
    def admin_notes(self):
        n = []
        if self.reason:
            n.append("<div class='error-note'>" + self.reason + "</div>")
        if self.notes:
            n.append("<div class='notes'>" + self.notes + "</div>")
        return "".join(n)
    admin_notes.short_description = _('notes')
    admin_notes.allow_tags = True
    
    def set_sender(self):
        if self.sender is None:
            for s in [
                SenderStationID.objects.filter(
                    station_id__exact=self.station_id),
                SenderCID.objects.filter(
                    caller_id__exact=self.caller_id)]:
                if s.count() > 0:
                    self.sender = s[0].sender
                    return
                    
    def caller_id_storable(self):
        return self.sender is not None and SenderCID.objects.filter(
            caller_id__exact=self.caller_id).count() == 0
        
    def station_id_storable(self):
        return self.sender is not None and SenderStationID.objects.filter(
            station_id__exact=self.station_id).count() == 0
        
    def related_image(self):
        return image.FaxImage(self)
        
    class Rotation(object):
        def __init__(self, fax):
            self.fax = fax
            
        def rotation_is_initialized(func):
            def wrapper(self, *args, **kwargs):
                if not self.fax._rotation:
                    self.fax._rotation = 'n'*self.fax.pages
                return func(self, *args, **kwargs)
            return wrapper
        
        @rotation_is_initialized        
        def __setitem__(self, page, r):
            if r not in ('n', 'r', 'l', 'p'):
                raise ValueError("%s is not a valid setting for rotation")
            if page < 1 or page > self.fax.pages:
                raise IndexError("There is no page %s in %s" % (page, self.fax))
            self.fax._rotation = self.fax._rotation[:page-1] + r + self.fax._rotation[page:]
            
        @rotation_is_initialized        
        def __getitem__(self, page):
            try:
                return self.fax._rotation[page-1]
            except IndexError:
                raise IndexError("There is no page %s in %s" % (page, self.fax))
                
        SEQUENCE = "nlpr"
        TYPES = { 'rotate-left': 1, 'rotate-right': -1};
        def rotate(self, rtype, page):
            self[page] = self.SEQUENCE[(self.SEQUENCE.index(self[page])+self.TYPES[rtype])
                % 4]
                    
    def __init__(self, *args, **kwargs):
        # Handlers for the rotation attribute
        
        super(Fax, self).__init__(*args, **kwargs)
        if self.filename:
            self.info = FaxInfo(self)
        self.rotation = self.Rotation(self)
        
    def fix_folders(self):
        folders = self.in_folders.all()
        for folder in folders:
            for ancestor in folder.ancestors():
                if ancestor in folders:
                    self.in_folders.remove(ancestor)
                    
    def available_printers(self):
        return settings.PRINTERS
        
    def update_from_tiff(self):
        info = os.popen('%s -r %s' % (settings.FAXINFO, self.filename))
        n = info.readline().rstrip() # TSI
        n = info.readline().rstrip() # Pages
        self.pages = int(n) # Pages
        info.readline() # Resolution
        info.readline() # Paper
        info.readline() # Date
        try:
            duration = self.DURATION.match(info.readline()).groupdict() # Time to receive
            self.time_to_receive = int(duration['min'])*60 + int(duration['sec'])
        except AttributeError:
            pass
        info.readline() # Bitrate
        info.readline() # Mode
        info.readline() # Error correction
        del info

    def update_from_logfile(self):
        commid = self.comm_id
        log = open(settings.COMM_LOG_FORMAT % commid, "r")
        metadata = {}
        for line in log:
            for regex in (self.CALL_LINE, self.WRITE_LINE):
                try:
                    g = regex.search(line).groupdict()
                except AttributeError:
                    continue
                for key in g.keys():
                    metadata[key] = g[key]
        if 'callerid' in metadata:
            self.callerid = metadata['callerid']
            
    def inout(self):
        if self.outbound:
            return 'Out'
        else:
            return 'In'

class Sender(models.Model):
    """
    These objects are now usable for OUTGOING fax numbers too, so we changed
    their verbose names for clarity.
    """
    label = models.CharField(_('name'),max_length=80, unique=True)
    class Meta:
        ordering = ('label',)
        verbose_name = _('correspondent')
        verbose_name_plural = _('correspondents')
    
    def __str__(self):
        return self.label.encode('utf-8')

class PhonebookEntry(models.Model):
    subject = models.ForeignKey(Sender, null=False)
    number = models.CharField(max_length=32)
    
    def __unicode__(self):
        return u'%s: %s' % (self.subject, self.number)
        
    class Meta:
        ordering = ('subject',)
        verbose_name = _('phonebook entry')
        verbose_name_plural = _('phonebook entries')

class SenderCID(models.Model):
    caller_id = models.CharField(_('calling number'),
        max_length=32)
    sender = models.ForeignKey(Sender,
        verbose_name=_('Sender'))

    class Meta:
        verbose_name = _('calling number')
        verbose_name_plural = _('calling numbers')
    
    def __str__(self):
        return self.caller_id + ' → %s' % self.sender
    
    
class SenderStationID(models.Model):
    station_id = models.CharField(_('calling station ID'),
        max_length=32)
    sender = models.ForeignKey(Sender,
        verbose_name=_('Sender'))

    class Meta:
        verbose_name = _('calling station ID')
        verbose_name_plural = _('calling station IDs')
        

    def __unicode__(self):
        return self.station_id + u' → %s' % self.sender

class FolderACL(models.Model):
    
    READ = 1
    REMOVE = 2
    INSERT = 3
    CREATE_SUBFOLDER = 4
    
    access_type_choices = (
        (1, 'READ'),
        (2, 'DELETE'),
#        (3, 'INSERT'),
#        (4, 'CREATE_SUBFOLDER')
    )
    
    @classmethod
    def get_access_type_string(cls, type_number):
        return cls.access_type_choices[type_number-1][1]
    
    folder = models.ForeignKey(Folder, null=False)
    group = models.ForeignKey(Group, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)
    access = models.IntegerField(choices=access_type_choices)
    permit = models.BooleanField()
    
    def clean(self):
        """
        Check that we have specified either a group or a user and not both
        of them.
        Also check the access type integer for meaningfulness.
        """
        from django.core.exceptions import ValidationError
        if (not self.user and not self.group) or (self.user and self.group):
            raise ValidationError("Exactly one of user and group must be set")
        if self.access not in [x[0] for x in self.access_type_choices]:
            raise ValidatonError("%s is not a valid access type" % self.access)
        return super(FolderACL, self).clean()
    
    def __unicode__(self):
        if self.permit:
            action = 'ALLOW'
        else:
            action = 'DENY'
        if self.user:
            subject = u'user %s' % self.user
        elif self.group:
            subject = u'group %s' % self.group
        else:
            raise ValueError("Exactly one of user and group must be set")
        return u'%s %s for %s on folder %s' % (action,
            self.get_access_type_string(self.access), subject, self.folder)
        
    
    class Meta:
        verbose_name = "folder ACL"
        
