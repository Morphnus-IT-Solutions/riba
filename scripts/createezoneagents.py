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

from utils import utils

def add_agents():
    from users.models import Profile
    from django.contrib.auth.models import User

    f = open('ezone_store_agents.txt')
    lines = f.readlines()
    for line in lines:
        print line
        line = line.strip()
        print line.split(',')
        name, email, password = line.split(',')
        namels = name.strip().split()
        if len(namels) > 1:
            first_name = namels[0]
            last_name = namels[1]
        email = email.strip()
        password = password.strip()
        user,profile = utils.get_or_create_user(email,email,password,first_name,last_name)
        profile.is_agent = True
        profile.save()

if __name__ == '__main__':
    add_agents()
