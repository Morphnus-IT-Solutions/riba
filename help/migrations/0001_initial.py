# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Help'
        db.create_table('help_help', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('heading', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('help', self.gf('tinymce.models.HTMLField')(blank=True)),
        ))
        db.send_create_signal('help', ['Help'])


    def backwards(self, orm):
        
        # Deleting model 'Help'
        db.delete_table('help_help')


    models = {
        'help.help': {
            'Meta': {'object_name': 'Help'},
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'help': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['help']
