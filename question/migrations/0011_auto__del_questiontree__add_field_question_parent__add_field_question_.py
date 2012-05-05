# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'QuestionTree'
        db.delete_table('question_questiontree')

        # Adding field 'Question.parent'
        db.add_column('question_question', 'parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='parent_question', null=True, to=orm['question.Question']), keep_default=False)

        # Adding field 'Question.parent_value'
        db.add_column('question_question', 'parent_value', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=100, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'QuestionTree'
        db.create_table('question_questiontree', (
            ('parent_question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='parent_question', null=True, to=orm['question.Question'], blank=True)),
            ('parent_value', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('question', ['QuestionTree'])

        # Deleting field 'Question.parent'
        db.delete_column('question_question', 'parent_id')

        # Deleting field 'Question.parent_value'
        db.delete_column('question_question', 'parent_value')


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
            'max_times': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_question'", 'null': 'True', 'to': "orm['question.Question']"}),
            'parent_value': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['question']
