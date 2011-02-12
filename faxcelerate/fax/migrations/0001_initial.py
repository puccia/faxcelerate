# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Folder'
        db.create_table('fax_folder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fax.Folder'], null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('fax', ['Folder'])

        # Adding model 'Fax'
        db.create_table('fax_fax', (
            ('comm_id', self.gf('django.db.models.fields.CharField')(max_length=9, primary_key=True)),
            ('station_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True)),
            ('caller_id', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('msn', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('received_on', self.gf('django.db.models.fields.DateTimeField')()),
            ('time_to_receive', self.gf('django.db.models.fields.IntegerField')()),
            ('conn_duration', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('pages', self.gf('django.db.models.fields.IntegerField')()),
            ('params', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('expiry', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fax.Sender'], null=True, blank=True)),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('_rotation', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_column='rotation', blank=True)),
            ('localsender', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('outbound', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('fax', ['Fax'])

        # Adding M2M table for field in_folders on 'Fax'
        db.create_table('fax_fax_in_folders', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('fax', models.ForeignKey(orm['fax.fax'], null=False)),
            ('folder', models.ForeignKey(orm['fax.folder'], null=False))
        ))
        db.create_unique('fax_fax_in_folders', ['fax_id', 'folder_id'])

        # Adding model 'Sender'
        db.create_table('fax_sender', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(unique=True, max_length=80)),
        ))
        db.send_create_signal('fax', ['Sender'])

        # Adding model 'SenderCID'
        db.create_table('fax_sendercid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('caller_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fax.Sender'])),
        ))
        db.send_create_signal('fax', ['SenderCID'])

        # Adding model 'SenderStationID'
        db.create_table('fax_senderstationid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('station_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fax.Sender'])),
        ))
        db.send_create_signal('fax', ['SenderStationID'])


    def backwards(self, orm):
        
        # Deleting model 'Folder'
        db.delete_table('fax_folder')

        # Deleting model 'Fax'
        db.delete_table('fax_fax')

        # Removing M2M table for field in_folders on 'Fax'
        db.delete_table('fax_fax_in_folders')

        # Deleting model 'Sender'
        db.delete_table('fax_sender')

        # Deleting model 'SenderCID'
        db.delete_table('fax_sendercid')

        # Deleting model 'SenderStationID'
        db.delete_table('fax_senderstationid')


    models = {
        'fax.fax': {
            'Meta': {'ordering': "('-received_on',)", 'object_name': 'Fax'},
            '_rotation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_column': "'rotation'", 'blank': 'True'}),
            'caller_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'comm_id': ('django.db.models.fields.CharField', [], {'max_length': '9', 'primary_key': 'True'}),
            'conn_duration': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expiry': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'in_folders': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['fax.Folder']", 'null': 'True', 'blank': 'True'}),
            'localsender': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'msn': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'outbound': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pages': ('django.db.models.fields.IntegerField', [], {}),
            'params': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'received_on': ('django.db.models.fields.DateTimeField', [], {}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fax.Sender']", 'null': 'True', 'blank': 'True'}),
            'station_id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            'time_to_receive': ('django.db.models.fields.IntegerField', [], {})
        },
        'fax.folder': {
            'Meta': {'ordering': "('order',)", 'object_name': 'Folder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fax.Folder']", 'null': 'True', 'blank': 'True'})
        },
        'fax.sender': {
            'Meta': {'ordering': "('label',)", 'object_name': 'Sender'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'})
        },
        'fax.sendercid': {
            'Meta': {'object_name': 'SenderCID'},
            'caller_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fax.Sender']"})
        },
        'fax.senderstationid': {
            'Meta': {'object_name': 'SenderStationID'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fax.Sender']"}),
            'station_id': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['fax']
