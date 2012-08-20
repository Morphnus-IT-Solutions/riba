# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'DpsContactInfo'
        db.delete_table('atg_dpscontactinfo')


    def backwards(self, orm):
        
        # Adding model 'DpsContactInfo'
        db.create_table('atg_dpscontactinfo', (
            ('info', self.gf('django.db.models.fields.CharField')(max_length=40, primary_key=True, db_column='id')),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('suffix', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('address1', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('address2', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('address3', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('fax_number', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('county', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('prefix', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('company_name', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('user_id', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('phone_number', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('job_title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('atg', ['DpsContactInfo'])


    models = {
        
    }

    complete_apps = ['atg']
