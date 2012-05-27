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

from promotions.models import ScratchCard

msgs = []
count = 0

code_file = open('scripts/scratch_codes.txt')
for code in code_file.readlines():
    code = code.strip()
    count += 1
    scratch_card = ScratchCard.objects.filter(scratch_card_no = code)
    if not scratch_card:
        scratch_card = ScratchCard()
        scratch_card.scratch_card_no = code
        scratch_card.status = 'active'
        scratch_card.store = 'scratch_and_win'
        scratch_card.save()
        print count,") ",code," Added"
    else:
        print count,") REPLICATED scratch_card::",code
