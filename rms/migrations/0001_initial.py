# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Campaign'
        db.create_table('rms_campaign', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(related_name='campaigns', to=orm['accounts.Client'])),
            ('funnel', self.gf('django.db.models.fields.related.ForeignKey')(related_name='campaigns', to=orm['rms.Funnel'])),
            ('dni_number', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('starts_on', self.gf('django.db.models.fields.DateTimeField')()),
            ('ends_on', self.gf('django.db.models.fields.DateTimeField')()),
            ('draft', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True, blank=True)),
            ('script', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('demo', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('rms', ['Campaign'])

        # Adding unique constraint on 'Campaign', fields ['name', 'client']
        db.create_unique('rms_campaign', ['name', 'client_id'])

        # Adding M2M table for field agents on 'Campaign'
        db.create_table('rms_campaign_agents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('campaign', models.ForeignKey(orm['rms.campaign'], null=False)),
            ('agent', models.ForeignKey(orm['ccm.agent'], null=False))
        ))
        db.create_unique('rms_campaign_agents', ['campaign_id', 'agent_id'])

        # Adding model 'Funnel'
        db.create_table('rms_funnel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal('rms', ['Funnel'])

        # Adding model 'FunnelState'
        db.create_table('rms_funnelstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('funnel', self.gf('django.db.models.fields.related.ForeignKey')(related_name='funnel_states', to=orm['rms.Funnel'])),
        ))
        db.send_create_signal('rms', ['FunnelState'])

        # Adding unique constraint on 'FunnelState', fields ['name', 'funnel']
        db.create_unique('rms_funnelstate', ['name', 'funnel_id'])

        # Adding model 'FunnelSubState'
        db.create_table('rms_funnelsubstate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('funnel_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='funnel_sub_states', to=orm['rms.FunnelState'])),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(related_name='campaign_sub_states', to=orm['rms.Campaign'])),
            ('is_end_state', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('rms', ['FunnelSubState'])

        # Adding unique constraint on 'FunnelSubState', fields ['name', 'funnel_state', 'campaign']
        db.create_unique('rms_funnelsubstate', ['name', 'funnel_state_id', 'campaign_id'])

        # Adding model 'Response'
        db.create_table('rms_response', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('campaign', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['rms.Campaign'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Phone'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('is_closed', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('closed_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('medium', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('funnel_state', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='+', to=orm['rms.FunnelState'])),
            ('funnel_sub_state', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='responses', null=True, blank=True, to=orm['rms.FunnelSubState'])),
            ('assigned_to', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='responses', null=True, to=orm['ccm.Agent'])),
            ('last_interaction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', null=True, to=orm['rms.Interaction'])),
            ('last_interacted_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccm.Agent'], null=True)),
            ('last_interacted_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 8, 14, 21, 36, 245443), null=True)),
            ('followup_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 8, 8, 14, 21, 36, 245515))),
            ('call_in_progress', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('connections', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('rms', ['Response'])

        # Adding model 'Interaction'
        db.create_table('rms_interaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response', self.gf('django.db.models.fields.related.ForeignKey')(related_name='interactions', to=orm['rms.Response'])),
            ('agent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccm.Agent'], null=True, blank=True)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True, blank=True)),
            ('communication_mode', self.gf('django.db.models.fields.related.ForeignKey')(related_name='interactions', to=orm['contenttypes.ContentType'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('pre_funnel_state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['rms.FunnelState'])),
            ('pre_funnel_sub_state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['rms.FunnelSubState'])),
            ('post_funnel_state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['rms.FunnelState'])),
            ('post_funnel_sub_state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['rms.FunnelSubState'])),
            ('followup_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('rms', ['Interaction'])


    def backwards(self, orm):
        
        # Deleting model 'Campaign'
        db.delete_table('rms_campaign')

        # Removing unique constraint on 'Campaign', fields ['name', 'client']
        db.delete_unique('rms_campaign', ['name', 'client_id'])

        # Removing M2M table for field agents on 'Campaign'
        db.delete_table('rms_campaign_agents')

        # Deleting model 'Funnel'
        db.delete_table('rms_funnel')

        # Deleting model 'FunnelState'
        db.delete_table('rms_funnelstate')

        # Removing unique constraint on 'FunnelState', fields ['name', 'funnel']
        db.delete_unique('rms_funnelstate', ['name', 'funnel_id'])

        # Deleting model 'FunnelSubState'
        db.delete_table('rms_funnelsubstate')

        # Removing unique constraint on 'FunnelSubState', fields ['name', 'funnel_state', 'campaign']
        db.delete_unique('rms_funnelsubstate', ['name', 'funnel_state_id', 'campaign_id'])

        # Deleting model 'Response'
        db.delete_table('rms_response')

        # Deleting model 'Interaction'
        db.delete_table('rms_interaction')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'dni': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'greeting_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'greeting_title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'pg_return_url': ('django.db.models.fields.URLField', [], {'default': "'http://www.chaupaati.in'", 'max_length': '200', 'blank': 'True'}),
            'primary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'returns_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'shipping_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tos': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Channel'", 'max_length': '100'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'accounts.client': {
            'Meta': {'object_name': 'Client'},
            'clientdomain_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'feedback_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> feedback@chaupaati.com'", 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'promotions_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> promotions@chaupaati.com'", 'max_length': '200'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'ccm.agent': {
            'Meta': {'object_name': 'Agent'},
            'clients': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.Client']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rms.campaign': {
            'Meta': {'unique_together': "(('name', 'client'),)", 'object_name': 'Campaign'},
            'agents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'campaigns'", 'symmetrical': 'False', 'to': "orm['ccm.Agent']"}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaigns'", 'to': "orm['accounts.Client']"}),
            'demo': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'dni_number': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'draft': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True', 'blank': 'True'}),
            'ends_on': ('django.db.models.fields.DateTimeField', [], {}),
            'funnel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaigns'", 'to': "orm['rms.Funnel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'script': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'starts_on': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        'rms.funnel': {
            'Meta': {'object_name': 'Funnel'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'rms.funnelstate': {
            'Meta': {'unique_together': "(('name', 'funnel'),)", 'object_name': 'FunnelState'},
            'funnel': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'funnel_states'", 'to': "orm['rms.Funnel']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rms.funnelsubstate': {
            'Meta': {'unique_together': "(('name', 'funnel_state', 'campaign'),)", 'object_name': 'FunnelSubState'},
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'campaign_sub_states'", 'to': "orm['rms.Campaign']"}),
            'funnel_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'funnel_sub_states'", 'to': "orm['rms.FunnelState']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_end_state': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rms.interaction': {
            'Meta': {'object_name': 'Interaction'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccm.Agent']", 'null': 'True', 'blank': 'True'}),
            'communication_mode': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'interactions'", 'to': "orm['contenttypes.ContentType']"}),
            'followup_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'post_funnel_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['rms.FunnelState']"}),
            'post_funnel_sub_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['rms.FunnelSubState']"}),
            'pre_funnel_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['rms.FunnelState']"}),
            'pre_funnel_sub_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['rms.FunnelSubState']"}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'interactions'", 'to': "orm['rms.Response']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'rms.response': {
            'Meta': {'object_name': 'Response'},
            'assigned_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responses'", 'null': 'True', 'to': "orm['ccm.Agent']"}),
            'attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'call_in_progress': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': "orm['rms.Campaign']"}),
            'closed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'connections': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'followup_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 8, 14, 21, 36, 245515)'}),
            'funnel_state': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'to': "orm['rms.FunnelState']"}),
            'funnel_sub_state': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'responses'", 'null': 'True', 'blank': 'True', 'to': "orm['rms.FunnelSubState']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_interacted_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccm.Agent']", 'null': 'True'}),
            'last_interacted_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2011, 8, 8, 14, 21, 36, 245443)', 'null': 'True'}),
            'last_interaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': "orm['rms.Interaction']"}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Phone']"})
        },
        'users.phone': {
            'Meta': {'object_name': 'Phone'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']"})
        },
        'users.profile': {
            'Meta': {'object_name': 'Profile'},
            'acquired_through_account': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_customers'", 'null': 'True', 'to': "orm['accounts.Account']"}),
            'atg_username': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'buyer_or_seller': ('django.db.models.fields.CharField', [], {'default': "'Buyer'", 'max_length': '100'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer_of_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'customers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email_notification': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_agent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'managed_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'account_staff'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'marketing_alerts': ('django.db.models.fields.CharField', [], {'default': "'neutral'", 'max_length': '25'}),
            'passcode': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'profession': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'salutation': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'sms_alert': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['users.UserTag']", 'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'verify_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'webpage': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'users.usertag': {
            'Meta': {'object_name': 'UserTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        }
    }

    complete_apps = ['rms']