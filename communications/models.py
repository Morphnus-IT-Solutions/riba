from django.db import models
import logging
import urllib
import urllib2
from datetime import datetime
import re
from tinymce.models import HTMLField
from accounts.models import ClientDomain
log = logging.getLogger('request')

# Create your models here.
class Email(models.Model):
    #client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True, default = ClientDomain.objects.get(id = 1))
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True, default = 1)
    order = models.ForeignKey('orders.Order', blank = True, null = True)
    profile = models.ForeignKey('users.Profile', blank = True, null = True, related_name = 'user_profile')

    sent_to = models.CharField(max_length=1000, db_index=True)
    ccied_to = models.CharField(max_length=200, db_index=True, blank=True)
    bccied_to = models.CharField(max_length=200, db_index=True, blank=True)
    sent_from = models.EmailField(max_length=100, db_index=True)

    subject = models.TextField()
    body = HTMLField()

    sent_via = models.CharField(max_length=50, db_index=True)
    status = models.CharField(max_length=15, db_index=True, choices=(
        ('in_queue', 'In queue'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('delivery_failed', 'Bounced'),
        ('unable_to_send', 'Unable to send')))
    type = models.CharField(max_length=30, db_index=True, null = True, blank = True, choices=(
        ('buyer_order_confirmation', 'Buyer Order Confirmation'),
        ('seller_order_confirmation', 'Seller Order Confirmation'),
        ('buyer_order_cancellation', 'Buyer Order Cancellation'),
        ('seller_order_cancellation', 'Seller Order Cancellation'),
        ('product_sharing', 'Product Sharing'),
        ('buyer_pending_order', 'Buyer Pending Order'),
        ('seller_pending_order', 'Seller Pending Order'),
        ('shipped_order', 'Shipped Order'),
        ('user_subscription', 'User Subscription'),
        ('forgot_password', 'Forgot Password'),
        ('user_feedback', 'User Feedback')))

    created_on = models.DateTimeField(auto_now_add=True)
    sent_on = models.DateTimeField(blank=True, null=True)
    bounced_on = models.DateTimeField(blank=True, null=True)
    delivered_on = models.DateTimeField(blank=True, null=True)

class SMS(models.Model):
    sent_to = models.CharField(max_length=15)
    sms_text = models.TextField()
    mask = models.CharField(max_length=15, default='FutrBazr', choices=(
        ('9222221947','9222221947'),
        ('Chaupati','Chaupati'),
        ('FutrBazr','FutrBazr'),
        ('Potluck','Potluck')))

    created_on = models.DateTimeField(auto_now_add=True)
    sent_on = models.DateTimeField(blank=True, null=True)
    bounced_on = models.DateTimeField(blank=True, null=True)
    delivered_on = models.DateTimeField(blank=True, null=True)
    sent_through = models.CharField(max_length=20, blank=True, choices=(
        ('netcore','Netcore'),
        ('smsgupshup', 'SMS Gupshup')), default='netcore')

    # counters
    attempts = models.IntegerField(default=0)

    status = models.CharField(max_length=15, db_index=True, default='new', choices=(
        ('new','New'),
        ('in_queue', 'In queue'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('rejected', 'Rejected'),
        ('delivery_failed', 'Delivery failed'),
        ('unable_to_send', 'Unable to send')))

    def __unicode__(self):
        return "Mask: %s\nTo: %s\nText: %s\n" % (self.mask, self.sent_to, self.sms_text)

    def fill_message_details(self, params):
        if self.sent_through == 'netcore':
            params['text'] = self.sms_text
            params['to'] =  '91%s' % self.sent_to
            params['senderid'] = self.mask
        if self.sent_through == 'SMS Gupshup API':
            pass

    def fill_credentials(self, params):
        if self.sent_through == 'netcore':
            if self.mask == 'FutrBazr':
                params['feedid'] = '315128'
                params['username'] = '9819766601'
                params['password'] = 'dwdjd'
            elif self.mask.lower() == 'ezone':
                params['feedid'] = '244294'
                params['username'] = '9769122118'
                params['password'] = 'ggdpt'
            else:
                params['feedid'] = '263153'
                params['username'] = '9819766601'
                params['password'] = 'dwdjd'
        if self.sent_through == 'SMS Gupshup API':
            pass

    def on_sent(self, response):
        if self.sent_through == 'netcore':
            error_re = re.compile('.*ERROR.*')
            if error_re.match(response.replace('\r','').replace('\n','')):
                self.status = 'in_queue'
            else:
                self.status = 'sent'
            self.save()
        if self.sent_through == 'smsgupshup':
            return ''

    def get_base_url(self):
        if self.sent_through == 'netcore':
            base_url = 'http://bulkpush.mytoday.com/BulkSms/SingleMsgApi?'
        if self.sent_through == 'SMS Gupshup API':
            pass
        return base_url

    def send(self):
        if not self.status in ['new','in_queue']:
            return
        try:
            if len(self.sent_to) != 10:
                return
            if self.sent_to[0] not in ['9','8','7']:
                return
            if not self.sms_text:
                return
            q = {}
            self.fill_message_details(q)
            self.fill_credentials(q)
            base_url = self.get_base_url()
            url = base_url + urllib.urlencode(q)
            req = urllib2.Request(url)
            if self.status == 'new':
                self.created_on = datetime.now()
            self.attempts += 1
	    self.status = 'sending'
            self.save()
            response = urllib2.urlopen(req).read()
            self.on_sent(response)
            log.info(response)
        except Exception, e:
            log.exception('error sending message %s to %s' % (self.sms_text, self.sent_to))
            self.status = 'in_queue'
            self.save()

    def get_billed_sms_count(self):
        length = len(self.sms_text)
        if length <= 160:
            return 1
        # index takes extra 6 characters per message
        chars_per_msg = 160 - 6
        no_of_messages = length/chars_per_msg
        if length % chars_per_msg > 0:
            return no_of_messages + 1
        else:
            return no_of_messages

class Chat(models.Model):
    transcript = models.TextField()

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)
