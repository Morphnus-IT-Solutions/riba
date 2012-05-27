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

from twisted.application import service, internet
from twisted.internet import reactor, defer
#from listener_conf import *
from django.conf import settings
from users.models import *
from starpy import manager
from eventHandlers import onCdr,onAgentLogin,onAgentLogout
import logging

def connect():
    def onConnect(ami):
        global ami_instance
        ami_instance = ami
        ami.registerEvent('Cdr', onCdr)
        ami.registerEvent('Agentlogin', onAgentLogin)
        ami.registerEvent('Agentcallbacklogin', onAgentLogin)
        ami.registerEvent('Agentlogoff', onAgentLogout)
        ami.registerEvent('Agentcallbacklogoff', onAgentLogout)
    f = manager.AMIFactory(settings.AMI_USR, settings.AMI_SECRET)
    df = f.login(settings.ASTERISK_IP, settings.AMI_PORT, 30.0)
    df.addCallback(onConnect)

if __name__ == '__main__':
 #   logging.config.fileConfig('logging.listener.conf')
    reactor.callWhenRunning( connect )
    reactor.run()

