# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Questionnaire'
        db.delete_table('build_document_questionnaire')

        # Deleting model 'Template'
        db.delete_table('build_document_template')


    def backwards(self, orm):
        
        # Adding model 'Questionnaire'
        db.create_table('build_document_questionnaire', (
            ('keyword', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'], null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['build_document.Template'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('build_document', ['Questionnaire'])

        # Adding model 'Template'
        db.create_table('build_document_template', (
            ('upload_text', self.gf('tinymce.models.HTMLField')(null=True, blank=True)),
            ('list_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Category'])),
            ('information', self.gf('tinymce.models.HTMLField')(null=True, blank=True)),
            ('about', self.gf('tinymce.models.HTMLField')(null=True, blank=True)),
            ('time_to_build', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('offer_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, db_index=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('upload_document', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(default='new', max_length=20, blank=True, db_index=True)),
        ))
        db.send_create_signal('build_document', ['Template'])


    models = {
        
    }

    complete_apps = ['build_document']
