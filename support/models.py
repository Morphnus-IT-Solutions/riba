from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User as AuthUser

from orders.models import Order, OrderItem
from utils.fields import TimeDeltaField

class Team(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return u'%s' % self.name


class User(models.Model):
    user = models.ForeignKey(AuthUser, related_name='+', unique=True)
    team = models.ForeignKey(Team, related_name='members', blank=True, null=True)
    role = models.CharField(max_length=10, choices=(('member','Member'),('lead','Lead')), default='member')

    def __unicode__(self):
        return u'%s' % self.user.username

    class Meta:
        unique_together = ('user', 'team')


class State(models.Model):
    name = models.CharField(max_length=200, unique=True)
    responsible_team = models.ForeignKey(Team, blank=True, null=True, related_name='responsible_states', verbose_name='Responsible Team')

    def __unicode__(self):
        return u'%s' % self.name


class SubState(models.Model):
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, related_name='substates')
    entity = models.ForeignKey(ContentType, related_name='substates')
    acting_team = models.ForeignKey(Team, blank=True, null=True, related_name='acting_substates', verbose_name='Acting Team')
    tat = TimeDeltaField(blank=True, null=True, verbose_name='Turn Around Time')
    
    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        unique_together = ('name', 'entity')


class ActionFlow(models.Model):
    name = models.CharField(max_length=200)
    initial_state = models.ForeignKey(State, related_name='+', verbose_name='Initial State')
    initial_substate = models.ForeignKey(SubState, related_name='out_action_flows', verbose_name='Initial Substate')
    final_state = models.ForeignKey(State, null=True, blank=True, related_name='+', verbose_name='Final State')
    final_substate = models.ForeignKey(SubState, null=True, blank=True, related_name='in_action_flows', verbose_name='Final Substate')
    group = models.PositiveIntegerField(default=1)  #used to filter payment action flows
    
    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        unique_together = ('name', 'initial_substate', 'final_substate','group')


class InformationFlow(models.Model):
    name = models.CharField(max_length=200)
    state = models.ForeignKey(State, related_name='+')
    substate = models.ForeignKey(SubState, related_name='information_flows',)
    acting_team = models.ForeignKey(Team, related_name='information_flows', verbose_name='Acting Team')
    receipients = models.ManyToManyField(Team, related_name='+')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        unique_together = ('name', 'substate')

#will not be using this model - prady
class OrderLog(models.Model):
    order = models.ForeignKey(Order, related_name='+')
    action = models.ForeignKey('Action', null=True, blank=True, related_name='+')
    user = models.ForeignKey(User, null=True, blank=True, related_name='+')
    timestamp = models.DateTimeField(auto_now_add=True)

#will not be using this model - prady
class Action(models.Model):
    user = models.ForeignKey(User, related_name='+')
    flow_type = models.ForeignKey(ContentType, related_name='+')
    flow_object_id = models.PositiveIntegerField()
    flow_object = generic.GenericForeignKey('flow_type', 'flow_object_id')
    entity_type = models.ForeignKey(ContentType, related_name='actions')
    entity_object_id = models.PositiveIntegerField()
    entity_object = generic.GenericForeignKey('entity_type', 'entity_object_id')
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)


#class Escalation(models.Model):
#    order = models.ForeignKey(OrderStatus, related_name='escalations')
#    state = models.ForeignKey(State, related_name='escalations')
#    substate = models.ForeignKey(SubState, related_name='escalations')
#    timestamp = models.DateTimeField(auto_now_add=True)

