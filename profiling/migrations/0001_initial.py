# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ProfilerData'
        db.create_table('profiling_profilerdata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('view', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('timeAdded', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('profile', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('profiling', ['ProfilerData'])


    def backwards(self, orm):
        
        # Deleting model 'ProfilerData'
        db.delete_table('profiling_profilerdata')


    models = {
        'profiling.profilerdata': {
            'Meta': {'object_name': 'ProfilerData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'profile': ('django.db.models.fields.TextField', [], {}),
            'timeAdded': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'view': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['profiling']
