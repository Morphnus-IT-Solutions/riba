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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils
from accounts.models import *
import socket
socket.setdefaulttimeout(10*60)

if __name__ == '__main__':
    for i in range(1, 100):
        class Request:
            pass

        req = Request()
        req.client = ClientDomain.objects.get(domain='www.futurebazaar.com')
        
        cookie_file = fbapiutils.init(req)
        # cookie_file = '/tmp/tmpD3VfgE'
        u = users.get_user_by_mobile('hemanth@chaupaati.com', 'hemant.fb', cookie_file,req)
        profile = u['items'][0]['profileId']
