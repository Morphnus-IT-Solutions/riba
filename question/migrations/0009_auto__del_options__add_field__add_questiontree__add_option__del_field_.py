# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Options'
        db.delete_table('question_options')

        # Adding model 'Field'
        db.create_table('question_field', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('fieldname', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('fieldtype', self.gf('django.db.models.fields.CharField')(default='char', max_length=15, db_index=True)),
        ))
        db.send_create_signal('question', ['Field'])

        # Adding model 'QuestionTree'
        db.create_table('question_questiontree', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('parent_question', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='parent_question', null=True, to=orm['question.Question'])),
            ('parent_value', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('question', ['QuestionTree'])

        # Adding model 'Option'
        db.create_table('question_option', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('question', ['Option'])

        # Deleting field 'Question.is_dynamic'
        db.delete_column('question_question', 'is_dynamic')

        # Adding field 'Question.max_times'
        db.add_column('question_question', 'max_times', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'Options'
        db.create_table('question_options', (
            ('dependent_question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dependent_question', null=True, to=orm['question.Question'], blank=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('question', ['Options'])

        # Deleting model 'Field'
        db.delete_table('question_field')

        # Deleting model 'QuestionTree'
        db.delete_table('question_questiontree')

        # Deleting model 'Option'
        db.delete_table('question_option')

        # Adding field 'Question.is_dynamic'
        db.add_column('question_question', 'is_dynamic', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Deleting field 'Question.max_times'
        db.delete_column('question_question', 'max_times')


    models = {
        'question.field': {
            'Meta': {'object_name': 'Field'},
            'fieldname': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'fieldtype': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
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
