import sys, os
from twisted.application import service, internet
from twisted.internet import reactor, defer
from amiClient import AMIFactory
from datetime import datetime

AMI_USR = 'watchmen'
AMI_SECRET = 'sauron'
ASTERISK_IP = '10.114.61.2'
AMI_PORT = 5038

def logoff():
    global ami_instance
    ami_instance.logoff()

def launch_browser(url):
    command = '%s "%s"' % ("firefox",url)
    print url
    os.system(command)

def onAgentCalled(ami, event):
    def printvar(message):
        print "LAUNCH_URL", message
        launch_browser(message)
    global agent_id
    if event['agentcalled'] == 'Agent/%s'%agent_id:
        print datetime.now()
        print event
        print
        if event['variable'].startswith('LAUNCH_URL'):
            launch_browser(event['variable'].replace('LAUNCH_URL=',''))
        else:
            df1 = ami.getVar(event['channelcalling'],'LAUNCH_URL')
            df1.addCallback(printvar)

def onNewexten(ami, event):
    global agent_id
    if event['channel'].startswith('SIP/%s'%agent_id) and event['appdata'].startswith('LAUNCH_URL='):
        launch_browser(event['appdata'].replace('LAUNCH_URL=',''))

def connect():
    def onConnect(ami):
        global ami_instance
        ami_instance = ami
        ami.registerEvent('Newexten', onNewexten)
        ami.registerEvent('AgentCalled', onAgentCalled)
        print "connected.."

    f = AMIFactory(AMI_USR, AMI_SECRET, 'on')
    df = f.login(ASTERISK_IP, AMI_PORT, 30.0)
    df.addCallback(onConnect)

if __name__ == '__main__':
    try:
        global agent_id
        while True:
            print 'Enter your agent id: ',
            agent_id = sys.stdin.readline().strip()
            print 'Your Agent ID is: %s' % agent_id
            break
    except KeyboardInterrupt:
        pass
    else:
        reactor.callWhenRunning( connect )
        reactor.run()
