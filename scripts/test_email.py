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

from django.core.mail import EmailMessage

def send_email():
    body = 'Testing email ....'
    msg = EmailMessage('Scratch card count', body,
        "Future Bazaar Reports<lead@futurebazaar.com>",
        ['hemanth@chaupaati.com', 'hemanth.goteti@gmail.com'])
    msg.send()


if __name__ == '__main__':
    send_email()
