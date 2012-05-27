from starpy import manager
from datetime import datetime
from communications.models import *
from ccm.models import *
import logging

log = logging.getLogger('request')

def onAgentLogin(ami, event):
    try:
        print event
        extension = event['agent']
        agent = Extension.objects.get(number=extension)
        login_record = AgentLoginLogout(agent_id=agent.allotted_to, time=datetime.now(), action='Login')
        login_record.save()
    except Exception, e:
        log.exception('onAgentLogin: %s, event: %s' % (event,repr(e)))
        print repr(e)


def onAgentLogout(ami, event):
    try:
        print event
        extension = event['agent']
        agent = Extension.objects.get(number=extension)
        logout_record = AgentLoginLogout(agent_id=agent.allotted_to, time=datetime.now(), action='Logout')
        logout_record.save()
    except Exception, e:
        log.exception('onAgentLogout: %s, event: %s' % (event,repr(e)))
        print repr(e)


def time_diff(start,end):
    diff = end - start
    seconds_elapsed = diff.seconds
    return seconds_elapsed


def onCdr(ami, event):
    print event
    try:
        call = Call()
        call.unique_id = event['uniqueid']
        start_time = event['starttime']
        answer_time = event['answertime']
        end_time=event['endtime']
        call.call_duration=int(event['duration'])
        call.wait_duration=int(event['duration']) - int(event['billableseconds'])
        if start_time:
            start_time=datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')
            call.called_on=start_time
        if answer_time:
            answer_time=datetime.strptime(answer_time,'%Y-%m-%d %H:%M:%S')
            call.answered_on=answer_time
        if end_time:
            end_time=datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S')
            call.ended_on=end_time

        call.status = "answered"
        if event['disposition'] == "NO ANSWER" or event['disposition'] == "FAILED" or event['disposition'] == "BUSY":
            call.status = "abandoned"

        if event['destinationcontext'] == "from_zaptel":
            call.type = "inbound"
            call.caller_id = event['source']
            call.did_number = event['destination']

            if event['destinationchannel'].find('Agent/') != -1:
                call.answered_exten=event['destinationchannel'].strip('Agent/')
                agent = None
                try:
                    agent = Extension.objects.get(number = event['destinationchannel'].strip('Agent/'))
                except Extension.DoesNotExist:
                    pass
                if agent:
                    call.answered_by = agent.allotted_to
                call.save()

        if event['destinationcontext'] == "phones":
            if event['destinationchannel'].startswith('SIP') and event['channel'].startswith('SIP'):
                # calls between agents, ignore these
                return
            if event['channel'].startswith('Agent/') and not event['destinationchannel']:
                if len(event['destination']) == 5:
                    if event['destination'].startswith('52') or event['destination'].startswith('42'):
                        # agent login or log off. ignore these
                        return
            if event['channel'].startswith('SIP') and not event['destinationchannel']:
                if len(event['destination']) == 5:
                    if event['destination'].startswith('42') or event['destination'].startswith('52'):
                        return

            if event['channel'].startswith('SIP') and event['destinationchannel'].startswith('IAX2'):
                call.type = 'outbound_manual'
                call.caller_id = event['destination']
                if event['source'].startswith('2'):
                    call.did_number = '67399600'
                if event['source'].startswith('3'):
                    call.did_number = '61911947'
                if event['source'].startswith('4'):
                    call.did_number = '61911500'
                call.answered_exten = event['source']
                ext = Extension.objects.get(number=call.answered_exten)
                call.answered_by = ext.allotted_to
                call.save()
                return

        if event['destinationcontext'].startswith("dialer"):
            call.type = 'outbound_dialer'
            call.caller_id = event['callerid']
            if event['channel'].startswith('SIP/'):
                extension = event['channel'].replace('SIP/','').split('-')[0]
                call.answered_exten = extension

                if extension.startswith('2'): call.did_number = '67399600'
                if extension.startswith('3'): call.did_number = '61911947'
                if extension.startswith('4'): call.did_number = '61911500'

                ext = Extension.objects.get(number=call.answered_exten)
                call.answered_by = ext.allotted_to
            call.save()
            return

    except Exception, e:
        log.exception('onCdr: %s, event: %s' % (event,repr(e)))
        print repr(e)

