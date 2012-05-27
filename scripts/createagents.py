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

def add_agents():
    from users.models import Profile
    from django.contrib.auth.models import User

    f = open('chaupaati')
    lines = f.readlines()
    for line in lines:
        print line
        line = line.strip()
        print line.split(',')
        password, name, loginid = line.split(',')
        name = name.strip()
        first_name = name.split(' ')[0]
        loginid = loginid.strip()
        password = password.strip()
        u = User.objects.create_user(loginid, 'agent@example.com', password)
        u.name = name
        u.save()

        agent = Profile()
        agent.user = u
        agent.full_name = '%s%s' % (name,password)
        agent.primary_phone = '%s%s' % (first_name,password)
        agent.is_agent = True
        agent.save()

if __name__ == '__main__':
    add_agents()
