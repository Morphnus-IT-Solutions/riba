# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Template.template_doc'
        db.delete_column('build_document_template', 'template_doc')

        # Deleting field 'Template.template_text'
        db.delete_column('build_document_template', 'template_text')

        # Adding field 'Template.upload_document'
        db.add_column('build_document_template', 'upload_document', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'Template.upload_text'
        db.add_column('build_document_template', 'upload_text', self.gf('tinymce.models.HTMLField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'Template.template_doc'
        db.add_column('build_document_template', 'template_doc', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'Template.template_text'
        db.add_column('build_document_template', 'template_text', self.gf('tinymce.models.HTMLField')(null=True, blank=True), keep_default=False)

        # Deleting field 'Template.upload_document'
        db.delete_column('build_document_template', 'upload_document')

        # Deleting field 'Template.upload_text'
        db.delete_column('build_document_template', 'upload_text')


    models = {
        'build_document.template': {
            'Meta': {'object_name': 'Template'},
            'about': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'information': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'offer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '20', 'blank': 'True'}),
            'time_to_build': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'upload_document': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'upload_text': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'})
        },
        'categories.category': {
            'Meta': {'object_name': 'Category'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['build_document']
