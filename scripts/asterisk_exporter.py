#! /usr/bin/env python
import os, sys
# change sys.path so that we can use django's orm
sys.path.insert(0, os.path.realpath((os.path.dirname(__file__) or '.')+'/../..'))
sys.path.insert(0, os.path.realpath((os.path.dirname(__file__) or '.')+'/..'))

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

import json
from asterisklog.models import AsteriskLog
from asterisklog import utils as ast_utils


def main(prune=False):
    for ast_log in AsteriskLog.objects.uncommitted_logs():
        event = json.loads(ast_log.jsondata)
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
    if prune:
        AsteriskLog.objects.prune_old_logs()


if __name__ == '__main__':
    if '--prune' in sys.argv[1:]:
        main(prune=True)
    else:
        main()

