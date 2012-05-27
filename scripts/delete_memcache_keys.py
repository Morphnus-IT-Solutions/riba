import os
import sys
import tempfile

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import memcache

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] == ('-h' or '--help'):
        sys.stderr.write('Usage: %s <file-with-memcache-keys>\n' % sys.argv[0])
        sys.stderr.write('Please provide list of keys with one key per line\n')
        sys.exit(1)
    else:
        fsock = open(sys.argv[1], 'r')
        keys = [line.strip() for line in fsock.readlines()]
        keys = [rid for rid in keys if rid]
        fsock.close()
    mc = memcache.Client(['127.0.0.1:11211'], debug=0)
    err = []
    for key in keys:
        r = mc.delete(key)
        if not r:
            err.append(key)
    print "Key deletion result:"
    for key in keys:
        if key in err:
            print "%s: failed" % key
        else:
            print "%s: successful" % key
    sys.exit(0)
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 autoindent smartindent
