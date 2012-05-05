# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Question.parent'
        db.alter_column('question_question', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, null=True, to=orm['question.Question']))


    def backwards(self, orm):
        
        # Changing field 'Question.parent'
        db.alter_column('question_question', 'parent_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'], blank=True))


    models = {
        'question.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dynamic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_question'", 'null': 'True', 'to': "orm['question.Question']"}),
            'parent_value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['question']
