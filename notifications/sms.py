from notifications.notificationmedium import NotificationMedium
import urllib
import urllib2
import logging
from communications.models import SMS as SMSEntry
log = logging.getLogger('request')

class SMS(NotificationMedium):
    mask = None
    to = None
    text = None
    sms = None

    def toString(self):
        if self.sms:
            return self.sms.unicode()
        return "Mask: %s\nTo: %s\nText: %s\n" % (self.mask, self.to, self.text)

    def run(self):
        number = self.to.split(',')[0]
        message = self.text
        sms_entry = SMSEntry(sent_to=number, sms_text=self.text)
        sms_entry.mask = self.mask or 'FutrBazr'
        sms_entry.save()
        self.sms = sms_entry
        self.sms.send()

    def send(self):
        self.run()
        return True

