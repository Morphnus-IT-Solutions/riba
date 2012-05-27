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

from locations.models import State

STATES_MAP = {'Andaman and Nicobar':'26',
            'Andhra Pradesh':'01',
            'Arunachal Pradesh':'02',
            'Assam':'03',
            'Bihar':'04',
            'Chandigarh':'27',
            'Chattisgarh':'33',
            'Dadra and Nagar Haveli':'28',
            'Daman and Diu':'29',
            'Delhi':'30',
            'Goa':'05',
            'Gujarat':'06',
            'Haryana':'07',
            'Himachal Pradesh':'08',
            'Jammu and Kashmir':'09',
            'Jharkhand':'34',
            'Karnataka':'10',
            'Kerala':'11',
            'Lakshadweep':'31',
            'Madhya Pradesh':'12',
            'Maharastra':'13',
            'Maharashtra':'13',
            'Manipur':'14',
            'Meghalaya':'15',
            'Mizoram':'16',
            'Nagaland':'17',
            'New Delhi':'30',
            'Orissa':'18',
            'Pondicherry':'32',
            'Punjab':'19',
            'Rajasthan':'20',
            'Sikkim':'21',
            'Tamil Nadu':'22',
            'Tamilnadu':'22',
            'Tripura':'23',
            'Uttar Pradesh':'24',
            'Uttaranchal':'35',
            'West Bengal':'25'}

if __name__ == '__main__':
    for key,value in STATES_MAP.iteritems():
        for state in State.objects.filter(name=key):
            state.sap_code = value
            state.save()

