#! /usr/bin/env python

from twisted.application import service, internet
from twisted.internet import reactor
from starpy.manager import AMIFactory
import json
from datetime import datetime

import os, sys
# change sys.path so that we can use django's orm
sys.path.insert(0, os.path.realpath((os.path.dirname(__file__) or '.')+'/../..'))
sys.path.insert(0, os.path.realpath((os.path.dirname(__file__) or '.')+'/..'))
#sys.path.insert(0, (os.path.realpath('../') os.path.realpath('../..')))
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

from django.conf import settings
import logging
from asterisklog.models import AsteriskLog
from asterisklog import utils as ast_utils
logging.basicConfig()


def dump_to_database(ami, event):
    js = json.dumps(event)
    ast_log = AsteriskLog(jsondata=js, event=event.get('event', None))
    ast_log.save()
    timestamp = ast_log.timestamp
    if event['event'] == 'Cdr':
        if ast_utils.event_Cdr(event, timestamp):
            ast_log.commit
    elif event['event'] in ('Agentlogin','Agentcallbacklogin'):
        if ast_utils.event_onAgentLogin(event, timestamp):
            ast_log.commit
    elif event['event'] in ('Agentlogoff', 'Agentcallbacklogoff'):
        if ast_utils.event_onAgentLogout(event, timestamp):
            ast_log.commit
    print AsteriskLog.objects.count()

def connect():
    def onConnect(ami):
        global ami_instance
        ami_instance = ami
        ami.registerEvent('Cdr', dump_to_database)
        ami.registerEvent('Agentlogin', dump_to_database)
        ami.registerEvent('Agentcallbacklogin', dump_to_database)
        ami.registerEvent('Agentlogoff', dump_to_database)
        ami.registerEvent('Agentcallbacklogoff', dump_to_database)

    f = AMIFactory(settings.AMI_USER, settings.AMI_SECRET)
    df = f.login(settings.ASTERISK_IP, settings.AMI_PORT, 30.0)
    df.addCallback(onConnect)

if __name__ == '__main__':
    reactor.callWhenRunning(connect)
    reactor.run()

