from notifications.notificationmedium import NotificationMedium
from django.core.mail import send_mail,EmailMessage,EmailMultiAlternatives
import logging
from django.utils.html import strip_tags
from communications.models import Email as LEmail


log = logging.getLogger('request')

class Email(NotificationMedium):
    _from = "Chaupaati Bazaar<lead@chaupaati.com>"
    to = ""
    cc = ""
    bcc = ""
    subject = ""
    attachment = ""
    body = ""
    embedUrl = ""
    email_log_id = ""
    useApache = False
    isAttachment = False
    isGif = False
    imagePrefix = "/home/chaupaati/tinla/media/"
    isHtml = False

    def toString(self):
        return "To: %s\nCC: %s\nBCC: %s\nFrom: %s\nSubject: %s\nBody: %s\n" % (self.to,self.cc,self.bcc,self._from,self.subject,self.body)

    def send(self):
        self.run()
        return True
        
    def run(self):
        try:
            log.info(self.toString())
            msg = EmailMessage(self.subject.strip(), self.body.strip(), self._from, self.to.split(','),self.bcc.split(','), None)
            if self.isAttachment:
                img_data = open(self.attachment,'rb').read()
                msg.attach('product.jpg',img_data,'image/jpg')
            if self.isHtml:
                text_content = strip_tags(self.body.strip())
                msg = EmailMultiAlternatives(self.subject.strip(), text_content, self._from,self.to.split(','), self.bcc.split(','))
                msg.bcc = self.bcc.split(',')
                msg.attach_alternative(self.body.strip(), "text/html")
            msg.send()
            if self.email_log_id:
                try:
                    email_log = LEmail.objects.get(id = self.email_log_id)
                    email_log.status = 'delivered'
                    email_log.save()
                except:
                    log.warn(
                        'Skipping saving email log to %s' % self.email_log_id)
        except Exception, e:
            if self.email_log_id:
                try:
                    email_log = LEmail.objects.get(id = self.email_log_id)
                    email_log.status = 'delivery_failed'
                    email_log.save()
                except:
                    log.warn(
                        'Skipping saving email log to %s' % self.email_log_id)
            log.exception('Error sending email %s' % self.toString())
