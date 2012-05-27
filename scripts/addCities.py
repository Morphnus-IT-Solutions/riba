import os, sys
import xlrd

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from locations.models import State,City


book = xlrd.open_workbook("cities.xls")
sh = book.sheet_by_index(0)
header = sh.row(0)
map = {}

idx = 0
stateMap = {1:35,2:1,3:2,4:4,5:31,6:29,7:6,9:8,10:11,11:10,12:20,13:25,14:30,15:15,16:14,17:32,18:17,19:13,20:23,21:18,22:24,23:19,24:21,25:26,26:27,27:33,28:7,29:22,30:3,31:16,32:28,33:9,34:4,35:15,36:33,37:5,38:12,39:34}
for x in header:
    val = x.value.strip().lower()
    map[val] = idx
    idx += 1
list = []
#allowedFeatureCodes = ['PPL','PPLF','PPLC','PPLL','PPLS']
allowedFeatureCodes = ['PPL','PPLA','PPLA2','PPLA3','PPLA4','PPLC','PPLF','PPLG','PPLL']
for i in range(1, sh.nrows):
    row = sh.row(i)
    name = row[map['asciiname']].value.strip()
    stateCode = row[map['admin1 code']].value
    featureCode = row[map['feature code']].value.strip()
    population = int(row[map['population']].value)
    if stateCode and featureCode in allowedFeatureCodes and population > 10000:
        actualCode = stateMap[int(stateCode)]
        key = name + ':' + str(actualCode)
        if key not in list:
            list.append(key)
            try:
                city = City()
                city.name = name
                city.state_id = actualCode
                city.type = 'primary'
                city.save()
            except:
                pass
