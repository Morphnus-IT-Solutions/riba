# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Options'
        db.create_table('question_options', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('dependent_question', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='dependent_question', null=True, to=orm['question.Question'])),
        ))
        db.send_create_signal('question', ['Options'])

        # Deleting field 'Question.parent'
        db.delete_column('question_question', 'parent_id')

        # Deleting field 'Question.parent_value'
        db.delete_column('question_question', 'parent_value')


    def backwards(self, orm):
        
        # Deleting model 'Options'
        db.delete_table('question_options')

        # Adding field 'Question.parent'
        db.add_column('question_question', 'parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parent_question', null=True, to=orm['question.Question'], blank=True), keep_default=False)

        # Adding field 'Question.parent_value'
        db.add_column('question_question', 'parent_value', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)


    models = {
        'question.options': {
            'Meta': {'object_name': 'Options'},
            'dependent_question': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'dependent_question'", 'null': 'True', 'to': "orm['question.Question']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'question.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dynamic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['question']
