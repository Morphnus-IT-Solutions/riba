from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.
class SMS(models.Model):
    message = models.TextField()
    mobile = models.CharField(max_length=10)
    mask = models.CharField(max_length=10, default='9222221947', choices=(
        ('9222221947','9222221947'),
        ('Chaupati','Chaupati'),
        ('Potluck','Potluck')))

    # which gateway have we used to send this message
    gateway = models.CharField(max_length=50, choices=(
        ('Netcore API','Netcore API'),
        ('SMS Gupshup API', 'SMS Gupshup API')))

    notification = models.ForeignKey('notifications.Notification', null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)

    # timestamps
    queued_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True)
    delivered_at = models.DateTimeField(blank=True)

    # counters
    attempts = models.IntegerField(default=0)

    # status
    status = models.CharField(max_length=50, choices=(
        ('New','New'),
        ('Queued','Queued'),
        ('Sent','Sent'),
        ('Rejected','Rejected'),
        ('Delivered','Delivered'),
        ('Delivery Failed','Delivery Failed'),
        ('Delivery Uknown','Delivery Unknown')))

    def __unicode__(self):
        return 'SMS to %s' % self.mobile

    def fill_message_details(self, params):
        if self.gateway == 'Netcore API':
            params['text'] = self.message
            params['to'] =  '91%s' % self.mobile
            params['senderid'] = self.mask
        if self.gateway == 'SMS Gupshup API':
            pass

    def fill_credentials(self, params):
        if self.gateway == 'Netcore API':
            params['feedid'] = '263153'
            params['username'] = '9819766601'
            params['password'] = 'ammgw'
        if self.gateway == 'SMS Gupshup API':
            pass

    def on_sent(self):
        if self.gateway == 'Netcore API':
            return ''
        if self.gateway == 'SMS Gupshup API':
            return ''

    def get_base_url(self, response):
        if self.gateway == 'Netcore API':
            base_url = 'http://bulkpush.mytoday.com/BulkSms/SingleMsgApi?'
        if self.gateway == 'SMS Gupshup API':
            pass
        return base_url

    def send(self):
        if not self.status in ['New','Queued']:
            return
        try:
            if len(self.mobile) != 10:
                return
            if self.mobile[0] not in ['9','8','7']:
                return
            if not self.message:
                return
            q = {}
            self.fill_message_details(q)
            self.fill_credentials(q)
            base_url = self.get_base_url()
            url = base_url + urllib.urlencode(q)
            req = urllib2.Request(url)
            if self.status == 'New':
                self.queued_at = datetime.now()
            self.attempts += 1
            self.save()
            response = urllib2.urlopen(req).read()
            self.on_sent(response)
        except Exception, e:
            log.exception('error sending message %s to %s' % (self.message, self.mobile))
            self.status = 'Queued'
            self.save()

    def get_billed_sms_count(self):
        length = len(self.message)
        if length <= 160:
            return 1
        # index takes extra 6 characters per message
        chars_per_msg = 160 - 6
        no_of_messages = length/chars_per_msg
        if length % chars_per_msg > 0:
            return no_of_messages + 1
        else:
            return no_of_messages
