from notifications.sms import SMS 
class Notification:
    def getNotifications(self):abstract
    def send(self):
        for n in self.getNotifications():
            try:
                n.send()
            except:
                pass
        return True
    def sendSMS(self):
        for n in self.getNotifications():
            if isinstance(n,SMS):
                try:
                    n.send()
                except:
                    pass
        return True
