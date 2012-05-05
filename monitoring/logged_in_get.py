#!/usr/bin/python

# Based on:
#  http://stackoverflow.com/questions/2236498/tell-urllib2-to-use-custom-dns
#  http://personalpages.tds.net/~kent37/kk/00010.html

import httplib
import socket
import sys
import urllib
import urllib2

if len(sys.argv) < 2:
    print "Usage: %s <url> [ip override]" % sys.argv[0]
    print "  Logs in to the server and requests the provided URL. If provided,"
    print "  this uses the supplied IP rather than what would be returned by"
    print "  a standard DNS request."
    print
    print "  Example: %s http://nu.futurebazaar.com/ 10.0.5.33" % sys.argv[0]
    print "    The above would request the home page of nu.futurebazaar.com"
    print "    from 10.0.5.33."
    print
    sys.exit(1)

url = sys.argv[1]
protocol, remainder = urllib2.splittype(url)
host, path = urllib2.splithost(remainder)
if len(sys.argv) > 2:
    ip = sys.argv[2]
else:
    ip = host

def MyResolver(host):
    return ip

class MyHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        self.sock = socket.create_connection((MyResolver(self.host), self.port),
                                             self.timeout)

class MyHTTPSConnection(httplib.HTTPSConnection):
    def connect(self):
        sock = socket.create_connection((MyResolver(self.host), self.port),
                                        self.timeout)
        self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file)

class MyHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
        return self.do_open(MyHTTPConnection, req)

class MyHTTPSHandler(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(MyHTTPSConnection, req)

opener = urllib2.build_opener(MyHTTPHandler, MyHTTPSHandler,
                              urllib2.HTTPCookieProcessor())
urllib2.install_opener(opener)

params = urllib.urlencode(dict(username='testing@futurebazaar.com',
                               password='acal&aC22',
                               next=path))
handle = opener.open('%s://%s/auth/signin/' % (protocol, host), params)
print handle.read()
handle.close()
