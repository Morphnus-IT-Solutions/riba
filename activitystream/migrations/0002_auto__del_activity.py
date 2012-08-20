# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Activity'
        db.delete_table('activitystream_activity')


    def backwards(self, orm):
        
        # Adding model 'Activity'
        db.create_table('activitystream_activity', (
            ('astatus', self.gf('django.db.models.fields.CharField')(default='Visible', max_length=50)),
            ('asrc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.SellerRateChart'], null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Profile'], null=True, blank=True)),
            ('atime', self.gf('django.db.models.fields.PositiveIntegerField')(default=1302257077)),
            ('atype', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('aclientdomain', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.ClientDomain'])),
            ('astream', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('activitystream', ['Activity'])


    models = {
        
    }

    complete_apps = ['activitystream']
