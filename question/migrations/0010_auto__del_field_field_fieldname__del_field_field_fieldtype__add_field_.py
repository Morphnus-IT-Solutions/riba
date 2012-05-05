# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Field.fieldname'
        db.delete_column('question_field', 'fieldname')

        # Deleting field 'Field.fieldtype'
        db.delete_column('question_field', 'fieldtype')

        # Adding field 'Field.field_label'
        db.add_column('question_field', 'field_label', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'Field.field_type'
        db.add_column('question_field', 'field_type', self.gf('django.db.models.fields.CharField')(default='char', max_length=15, db_index=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding field 'Field.fieldname'
        db.add_column('question_field', 'fieldname', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'Field.fieldtype'
        db.add_column('question_field', 'fieldtype', self.gf('django.db.models.fields.CharField')(default='char', max_length=15, db_index=True), keep_default=False)

        # Deleting field 'Field.field_label'
        db.delete_column('question_field', 'field_label')

        # Deleting field 'Field.field_type'
        db.delete_column('question_field', 'field_type')


    models = {
        'question.field': {
            'Meta': {'object_name': 'Field'},
            'field_label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'field_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"})
        },
        'question.option': {
            'Meta': {'object_name': 'Option'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'question.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_times': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        },
        'question.questiontree': {
            'Meta': {'unique_together': "(('question', 'parent_question', 'parent_value'),)", 'object_name': 'QuestionTree'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_question': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_question'", 'null': 'True', 'to': "orm['question.Question']"}),
            'parent_value': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"})
        }
    }

    complete_apps = ['question']
