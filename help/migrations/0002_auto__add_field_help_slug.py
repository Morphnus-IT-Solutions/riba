# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Help.slug'
        db.add_column('help_help', 'slug', self.gf('django.db.models.fields.SlugField')(default='', unique=True, max_length=50, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Help.slug'
        db.delete_column('help_help', 'slug')


    models = {
        'help.help': {
            'Meta': {'object_name': 'Help'},
            'heading': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'help': ('tinymce.models.HTMLField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['help']
