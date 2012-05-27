import sys, os
from twisted.application import service, internet
from twisted.internet import reactor, defer
import twisted
from settings import *

# need to setup environment variable DJANGO_SETTINGS_MODULE to use django
os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE
from asterisk.models import Task, Call
from rms.models import Campaign, Response
from ccm.models import Agent, AgentLoginLogout, Extension
from rms.views import get_or_create_response, move_response

from asterisk.amiClient import AMIFactory
import logging.config
import threading
from datetime import datetime, timedelta
from time import sleep
import random
import logging
logging.config.fileConfig('/home/hemanth/tinla/logging.conf')

log = logging.getLogger('ccc')
contexts = ['from_zaptel','fb-eng','fb-hin','ez-eng','ez-hin','fb_test','TR400','TR301','TR302','TR303','TR304']

def get_data_from_url(url):
    """Return cli, dni, call_id values from launch url
    """
    try:
        data = url.split('/')[3].split('-')
        outgoing = False
        response_id = None
        if data[2] == '2':
            outgoing = True
            response_id = int(data[4])
        return data[0], data[1], outgoing, data[3], response_id
    except:
        return None, None, None, None, None

def onPeerStatus(ami, event):
    exten = int(event['peer'].replace('SIP/',''))
    try:
        extension = Extension.objects.get(number=exten)
    except:
        return
    if event['peerstatus'] == 'Registered':
        action = 'Login'
    elif event['peerstatus'] == 'Unregistered':
        action = 'Logout'
    else:
        return
    login_logout = AgentLoginLogout(agent=extension.allotted_to, time=datetime.now(), action=action, destination='asterisk')
    login_logout.save()

def onNewexten(ami, event):
    global queue_login_requests
    if (event['context'] in contexts) and (event['application'] == 'Set') and (event['appdata'].startswith('LAUNCH_URL=')):
        try:
            phone, dni, outgoing, call_id, response_id = get_data_from_url(event['appdata'].replace('LAUNCH_URL=',''))
            response = get_or_create_response(dni=dni, phone_number=phone)
            if response:
                log.info('onNewexten: Incoming call connected for response %s' % response.id)
            else:
                log.info('onNewexten: Error creating response - phone: %s, dni: %s' % (phone,dni))
        except Exception, e:
            log.info('Exception in onNewexten (%s): %s' % (event['context'], e))
        return
    if event['context'] == 'phones' and (event['application'] == 'Set') and (event['appdata'].startswith('LAUNCH_URL=')):
        try:
            phone, dni, outgoing, call_id, response_id = get_data_from_url(event['appdata'].replace('LAUNCH_URL=',''))
            response = Response.objects.get(pk=response_id)
            exten = event['channel'].split('/')[1].split('-')[0]
            extension = Extension.objects.select_related('allotted_to').get(number=exten) 
            agent = extension.allotted_to
            if not agent:
                log.info('onNewexten: Agent not found with extension - %s' % exten)
                return
            move_response(response=response, state=response.funnel_state, substate=response.funnel_sub_state, agent=agent, callid=call_id)
            log.info('onNewexten: Outgoing call connected for response %s' % response_id)
        except Exception, e:
            log.info('onNewexten: Error in processing outgoing call - %s' % e)
        return
    if event['context'] == 'phones' and event['extension'] == '42000' and event['application'] == 'AgentLogin':
        try:
            agent_id = event['appdata'].split('||')[0]
            if agent_id not in queue_login_requests:
                queue_login_requests.append(agent_id)
        except Exception, e:
            log.info('Exception in onNewexten(phones): %s'%e)
        return
    log.info(event)

def onQueueMemberStatus(ami,event):
    global queue_login_requests
    exten = event['membername'].replace('Agent/','')
    action = None
    if event['status'] == '5':
        action = 'Logout'    
    elif event['status'] == '1' and (exten in queue_login_requests):
        action = 'Login'
        queue_login_requests.remove(exten)
    if action:
        try:
            extension = Extension.objects.get(number=exten)
        except:
            return
        login_logout = AgentLoginLogout(agent=extension.allotted_to, time=datetime.now(), action=action, destination='queue')
        login_logout.save()

def onAgentCalled(ami, event):
    def update_res(variable):
        phone, dni, outgoing, call_id, response_id = get_data_from_url(variable)
        response = get_or_create_response(dni=dni, phone_number=phone)
        if response:
            new_state = response.funnel_state
            new_substate = response.funnel_sub_state
            if response.funnel_sub_state.name == 'Abandoned':
                new_state = response.campaign.funnel.funnel_states.get(name='Answered')
                new_substate = response.campaign.campaign_sub_states.get(name='Untagged', funnel_state=new_state)
            move_response(response=response, state=new_state, substate=new_substate, agent=agent, callid=call_id)
            log.info('onAgentCalled: Agent %s assigned to response %s' % (agent,response))
        else:
            log.info('onAgentCalled: Error retrieving response - phone: %s, dni: %s' % (phone,dni))
    if event['context'] in contexts and event['agentcalled'].startswith('Agent/'):
        exten = event['agentcalled'].replace('Agent/','')
        log.info('onAgentCalled: %s, exten: %s' % (event['variable'],exten))
        agent = None
        try:
            extension = Extension.objects.get(number=exten) 
            agent = extension.allotted_to
            if agent:
                if event['variable'].startswith('LAUNCH_URL'):
                    phone, dni, outgoing, call_id, response_id = get_data_from_url(event['variable'].replace('LAUNCH_URL=',''))
                    response = get_or_create_response(dni=dni, phone_number=phone)
                    if response:
                        new_state = response.funnel_state
                        new_substate = response.funnel_sub_state
                        if response.funnel_sub_state.name == 'Abandoned':
                            new_state = response.campaign.funnel.funnel_states.get(name='Answered')
                            new_substate = response.campaign.campaign_sub_states.get(name='Untagged', funnel_state=new_state)
                        move_response(response=response, state=new_state, substate=new_substate, agent=agent, callid=call_id)
                        log.info('onAgentCalled: Agent %s assigned to response %s' % (agent,response))
                    else:
                        log.info('onAgentCalled: Error retrieving response - phone: %s, dni: %s' % (phone,dni))
                else:
                    df1 = ami.getVar(event['channelcalling'],'LAUNCH_URL')
                    df1.addCallback(update_res)
        except Exception, e:
            log.info('Exception in onAgentCalled: %s'%e)
    else:
        log.info('onAgentCalled: Error - agentcalled: %s'%event['agentcalled'])


def onCdr(ami, event):
    try:
        call = Call()
        for key in ['event','privilege']:
            event.pop(key)
        for field in ['starttime','answertime','endtime']:
            value = event.pop(field)
            if value:
                date = datetime.strptime(value,'%Y-%m-%d %H:%M:%S')
                setattr(call, field, date)
        for field in ['duration', 'billableseconds']:
            value = event.pop(field)
            if value:
                seconds = int(value)
                setattr(call, field, seconds)
        for field in event.keys():
            setattr(call, field, event[field])
        
        call.status = "answered"
        if call.disposition == "NO ANSWER" or call.disposition == "FAILED":
            call.status = "abandoned"
        if not call.destinationchannel:
            call.status = "abandoned"

        call.dir = "out"
        call.is_dialer_call = False
        
        if call.destinationcontext in contexts:
            call.dir = "in"
            call.cli = call.source
            cli, dni, outgoing, call_id, response_id = get_data_from_url(call.lastdata.split('|')[2])
            call.dni = dni
            
            agent = None
            if call.destinationchannel.find('Agent/') != -1:
                exten = call.destinationchannel.replace('Agent/','')
                try:
                    extension = Extension.objects.get(number=exten)
                    agent = extension.allotted_to
                    if agent:
                        call.agent = agent
                except Exception, e:
                    log.info('onCdr: Error assigning agent to call (%s) - %s' % (call.destinationcontext, e))
            else:
                log.info('onCdr: Unknown destination channel (%s) - %s, callid - %s' % (call.destinationcontext, call.destinationchannel, call.uniqueid))
        
            response = get_or_create_response(dni=call.dni, phone_number=call.cli)
            if response:
                call.response = response
                call.campaign = response.campaign
                call.interaction = response.last_interaction
            else:
                log.info('onCdr: Could not assign a response for this call - dni: %s, phone: %s' %(call.dni,call.cli))

        elif call.destinationcontext == "phones":
            if call.channel.find('SIP/') != -1:
                exten = call.channel.split('-')[0].replace('SIP/','')
                agent = None
                try:
                    extension = Extension.objects.get(number=exten) 
                    agent = extension.allotted_to
                    if agent:
                        call.agent = agent
                except Exception, e:
                    log.info('onCdr: Error assigning agent to call (phones) - %s'%e)
                    #log.exception('error assiging agent to call')
            else:
                log.info('onCdr: Unknown call channel (phones) - %s, callid - %s' % (call.channel, call.uniqueid))
            
            if call.userfield:
                try:
                    response = Response.objects.get(pk=int(call.userfield))
                    call.response = response
                    call.campaign = response.campaign
                    call.cli = response.phone.phone
                    call.dni = response.campaign.dni_number
                    call.interaction = response.last_interaction
                except ValueError, ve:
                    call.cli = call.source
                except Exception, ex:
                    log.info('onCdr: Error retrieving response (phones), %s, response - %s, callid - %s' % (ex, call.userfield, call.uniqueid))
            else:
                log.info('onCdr: Response ID not found (phones) in call - %s' % call.uniqueid)
        
        #elif call.destinationcontext == "phones":
        #    if call.destinationchannel.startswith('Agent/'):
        #        #Transferred call - reset response call_in_progress
        #        log.info('onCdr: Transferred call - %s', call.lastdata)
        #        exten = call.destinationchannel.replace('Agent/','')
        #        agent = None
        #        try:
        #            extension = Extension.objects.get(number=exten)
        #            agent = extension.allotted_to
        #            cli, dni, call_id = get_data_from_url(call.lastdata.split('|')[2])
        #            response = get_or_create_response(dni=dni, phone_number=cli)
        #            if response:
        #                response.call_in_progress = True
        #            if agent:
        #                response.assigned_to = agent
        #            response.save()
        #            log.info('onCdr: Response %s reset for transferred call. cli - %s, dni - %s' % (response.id, cli, dni))
        #        except Exception, e:
        #            log.info('onCdr: Error assigning agent to response (phones) - %s, extension - %s' % (e,exten))
        #    #Do not save this call record since it is a transfer
        #    else:
        #        log.info('onCdr: Unknown destination channel (phones) %s'% call.destinationchannel)
        #    return

        else:
            log.info(event)
            log.info('onCdr: Unknown destination context - %s, callid - %s' % (call.destinationcontext, call.uniqueid))
	    
        call.save()
    
    except Exception, e:
        log.info('onCdr: Error saving call record, %s' % e)
        #log.exception('error saving call record %s' % repr(e))

def ping():
    global ami_instance
    ami =  ami_instance
    if not ami:
        #log.error('no ami instance to originate calls')
        return
    ami.ping()
    reactor.callLater(3, ping)

def call_response_agent_first(agent, response, task):
    global ami_instance
    ami = ami_instance
    if not ami:
        #log.error('no ami instance to originate calls')
        return
    
    response.call_in_progress = True
    response.save()
    
    def onComplete(result):
        def onExtensionStatus(result):
            if(result['status'] == '8'):
                task.status = 'Completed'
                task.save()
            elif(result['status'] == '-1'):
                task.status ='InvalidExtension'
                task.save()
            elif(result['status'] == '0'):
                task.status ='AgentIdle'
                task.save()
            elif(result['status'] == '1'):
                task.status ='InUse'
                task.save()
            elif(result['status'] == '16'):
                task.status ='OnHold'
                task.save()
            elif(result['status'] == '4'):
                task.status ='Unavailable'
                task.save()
            else:
                task.status ='Busy'
                task.save()
            return
        
        df_2=ami.extensionState(agent.extension.get().number,'phones')
        df_2.addCallbacks(onExtensionStatus,onError)

    def onError(reason):
        #log.error('error originating call %s' % repr(reason))
        task.state = 'Failed'
        task.save()
        response.call_in_progress = False
        response.save()
        return reason

    url = 'http://cb.phonepedeal.com/'
    if response.campaign.client.name == 'holii':
        url = 'http://p.holii.in/'
    elif response.campaign.client.name == 'Ezone':
        url = 'http://p.ezoneonline.in/'
    elif response.campaign.client.name == 'Future Bazaar':
        url = 'http://p.futurebazaar.com/'
    log.info('originate: %s, %s' %(agent.extension.get().number, response.phone.phone))
    df = ami.originate('SIP/%s' % agent.extension.get().number, async='true', timeout=60, context='phones',
            priority='1', exten= '0%s'%response.phone.phone, variable={'RID':response.id, 'PH':response.phone.phone,
            'URL':url, 'DNI':response.campaign.dni_number})
    df.addCallbacks(onComplete, onError)
    task.status = 'Attempted'
    task.save()

def work():
    global connection_status
    if connection_status != 'connected':
        # cant work. lets wait till connection gets established.
        return
    try:
        # Get open tasks
        tasks = Task.objects.select_related('response','response__campaign','response__phone',
            'agent__extension','response__campaign__client').filter(status='New')
        for task in tasks:
            if task.type == 'call_by_agent_to_response':
                call_response_agent_first(task.agent, task.response, task)
    except Exception, e:
        log.info('Error from work: %s' % e)
    # whatever happens, register for next call
    reactor.callLater(1, work)

def logoff():
    global ami_instance
    ami_instance.logoff()

def connect():
    log.info('connecting ...')

    def connectionLost(connector, reason):
        global connection_status
        connection_status = 'lost'
        log.info('connection lost - %s' % reason)
        #log.info('ami lost connection')
        reactor.callLater(30, connect)

    def onConnect(ami):
        try:
            global ami_instance
            global connection_status
            global queue_login_requests
            ami_instance = ami
            queue_login_requests = []
            ami.registerEvent('Cdr', onCdr)
            ami.registerEvent('PeerStatus', onPeerStatus)
            ami.registerEvent('AgentCalled', onAgentCalled)
            ami.registerEvent('Newexten', onNewexten)
            ami.registerEvent('QueueMemberStatus', onQueueMemberStatus)
            connection_status = 'connected'
            log.info('connected')
            reactor.callLater(1, work)
        except Exception, e:
            #log.exception('error ' + repr(e))
            pass

    def onError(error):
        #log.error('Got error %s' % repr(error))
        log.info('onError: connection lost - %s' % error)
        # reset globals
        global ami_instance
        global connection_status
        ami_instance = None
        connection_status = 'lost'
        reactor.callLater(30, connect)

    f = AMIFactory(AMI_USR, AMI_SECRET, 'on', connectionLost)
    df = f.login(ASTERISK_IP, AMI_PORT, 30.0)
    df.addCallback(onConnect)
    df.addErrback(onError)

if __name__ == '__main__':
    try:
        #logging.config.fileConfig('logging.dialer.conf')
        reactor.callWhenRunning( connect )
        reactor.run()
    except KeyboardInterrupt:
        log.info('Keyboard error')
        pass
