import os, sys
from fabric.api import (abort, env, get, hosts, output, put, reboot, roles,
    runs_once, show, warn, cd, fastprint, hide, local, prompt, puts,
    require, run, settings, sudo)
from fabric.contrib import files, console
from fabric import utils
from fabric.decorators import hosts
from fabric.colors import blue, cyan, green, magenta, red, white, yellow

major, minor, micro, releaselevel, serial = sys.version_info
if (major, minor) <= (2, 5):
    sys.stderr.write("Please upgrade your python version to at least 2.6")
    sys.exit(2)

staging_hosts = ['10.0.102.12',]
production_hosts = [
        '10.0.101.13',
        '10.0.101.14',
        '10.0.101.15',
        '10.0.101.37',
        '10.0.101.38',
        '10.0.101.51',
        ]

def _setup_path():
    env.home = '/home/apps/'
    env.project = 'tinla'
    env.code_root = os.path.join(env.home, env.project)

def staging():
    """ use staging environment on remote host"""
    env.user = 'apps'
    env.hosts = staging_hosts
    _setup_path()

def production():
    """ use staging environment on remote host"""
    env.user = 'apps'
    env.hosts = production_hosts
    _setup_path()

def check_requirements():
    """check minimum requirement need for application"""
    #TODO: currently doing nothing useful
    require('code_root', provided_by=('staging', 'production'))
    with settings(hide('running', 'stdout', 'stderr'),):
        r = run('uname -a')
        r1 = run('python --version')
    print(r, r1)

def apache_reload():
    sudo('service apache2 graceful')

def git_pull(branch)
    """pulls changes from git"""
    if not branch:
        sys.stderr.write("please provide a branch")
        sys.exit(1)
    with cd(env.code_root):
        sudo("git pull origin %s" % branch)

def upgrade():
    """upgrade server version"""
    #TODO: restrict it to use tags only on production
    require('code_root', provided_by=('staging', 'production'))
    with cd(env.code_root):
        if env.host_string in staging_hosts:
            sudo("git pull origin %s" % 'staging')
        elif env.host_string in staging_hosts:
            sudo("git pull origin %s" % 'master')
        sudo("python manage.py migrate --all")
        # can be used when inside a virtualenv
        #sudo("pip -E virt-python install -r requirements.txt")
        # can be used for reloading new version, no need to restart apache2
        #sudo("touch apache/django.wsgi")
        apache_reload()
