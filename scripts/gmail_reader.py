import getpass, imaplib
import email

class EmailResponse(models.Model):
    body = models.TextField(blank=True, null=True)
    subject = models.TextField(blank=True, null=True)
    sent_from = models.CharField(max_length=100, blank=True, null=True)
    sent_to = models.CharField(max_length=100, blank=True, null=True)
    unique_id = models.CharField(max_length=200, unique=True)

    state = models.CharField(max_length=20, db_index=True, choices=(
        ('new','New'),
        ('posted', 'Posted')), default='new')
     

def save_email(subject, body, sent_to, sent_from, message_id, sent_at):


def fetch_messages():
    m = None
    try:
        m = imaplib.IMAP4_SSL("imap.gmail.com", "993")

        m.login('readerbot@chaupaati.com', '36T1471947')
        m.select()

        type, msg_ids = m.search(None, 'ALL')

        if type == 'OK':
            for num in msg_ids[0].split():
                type, data = m.fetch(num, '(RFC822)')
                if type == 'OK':
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_string(response_part[1])
                            subject = msg['subject']
                            sent_to = msg['to']
                            sent_from = msg['from']
                            message_id = msg['Message-ID']
                            body = ''
                            if msg.is_multipart():
                                body = msg.get_payload()
                            else:
                                body = msg.get_payload()[0].get_payload()

                            save_email()

                            type, del_resp = m.store(num, '+FLAGS', r'\Deleted')
                            if type == 'OK':
                                type, expunge = m.expunge()
    except Exception, e:
        log.exception('Error fetching email %s' % repr(e))
    finally:
        if m:
            m.close()
            m.logout()
