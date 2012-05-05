from telnetlib import Telnet
import threading
import time
import logging

class AMIReader(threading.Thread):
    def __init__(self, conn, callback):
        self.conn = conn
        self.callback = callback
        self.stop_reader = False
        self.data = ''
        super(AMIReader, self).__init__()

    def stop(self):
        self.stop_reader = True

    def run(self):
        try:
            while True:
                self.data += self.conn.read_eager()
                end_of_packet = False
                if self.data.find('\r\n\r\n') > 0:
                    end_of_packet = True
                if end_of_packet:
                    # we have one or more packets to send. lets find out
                    packets = self.data.split('\r\n\r\n')
                    # check if last packet is complete
                    if packets[-1].endswith('\r\n\r\n'):
                        # clean slate. inform and forget everything
                        self.callback(packets)
                    else:
                        # we should remember the last (incomplete packet)
                        self.callback(packets[:-1])
                        self.data = packets[-1]
                if self.stop_reader == True:
                    break
                else:
                    time.sleep(0.01)
        except:
            self.stop_reader = True
            pass

class AMI:
    class __impl:
        def __init__(self, host, port, username, secret):
            self.host = host
            self.port = port
            self.username = username
            self.secret = secret
            self.conn = Telnet(self.host, self.port)
            self.action_id = 0
            self.action_map = {}
            self.event_listeners = {}
            self.write_lock = threading.RLock()
            self.reader = AMIReader(self.conn, self.on_packets_read)

        def add_listener(self, event, callback):
            if event not in self.event_listeners:
                self.event_listeners[event] = [callback]
            else:
                self.event_listeners.get(event).append(callback)

        def on_packets_read(self, packets):
            for packet in packets:
                resp = {'_raw':[]}
                for line in packet.split('\n'):
                    logging.getLogger('events').info(line)
                    line = line.strip()
                    resp['_raw'].append(line)
                    first_colon = line.find(':')
                    if not first_colon > 0:
                        continue
                    key = line[:first_colon].strip()
                    value = line[first_colon+1:].strip()
                    resp[key] = value
                if 'ActionID' in resp and resp['ActionID'] in self.action_map:
                    try:
                        self.action_map[resp['ActionID']]['handler'](resp, self)
                    except:
                        pass
                else:
                    if 'Event' in resp and resp['Event'] in self.event_listeners:
                            for listener in self.event_listeners[resp['Event']]:
                                try:
                                    listener(resp, self)
                                except:
                                    pass

        def start(self):
            self.reader.start()
            self.login()

        def stop(self):
            self.reader.stop()
            self.reader.join()
            self.close()

        def close(self):
            self.conn.close()

        def get_next_action_id(self):
            self.write_lock.acquire()
            action_id = 0
            try:
                self.action_id += 1
                action_id = self.action_id
            finally:
                self.write_lock.release()
            return action_id


        def send_action(self, action, params, handler):
            line = 'Action: %s\r\n' % action
            self.conn.write(line)
            logging.getLogger('events').info(line)
            for key, value in params.items():
                line = '%s: %s\r\n' % (key, value)
                self.conn.write(line)
                logging.getLogger('events').info(line)
            action_id = str(self.get_next_action_id())
            self.action_map[str(action_id)] = dict(action=action, params=params, handler=handler)
            line = 'ActionID: %s' % action_id
            logging.getLogger('events').info(line)
            self.conn.write(line)
            line = '\r\n\r\n'
            self.conn.write(line)
            logging.getLogger('events').info(line)
            return action_id

        def clear_callback(self, action_id):
            if action_id in self.action_map:
                self.action_map.pop(action_id)

        def login(self):
            def parse_response(resp, ami):
                # clear call back
                ami.clear_callback(resp['ActionID'])

            action_id = self.send_action('login', 
                dict(Username=self.username, Secret=self.secret,Events='On'),
                parse_response
                )

        def queue_status(self, callback):
            queues = {}
            def parse_response(resp,ami):
                event = resp.get('Event','')
                queue_name = resp.get('Queue','')
                action_id = resp.get('ActionID','')
                # pop out global stuff
                pop_out = ['Event','Queue','ActionID']
                for x in pop_out:
                    if x in resp:
                        resp.pop(x)
                
                if event == 'QueueParams':
                    # info about queue
                    queue_info = {}
                    queue_info.update(resp)
                    queues[queue_name] = dict(info=queue_info,members=[],calls_waiting=[])
                if event == 'QueueMember':
                    queue_member = {}
                    queue_member.update(resp)
                    queues[queue_name]['members'].append(queue_member)
                if event == 'QueueEntry':
                    call = {}
                    call.update(resp)
                    queues[queue_name]['calls_waiting'].append(call)
                if event == 'QueueStatusComplete':
                    ami.clear_callback(action_id)
                    callback(queues)
            action_id = self.send_action('QueueStatus',{},parse_response)

    __instance = None

    def __init__(self, host, port, user, secret):
        if not AMI.__instance:
            AMI.__instance = AMI.__impl(host, port, user, secret)
        self.__dict__['_Singleton__instance'] = AMI.__instance

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

if __name__ == '__main__':
    stop = False
    ami = AMI('192.168.0.143',5038,'watchmen','sauron')
    ami.start()
    try:
        while True:
            if stop:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        ami.stop()
