import threading
from twisted.internet import reactor, defer
from asterisk.starpy import manager

class AMIManager(threading.Thread):
    def __init__(self, usr, secret, host, port, timeout=30.0):
        self.usr = usr
        self.secret = secret
        self.host = host
        self.port = port
        self.timeout = timeout
        self.ami = None
        self.error_reason = ''
        super(AMIManager, self).__init__()

    def onStart(self):
        def onConnect(ami):
            self.ami = ami
        def onError(reason):
            self.error_reason = reason
        f = manager.AMIFactory(self.usr, self.secret)
        df = f.login(self.host, self.port, self.timeout)
        df.addCallback(onConnect)

    def run(self):
        reactor.callWhenRunning(self.onStart)
        reactor.run(installSignalHandlers = 0)
