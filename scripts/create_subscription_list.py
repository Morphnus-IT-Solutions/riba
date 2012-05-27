import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from users.models import DailySubscription

if __name__ == '__main__':
    fp = '/tmp/subscription-list.txt' 
    sock = open(fp, 'w')
    i, es, em = 0,0,0
    for d in DailySubscription.objects.all():
        timestamp = d.timestamp
        source = d.source
	if not source:
	    source = ""
	try:
            sms_alert = d.sms_alert_on
            phone = sms_alert.phone
        except:
            phone = ""
            es = es+1
        try:
            email_alert = d.email_alert_on
            email = email_alert.email
        except:
            email = ""
            em = em+1
	if email or phone:
	    sock.write('"%s", "%s", "%s", "%s"\n' % (timestamp.strftime("%Y-%m-%d %H:%M:%S"), phone, email, source, ))
        print i, es, em
        i = i+1
    sock.close()
    print "files saved at:"
    print "\t%s" % fp 

