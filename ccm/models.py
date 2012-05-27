from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
import datetime

class Agent(models.Model):
    name = models.CharField(max_length=100,unique = True)
    user = models.OneToOneField(User)
    role = models.CharField(max_length=30, db_index=True, choices=(
        ('agent','Agent'),
        ('lead','Team Lead'),
        ('manager','CC Manager'),
        ('supervisor','Supervisor'),
        ('trainer','Trainer'),
        ('quality_control','Quality Control')))
    clients = models.ManyToManyField('accounts.Client', null=True, blank=True)
    report_to = models.ForeignKey('self', related_name='agents', limit_choices_to={'role':'lead'}, verbose_name='Report To', null=True, blank=True)

    def __unicode__(self):
        return self.name

    def Meta():
        ordering = ('name',)

    def get_daily_sales(self):
        daily_sale_key = 'dailysale#%s' % (self.id)
        daily_sale = cache.get(daily_sale_key)
        if daily_sale == None:
            today = datetime.datetime.now()
            start = today.date()
            end = (today + datetime.timedelta(days=1)).date()
            from utils.utils import get_user_profile
            profile = get_user_profile(self.user)
            q = 'doc_type:order AND booking_agent_id:%s AND support_state:confirmed AND confirming_timestamp:[%sT00:00:00Z TO %sT00:00:00Z]' % (profile.id, start, end)
            from utils.solrutils import order_solr_search
            solr_result = order_solr_search(q, stats='true', stats_field='payable_amount')
            daily_sale = 0
            if solr_result:
                daily_sale = solr_result.stats['stats_fields']['payable_amount']['sum']
            cache.set(daily_sale_key, daily_sale,600)
        return daily_sale

class AgentLoginLogout(models.Model):
    agent = models.ForeignKey('Agent')
    time = models.DateTimeField()
    action = models.CharField(max_length=20)
    destination = models.CharField(max_length=20, choices=(('asterisk','Asterisk'),('queue','Queue')), default='asterisk')

class Extension(models.Model):
    protocol = models.CharField(max_length=15, db_index=True, default='sip', choices=(
        ('sip','SIP'),))
    number = models.CharField(max_length=10, db_index=True)
    pin = models.CharField(max_length=6)
    allotted_to = models.ForeignKey(Agent, related_name='extension')

    class Meta:
        unique_together = ('protocol', 'number')

class CallSlot(models.Model):
    """call slots model:
    
    day_of_week are for sun-sat
    they are handled with CallSlotForm for serialization from Multiple Select
    Field to char value
    """
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.CharField(max_length=7, default='0111110', blank=True)

    def __unicode__(self):
        return u'%s' % self.name

class Queue(models.Model):
    name = models.CharField(max_length=50, unique=True)
