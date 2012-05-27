import re
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime
from django.contrib.contenttypes import generic

from accounts.models import Client
from ccm.models import Agent
from users.models import Phone, Permission

class Campaign(models.Model):
    name = models.CharField('name', max_length=200, blank=False)
    client = models.ForeignKey(Client, related_name='campaigns', blank=False)
    funnel = models.ForeignKey('Funnel', related_name='campaigns')
    dni_number = models.CharField('DNI', max_length=15, blank=False, unique=True)
    hotline = models.CharField(max_length=15, blank=True, null=True)
    type = models.CharField('Inbound/Outbound', max_length=15, blank=False,
        choices=(('inbound','Inbound'),
                ('outbound','Outbound')))
    priority = models.IntegerField(blank=False, default=1,
        choices=((1,'High'),(2,'Medium'),(3,'Low')))    # Campaign priority
    inbound_agents = models.ManyToManyField(Agent, related_name='inbound_campaigns', blank=True, null=True)
    outbound_agents = models.ManyToManyField(Agent, related_name='outbound_campaigns', blank=True, null=True)
    starts_on = models.DateTimeField('Start Time', blank=False)
    ends_on = models.DateTimeField('End Time', blank=True, null=True)
    draft = models.BooleanField('draft', default=True, db_index=True)
    script = models.TextField(blank=True, null=True)
      
    #Demo campaigns will be used to retrieve funnel templates
    demo = models.BooleanField(default=False)
    #Generic relation to all permitted users
    users = generic.GenericRelation(Permission)
    greeting_title = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', 'client')
        permissions = (('view_campaign', 'Can view campaign'),)

    def __unicode__(self):
        return u'%s-%s' % (self.name,self.client)

    def clean(self):
        if (not self.demo) and self.ends_on and self.starts_on and (self.ends_on <= self.starts_on):
            raise ValidationError('Campaign\'s end date can\'t precede it\'s start date')
        if (self.hotline) and not (re.compile('^\d{10}$').match(self.hotline) or re.compile('^\d{11}$').match(self.hotline)):
            raise ValidationError('Hotline should be a 10 or 11 digit number')
        if (self.dni_number) and not re.compile('^\d{4}$').match(self.dni_number):
            raise ValidationError('DNI should be a 4 digit number')


class Funnel(models.Model):
    """model for 'reusable' Funnels.
    
    Pre-congured funnels will define a workflow for one type of campaign, viz
    sales, promotion, etc. All campaign will use one or the other funnel for
    it's workflow.
    NOTE: Each funnel has unique set of states associated with it.
    """
    name = models.CharField('name', max_length=100, unique=True, blank=False)

    def __unicode__(self):
        return u"%s" % self.name

    class Meta:
        permissions = (('view_funnel', 'Can view funnel'),)


class FunnelState(models.Model):
    """State model for funnel
    
    Each Funnel will be comprised of one or more FunnelStates.
    """
    name = models.CharField(max_length=100, blank=False)
    funnel = models.ForeignKey(Funnel, related_name='funnel_states')

    class Meta:
        unique_together = ('name', 'funnel')
        permissions = (('view_funnelstate', 'Can view funnelstate'),)

    def __unicode__(self):
        return u"%s-%s" % (self.name, self.funnel)


class FunnelSubState(models.Model):
    """FunnelSubState model

    Each FunnelState is further divided into many FunnelSubstates.
    """
    index = models.PositiveIntegerField()
    name = models.CharField(max_length=100, blank=False)
    funnel_state = models.ForeignKey(FunnelState, related_name='funnel_sub_states')
    campaign = models.ForeignKey(Campaign, related_name='campaign_sub_states') #Foreign key to campaign is needed for response_count    
    exit_substate = models.BooleanField('is exit substate', default=False)
    is_active = models.BooleanField('is active', default=True) #Agents can only tag a response into active substates
    
    class Meta:
        unique_together = ('name', 'funnel_state', 'campaign')
        ordering = ('index',)
        permissions = (('view_funnelsubstate', 'Can view funnelsubstate'),)

    def __unicode__(self):
        return u'%s-%s-%s' % (self.name, self.funnel_state, self.campaign)


class Response(models.Model):
    """Response Model
    When a new Response is created, it has no funnel_sub_state. This
    corresponds to 'new' Response. In it's lifetime, it can never again be
    without a funnel sub-state.
    """
    campaign = models.ForeignKey(Campaign, related_name='responses')

    phone = models.ForeignKey(Phone)
    created_on = models.DateTimeField('created on', auto_now_add=True)
    is_closed = models.BooleanField(blank=False, default=False, db_index=True)
    closed_on = models.DateTimeField('closed on', blank=True, null=True)
    closed_by = models.ForeignKey(Agent, null=True, blank=True, default=None, related_name='+')
    medium = models.CharField('medium of first interaction', max_length=30,
            blank=True, null=True, choices=(('chat','Chat'),
                                            ('inbound','Inbound'),
                                            ('sms','SMS'),
                                            ('web','Web'),
                                            ('email','Email'),
                                            ('database','Database')))

    funnel_state = models.ForeignKey(FunnelState, related_name='+', default=None, blank=True, null=True)
    funnel_sub_state = models.ForeignKey(FunnelSubState, related_name='responses', null=True, blank=True, default=None)
    
    #assigned_to field acts as a lock and prevents this response from being sent to other agents
    assigned_to = models.ForeignKey(Agent, null=True, blank=True, related_name='responses')
    
    last_interaction = models.ForeignKey('Interaction', related_name='+', null=True)
    last_interacted_by = models.ForeignKey(Agent, null=True)
    last_interacted_on = models.DateTimeField(null=True, blank=True, db_index=True)
    followup_on = models.DateTimeField('follow up on', null=True, blank=True, auto_now_add=True, db_index=True)
    
    call_in_progress = models.BooleanField(blank=False, default=False) # works as a lock
    on_hold = models.BooleanField(blank=False, default=False)  # True when agent puts this response on hold
    attempts = models.IntegerField(blank=False, default=0)  # Successful + Unsuccessful attempts
    connections = models.IntegerField(blank=False, default=0) # Only successful connections    
    orders  = models.ManyToManyField('orders.Order', blank=True, null=True, related_name='response')

    class Meta:
        permissions = (('view_response', 'Can view response'),) 
    
    def __unicode__(self):
        return u"Response: #%s" % (self.id,)

    def clean(self):
        """Custom clean method
        - override save method to accomodate the modified behaviour for 'new'
        Responses (ones without funnel_sub_state)"""
        if self.id and not self.funnel_sub_state:
            raise ValidationError('Old Responses must have funnel_sub_state')


class Interaction(models.Model):
    """model for Interaction
    
    a communication (attempted/realized) between an agent and a customer
    """

    response = models.ForeignKey(Response, related_name='interactions')
    agent = models.ForeignKey(Agent, null=True, blank=True)
    # some interactions are invalid. a flag to filter them off from reports
    # we create the interaction object before asterisk responds 
    # and it could come back saying it couldn't try
    invalid = models.BooleanField(default=False, db_index=True)

    communication_mode = models.CharField('mode of communication', max_length=30,
            blank=True, null=True, choices=(('call','Call'),
                                            ('chat','Chat'),
                                            ('sms','SMS'),
                                            ('email','Email')))
    # We want to capture the following details in each interaction.
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    pre_funnel_state = models.ForeignKey(FunnelState, null=True, blank=True, related_name='+')
    pre_funnel_sub_state = models.ForeignKey(FunnelSubState, null=True, blank=True, related_name='+')
    post_funnel_state = models.ForeignKey(FunnelState, null=True, blank=True, related_name='+')
    post_funnel_sub_state = models.ForeignKey(FunnelSubState, null=True, blank=True, related_name='+')
    followup_on = models.DateTimeField(null=True, blank=True)
    #call_status = models.CharField(max_length=25, null=False, blank=False)
    callid = models.CharField(max_length=25, null=True, blank=True)

    class Meta:
        ordering = ('-timestamp',)
        permissions = (('view_interaction', 'Can view interaction'),)
